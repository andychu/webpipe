#!/usr/bin/python
"""
weboll.py

Server that receives content from a pipe, and serves it "interactively" to the
browser.  It relies on a "hanging GET" -- jQuery on the client and
threading.Event on the server.
"""

import datetime
import errno
import getpass
import optparse
import os
import Queue
import threading
import string  # for lower case letters
import sys

from common import httpd
from common import util
from common import spy

import file2html  # run in process
import wait_server

# outside
import tnet

log = util.log


class Error(Exception):
  pass


_verbose = False

def debug(msg, *args):
  if _verbose:
    common.log(msg, *args)


class ReadStdin(object):
  """Read file records from stdin and put them on a queue."""

  def __init__(self, q):
    """
    Args:
      q: Queue, can be None
    """
    self.q = q

  def __call__(self):
    while True:
      # must be unbuffered
      try:
        record = tnet.load(sys.stdin)
      except EOFError:
        break

      self.q.put(record)


class WriteFiles(object):
  """Write files to a single session dir."""

  # input message format:
  # later: should be BFO format
  # { dir: ... }
  # need filenames and contents

  def __init__(self, in_q, out_q, out_dir):
    self.in_q = in_q
    self.out_q = out_q
    self.out_dir = out_dir

  def __call__(self):
    i = 1
    while True:
      #log('disk thread waiting for %d', i)
      record = self.in_q.get()
      #log('got %r', record)

      files = record['files']

      for fi in files:
        path = os.path.join(self.out_dir, fi['path'])

        # TODO: use DirMaker from tree-tools?
        try:
          os.makedirs(os.path.dirname(path))
        except OSError, e:
          if e.errno != errno.EEXIST:
            # TODO: catch exceptions in other threads?
            raise

        with open(path, 'w') as f:
          f.write(fi['contents'])
      i += 1

      self.out_q.put(i)  # notify consumer that we're ready to write
      #log('put %r', i)


class Notify(object):
  """Thread to read from queue and notify waiter."""

  def __init__(self, q, waiter):
    """
    Args:
      q: Queue
      waiter: SequenceWaiter object
    """
    self.q = q
    self.waiter = waiter

  def __call__(self):
    # take care of index.html ?  Is this the right way to do it?
    unused = self.q.get()
    while True:
      unused = self.q.get()
      self.waiter.Notify()


def SuffixGen():
  """Generate a readable suffix for a session name

  (when more than one is used in a day)
  """
  i = ord('a')
  for c in string.lowercase:
    yield '-' + c

  # These shouldn't get used because people shouldn't start more than 26
  # sessions in a day.  But we prefix them with -z so they will sort later (at
  # least z0 through z9 will)
  i = 0
  while True:
    yield '-z' + str(i)
    i += 1


def MakeSession(out_dir):
  prefix = datetime.datetime.now().strftime('%Y-%m-%d')
  suffix = ''
  s = SuffixGen()
  while True:
    session = prefix + suffix
    full_path = os.path.join(out_dir, session)
    if not os.path.exists(full_path):
      os.makedirs(full_path)
      log('Created session dir %s', full_path)
      break
    suffix = s.next()
  return session, full_path


def Serve(opts, waiter):
  # Pipeline:
  # Read stdin messages -> Write to disk -> notify server

  # TODO:
  # Also support:
  # filenames -> read-files -> (machine boundary) -> file2html -> write to
  # disk -> notify server

  q1 = Queue.Queue()
  q2 = Queue.Queue()

  r = ReadStdin(q1)
  t1 = threading.Thread(target=r)
  t1.setDaemon(True)  # So Ctrl-C works
  t1.start()

  session_name, session_path = opts.session or MakeSession(opts.out_dir)

  w = WriteFiles(q1, q2, session_path)
  t2 = threading.Thread(target=w)
  t2.setDaemon(True)  # So Ctrl-C works
  t2.start()

  n = Notify(q2, waiter)
  t3 = threading.Thread(target=n)
  t3.setDaemon(True)  # So Ctrl-C works
  t3.start()

  # TODO:
  # - server should get root dir ~/webpipe/s
  # - waiters is {"session", waiter}
  # There's only one waiter I guess.  the rest of it is just served.

  # Serve from the same port that WriteFiles is writing to.
  waiters = {session_name: waiter}

  handler_class = wait_server.WaitingRequestHandler
  handler_class.root_dir = opts.out_dir
  handler_class.waiters = waiters

  s = httpd.ThreadedHTTPServer(('', opts.port), handler_class)

  # TODO: add opts.hostname?
  log('Serving at http://localhost:%d/  (Ctrl-C to quit)', opts.port)
  s.serve_forever()


def CreateOptionsParser():
  parser = optparse.OptionParser('webpipe_main <action> [options]')

  parser.add_option(
      '-v', '--verbose', dest='verbose', default=False, action='store_true',
      help='Write more log messages')
  parser.add_option(
      '-s', '--session', dest='session', type='str', default='',
      help="Name of the session (by default it is based on today's date)")
  parser.add_option(
      '--port', dest='port', type='int', default=8989,
      help='Port to serve on')
  parser.add_option(
      '--length', dest='length', type='int', default=1000,
      help='Length of the scroll, i.e. amount of history to keep.')
  parser.add_option(
      '--num-threads', dest='num_threads', type='int', default=5,
      help='Number of server threads, i.e. simultaneous connections.')

  # argument to "file2html" is an input dir.  This is the output dir.

  # scrolls go in the 's' dir
  parser.add_option(
      '--out-dir', dest='out_dir', type='str',
      default=os.path.expanduser('~/webpipe/s'),
      help='Base directory for scrolls')

  # TODO:
  # - merge options from other modules?  from file2html?
  # - --stages flag?

  return parser


def AppMain(argv):
  """Returns the length of the scroll created."""

  try:
    action = argv[1]
  except IndexError:
    raise Error('Action required')

  global _verbose
  (opts, _) = CreateOptionsParser().parse_args(argv[2:])
  if opts.verbose:
    _verbose = True

  waiter = wait_server.SequenceWaiter()

  # Other actions:
  # render (or should they just use file2html?)
  # serve-rendered (or servehtml)
  # refresh

  if action == 'serve':
    try:
      Serve(opts, waiter)
    except KeyboardInterrupt:
      log('Stopped')
      return waiter.Length()
  else:
    raise Error('Invalid action %r' % action)



def main(argv):
  """Returns an exit code."""

  spy_client = spy.GetClientFromConfig()

  d = {'argv': sys.argv, 'user': getpass.getuser()}
  spy_client.SendRecord('start', d)

  # TODO: also report unhandled exceptions.  The ones in the serving thread are
  # caught by a library though -- we should get at them.
  try:
    length = AppMain(sys.argv)
    d = {'scroll-length': length}
    spy_client.SendRecord('end', d)
  except Error, e:
    print >>sys.stderr, 'webpipe:', e.args[0]
    return 1

  return 0


if __name__ == '__main__':
  sys.exit(main(sys.argv))
