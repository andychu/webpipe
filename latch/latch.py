#!/usr/bin/python
"""
latch.py

Latch server (based on code from polyweb repo).
"""

import optparse
import sys
import threading

import templates
from webpipe import wait_server  # temporary
from webpipe import common

log = common.log


class Error(Exception):
  pass


class LatchApp(object):
  """Get and set latches."""

  def __init__(self, num_slots=3):
    """
    Args:
      num_slots: Maximum number of simultaneous waiters.  We don't want to take
          up all the threads in the server, so this is limited.
    """
    self.slots = threading.Semaphore(num_slots)
    # threading.Condition()?  or Queue.Queue()?
    # Simply dictionary
    # when you get a GET, just do .get().  Block forever.
    # when you get a POST, just do .put().
    self.latches = {'default': threading.Event()}

  def HandleRequest(self, request):
    # Is there a better way to do this?
    route = request['__META_INTERNAL']['route']  # hack to get route
    if route == 'index':
      data = {'latches': self.latches.keys()}
    elif route == 'wait':
      name = request['latch_name']

      ok = self.slots.acquire(False)
      if not ok:
        return util.TextResponse(503, 'All slots taken')

      event = self.latches.get(name)
      if not event:
        return util.TextResponse(404, 'Unknown latch %r' % name)

      start = time.time()
      event.wait()
      elapsed = time.time() - start

      self.slots.release()

      return util.TextResponse(200,
          'Waited %.2f seconds for latch %r.' % (elapsed, name))

    elif route == 'notify':
      name = request['latch_name']
      event = self.latches.get(name)
      if not event:
        return util.TextResponse(404, 'Unknown latch %r' % name)
      event.set()

      # Reset the flag so we can wait again.
      event.clear()
      return util.TextResponse(200, 'Notified all waiters on latch %r.' % name)

    else:
      # App should have prevented this
      raise AssertionError("Invalid route %r" % route)
    return {'body_data': data}


def CreateOptionsParser():
  parser = optparse.OptionParser('webpipe_main <action> [options]')

  parser.add_option(
      '-v', '--verbose', dest='verbose', default=False, action='store_true',
      help='Write more log messages')
  parser.add_option(
      '--port', dest='port', type='int', default=8990,
      help='Port to serve on')
  parser.add_option(
      '--num-threads', dest='num_threads', type='int', default=5,
      help='Number of server threads, i.e. simultaneous connections.')

  parser.add_option(
      '--root-dir', dest='root_dir', type='str',
      default='_tmp',
      help='Directory to serve out of.')

  return parser


def main(argv):
  """Returns an exit code."""

  (opts, _) = CreateOptionsParser().parse_args(argv[2:])

  # TODO:
  # pass request handler map
  # - index
  # - latch
  # - static
  #   - except this filters self.wfile
  #   - <!-- INSERT LATCH JS -->

  s = wait_server.WaitServer('', opts.port, opts.root_dir, None)

  #log("Serving on port %d... (Ctrl-C to quit)", opts.port)
  s.Serve()


if __name__ == '__main__':
  try:
    sys.exit(main(sys.argv))
  except Error, e:
    print >> sys.stderr, e.args[0]
    sys.exit(1)
