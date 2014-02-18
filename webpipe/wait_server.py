"""
wait_server.py

Server that does a hanging get.  Doesn't need to be a WSGI app I think.

Override SimpelHttpServer.

Only things like /<roll-name/1/ can hang.

Even index.html should be static?

There is a thread that reads from a Queue.  And then some event does it.o

Hanger() -- this is an object that hangs at the right moment.
Blocker()


"""

import os
import re
import threading

from common import log
import httpd

import jsontemplate



HOME_PAGE = jsontemplate.Template("""\
<h3>webpipe index</h3>

{.repeated section sessions}
  <a href="{@|htmltag}">{@}</a> <br/>
{.end}
""", default_formatter='html')


# /session/partnum.html
PATH_RE = re.compile(r'/(\S+)/(\d+).html$')

class WaitingRequestHandler(httpd.BaseRequestHandler):
  """
  differences:
  - block on certain paths
  - don't always serve in the current directory, let the user do it.
  - daemon threads so we don't block the process
  - what about cache headers?  I think I saw a bug where the browser would
    cache instead of waiting.
  """
  server_version = "webpipe"
  waiters = None

  def send_webpipe_index(self):
    self.send_response(200)
    self.send_header('Content-Type', 'text/html')
    self.end_headers()
    
    # Session are saved on disk; allow the user to choose one.

    dirs = os.listdir(self.root_dir)
    dirs.sort(reverse=True)
    html = HOME_PAGE.expand({'sessions': dirs})
    self.wfile.write(html)

  def do_GET(self):
    """Serve a GET request."""

    if self.path == '/':
      self.send_webpipe_index()
      return

    m = PATH_RE.match(self.path)
    if m:
      session, num = m.groups()
      num = int(num)
      i = num - 1  # container is 0-based

      waiter = self.waiters.get(session)
      if waiter is not None:
        log('PATH: %s', self.path)

        log('MaybeWait session %r, part %d', session, i)
        result = waiter.MaybeWait(i)
        log('Done %d', i)
        # result could be:
        # 404: too big
        # 503: 503

    # Serve static file.

    f = self.send_head()
    if f:
      self.copyfile(f, self.wfile)
      f.close()



WAIT_OK, WAIT_TOO_BIG, WAIT_TOO_BUSY = range(3)

class SequenceWaiter(object):
  """
  Call Notify() for every item.  Then you can call MaybeWait(n) for.
  """
  def __init__(self, max_waiters=None):
    # If this limit it
    self.max_waiters = max_waiters

    self.events = [threading.Event()]
    self.lock = threading.Lock()  # protects self.events
    self.counter = 0

  def MaybeWait(self, n):
    """
    Returns:
      success.
      200 it's OK to proceed (we may have waited)
      404: index is too big?
      503: maximum waiters exceeded.
    """
    i = self.counter

    # Block for the next item
    if i > n:
      #print '%d / %d' % (i, n)
      #print self.items
      return WAIT_OK
    elif i == n:
      log('Waiting for event %d', i)
      self.events[i].wait()  # wait for it to be added
      return WAIT_OK
    else:
      return WAIT_TOO_BIG

  def Notify(self):
    # *Atomically* append item N and event N+1.
    with self.lock:
      n = self.counter
      self.counter += 1

      # Now add another event to wait on.
      e = threading.Event()
      self.events.append(e)

    # unblock all MaybeWait() calls
    self.events[n].set()
