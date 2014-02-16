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

import BaseHTTPServer
import os
import posixpath
import re
import sys
import SimpleHTTPServer
import SocketServer
import threading
import time
import urllib

from common import log

import jsontemplate



HOME_PAGE = jsontemplate.Template("""\
<h3>webpipe</h3>

{.repeated section sessions}
  <a href="{@|htmltag}">{@}</a> <br/>
{.end}
""", default_formatter='html')


# /session/partnum.html
PATH_RE = re.compile(r'/(\S+)/(\d+).html$')

class ThreadedHTTPServer(SocketServer.ThreadingMixIn,
                         BaseHTTPServer.HTTPServer):
  """
  The main reason we inherit from HTTPServer instead of SocketServer is that it
  sets allow_reuse_address, which prevents the issue where we can't bind the
  same port for a period of time after restarting.
  """
  pass


class WaitingRequestHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
  """
  differences:
  - block on certain paths
  - don't always serve in the current directory, let the user do it.
  - daemon threads so we don't block the process
  - what about cache headers?  I think I saw a bug where the browser would
    cache instead of waiting.

  NOTE: The structure of Python's SimpleHTTPServer / BaseHTTPServer is quite
  bad.  But we are reusing it for now, since it is built in to the standard
  library, and it gives "Apache-like" static serving semantics.

  If we end up having to hack this up too much, it might be worth it to write
  our own (or at least copy and modify that code, rather than this fragile
  inheritance.

  How to pass it the queue?

  """
  server_version = "WebPipe"
  root_dir = None
  waiters = None
  session = None

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

  def translate_path(self, path):
      """Translate a /-separated PATH to the local filename syntax.

      NOTE: This is copied from Python stdlib SimpelHTTPServer.py, and we
      change os.getcwd() to self.root_dir.
      """
      # abandon query parameters
      path = path.split('?',1)[0]
      path = path.split('#',1)[0]
      path = posixpath.normpath(urllib.unquote(path))
      words = path.split('/')
      words = filter(None, words)
      path = self.root_dir  # note: class variable
      for word in words:
          drive, word = os.path.splitdrive(word)
          head, word = os.path.split(word)
          if word in (os.curdir, os.pardir): continue
          path = os.path.join(path, word)
      return path


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


class WaitServer(object):
  """
  Wrapper to hide the SocketServer guts from the stdlib.  The OO structure
  there is messy and worth hiding.
  """
  def __init__(self, host, port, root_dir, waiters):
    """
    Args:
      waiters: dictionary of {name -> SequenceWaiter}
    """
    self.host = host
    self.port = port
    self.root_dir = root_dir
    self.waiters = waiters

  def Serve(self):
    host_port = (self.host, self.port)

    # TODO: Add the current directory.  How hard is that?

    handler_class = WaitingRequestHandler
    handler_class.root_dir = self.root_dir  # this is so so lame
    handler_class.waiters = self.waiters

    # NOTE: This doesn't use a thread pool or anything.  It will just start a new
    # thread for each request.  Since every thread will block waiting for the
    # next part of the scroll, you can create a huge number of threads just by
    # having a huge number of clients.  But since this is mainly a single-user

    # TODO: There's a still a Ctrl-C bug here, because I think the request
    # threads get blocked on the threading.Event().  Need to setDaemon() all
    # threads, including the ones that the web server makes.

    s = ThreadedHTTPServer(host_port, handler_class)
    log('Serving on port %d', self.port)
    s.serve_forever()
