#!/usr/bin/python
"""
latch.py

Latch server (based on code from polyweb repo).
"""

import sys
import threading


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


def main(argv):
  """Returns an exit code."""
  print 'Hello from latch.py'
  return 0


if __name__ == '__main__':
  try:
    sys.exit(main(sys.argv))
  except Error, e:
    print >> sys.stderr, e.args[0]
    sys.exit(1)
