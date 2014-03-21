#!/usr/bin/python
"""
webpipe.py

Server that receives content from a pipe, and serves it "interactively" to the
browser.  It relies on a "hanging GET" -- jQuery on the client and
threading.Event on the server.
"""

import datetime
import errno
import getpass
import json
import optparse
import os
import Queue
import threading
import string  # for lower case letters
import sys

from common import httpd
from common import util
from common import spy

import handlers

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
  """Read filenames from stdin and put them on a queue."""

  def __init__(self, q):
    """
    Args:
      q: Queue, can be None
    """
    self.q = q

  def __call__(self):
    log('stdin 2')
    # TODO: read header?
    # if it doesn't start with 'lines:' or '[lines]' or 
    # protocol:
    # readline first... if line starts with '3:', then you need to read header
    # as JSON?  or tnet?

    while True:
      # must be unbuffered
      line = sys.stdin.readline()
      if not line:
        break

      line = line.rstrip()
      log('putting %r', line)
      self.q.put(line)


class Notify(object):
  """Thread to read from queue and notify waiter."""

  def __init__(self, q, waiter, spy_client):
    """
    Args:
      q: Queue
      waiter: SequenceWaiter object
    """
    self.q = q
    self.waiter = waiter
    self.spy_client = spy_client

  def __call__(self):
    # take care of index.html ?  Is this the right way to do it?
    #unused = self.q.get()
    i = 0
    while True:
      name = self.q.get()
      log('notify: %s', name)

      # TODO: do a better check
      if not name.endswith('.html'):
        log('skipped: %s', name)
        continue

      self.waiter.Notify()

      i += 1
      # For now, just how many parts there are.  Later we could see what file
      # types are being used.
      #
      # We send 'num-parts: 10' AFTER we have notified 10 parts.
      if i % 10 == 0:
        self.spy_client.SendRecord('every10', {'num-parts': i})


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


def Serve(opts, waiter, deploy_dir, spy_client):
  # Pipeline:
  # Read stdin messages -> notify server

  header_line = sys.stdin.readline()
  # skip over length prefix
  i = header_line.find(':')
  if i == -1:
    raise Error('Expected colon in header line: %r' % header_line)

  header = json.loads(header_line[i+1:])
  log('received header %r', header)

  next_part = header.get('nextPart')
  if next_part is not None:
    if isinstance(next_part, int):
      waiter.SetCounter(next_part)
      log('received counter state in header: %d', next_part)
    else:
      log('Ignored invalid nextPart %r', next_part)

  q = Queue.Queue()

  r = ReadStdin(q)
  t1 = threading.Thread(target=r)
  t1.setDaemon(True)  # So Ctrl-C works
  t1.start()

  if opts.session:
    session_path = opts.session
    session_name = os.path.basename(session_path)
  else:
    session_name, session_path = MakeSession(opts.out_dir)

  n = Notify(q, waiter, spy_client)
  t2 = threading.Thread(target=n)
  t2.setDaemon(True)  # So Ctrl-C works
  t2.start()

  # TODO:
  # - server should get root dir ~/webpipe/s
  # - waiters is {"session", waiter}
  # There's only one waiter I guess.  the rest of it is just served.

  waiters = {session_name: waiter}

  handler_class = handlers.WaitingRequestHandler
  handler_class.user_dir = opts.user_dir
  handler_class.deploy_dir = deploy_dir
  handler_class.waiters = waiters

  s = httpd.ThreadedHTTPServer(('', opts.port), handler_class)

  # TODO: add opts.hostname?
  log('Serving at http://localhost:%d/  (Ctrl-C to quit)', opts.port)
  s.serve_forever()

  # NOTE: Could do webbrowser.open() after we serve.  But people can also just
  # click the link we printed above, since most terminals will make them URLs.


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

  # scrolls go in the 's' dir, plugins in the 'plugins' dir
  parser.add_option(
      '--user-dir', dest='user_dir', type='str',
      default=os.path.expanduser('~/webpipe'),
      help='Per-user directory for webpipe')

  return parser


def AppMain(argv, spy_client):
  """Returns the length of the scroll created."""

  try:
    action = argv[1]
  except IndexError:
    raise Error('Action required')

  global _verbose
  (opts, _) = CreateOptionsParser().parse_args(argv[2:])
  if opts.verbose:
    _verbose = True

  waiter = handlers.SequenceWaiter()

  # Other actions:
  # serve-rendered (or servehtml)
  # refresh

  if action == 'serve':  # TODO: rename to 'serve'
    # TODO: clean up this usage.  I guess these should be flags.  Perhaps
    # optionally as positional arguments.
    session = argv[2]
    opts.session = session

    # Write index.html in the session dir.
    this_dir = os.path.dirname(sys.argv[0])  # webpipe subdir
    deploy_dir = os.path.dirname(this_dir)  # root of package
    path = os.path.join(this_dir, 'index.html')
    with open(path) as f:
      index_html = f.read()

    out_path = os.path.join(session, 'index.html')
    with open(out_path, 'w') as f:
      f.write(index_html)

    try:
      Serve(opts, waiter, deploy_dir, spy_client)
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
    length = AppMain(sys.argv, spy_client)
    d = {'scroll-length': length}
    spy_client.SendRecord('end', d)
  except Error, e:
    print >>sys.stderr, 'webpipe:', e.args[0]
    return 1

  return 0


if __name__ == '__main__':
  sys.exit(main(sys.argv))
