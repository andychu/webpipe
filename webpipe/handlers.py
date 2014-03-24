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
import sys
import threading

from common import util
from common import httpd

import jsontemplate

log = util.Logger(util.ANSI_BLUE)



# TODO:
# - The "Directory Listing" page should let you go back up.
# - common CSS for all pages.  put "plugins" div to the side.
# - show live scrolls

HOME_PAGE = jsontemplate.Template("""\
<html>
  <head>
    <title>json $output</title>
    <link href="/static/webpipe.css" rel="stylesheet">
  </head>
  <body>
    <h2>webpipe</h2>

    <div id="scrolls">
      <h4>Scrolls</h4>

      {.repeated section scrolls}
        <a href="s/{@|htmltag}">{@}</a> <br/>
      {.end}

      <p>
        (<a href="s/">browse</a>)
      </p>
    </div>

    <div id="links">
      <p><a href="plugins/">plugins</a></p>
    </div>

  </body>
</html>
""", default_formatter='html')


# TODO: put file system paths here?  So people can easily find their plugins.
PLUGINS_PAGE = jsontemplate.Template("""\
<p align="right">
  <a href="/">Home</a>
<p>

<h2>webpipe Plugins</h2>

<h3>User plugins installed in ~/webpipe</h3>

<p><i>User plugins override packaged plugins.</i></p>

<ul>
{.repeated section user}
  <li>{name} {.if test static} <a href="{name}/static/">static</a> {.end} </li>
{.end}
</ul>

<h3>Packaged Plugins</h3>

<ul>
{.repeated section package}
  <li>{name} {.if test static} <a href="{name}/static/">static</a> {.end} </li>
{.end}
</ul>
""", default_formatter='html')


# /s//<session>/<partnum>.html
PATH_RE = re.compile(r'/s/(\S+)/(\d+).html$')


def _ListPlugins(root_dir):
  """
  Returns a template data dictionary.  Plugins are directories.  Plugins with
  'static' dirs are marked.
  """
  plugin_root = os.path.join(root_dir, 'plugins')
  data = []
  for name in os.listdir(plugin_root):
    path = os.path.join(plugin_root, name)
    if not os.path.isdir(path):
      continue
    p = os.path.join(path, 'static')
    s = os.path.isdir(p)
    # e.g. {name: csv, static: True}
    data.append({'name': name, 'static': s})
  data.sort(key=lambda d: d['name'])
  return data


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
  root_dir = None  # from BaseRequestHandler, not used
  user_dir = None  # initialize to ~/webpipe
  package_dir = None  # initialize to /<package>/webpipe
  waiters = None

  def send_webpipe_index(self):
    self.send_response(200)
    self.send_header('Content-Type', 'text/html')
    self.end_headers()
    
    s_root = os.path.join(self.user_dir, 's')
    scrolls = os.listdir(s_root)
    scrolls.sort(reverse=True)

    h = HOME_PAGE.expand({'scrolls': scrolls})
    self.wfile.write(h)

  def send_plugins_index(self):
    self.send_response(200)
    self.send_header('Content-Type', 'text/html')
    self.end_headers()
    
    # Session are saved on disk; allow the user to choose one.

    u = _ListPlugins(self.user_dir)
    p = _ListPlugins(self.package_dir)

    html = PLUGINS_PAGE.expand({'user': u, 'package': p})
    self.wfile.write(html)

  def url_to_fs_path(self, url):
    """Translate a URL to a local file system path.

    By default, we just treat URLs as paths relative to self.user_dir.

    If it returns None, then a 404 is generated, without looking at disk.

    Called from send_head() (see SimpleHTTPServer).

    NOTE: This is adapted from Python stdlib SimpleHTTPServer.py.
    """
    # Disallow path traversal with '..'
    parts = [p for p in url.split('/') if p and p not in ('.', '..')]
    if not parts:  # corresponds to /, which is already handled by send_webpipe_index
      return None
    first_part = parts[0]
    rest = parts[1:]

    if first_part == 's':
      return os.path.join(self.user_dir, *parts)

    if first_part == 'plugins':
      # looking for ['plugins', <anything>, 'static'].
      # Note these can be files OR directories.  Directories will be listed.
      if len(parts) >= 3 and parts[2] == 'static':
        packaged_res = os.path.join(self.package_dir, *parts)
        user_res = os.path.join(self.user_dir, *parts)

        # Return the one that exists, starting with the user dir.
        if os.path.exists(user_res):
          return user_res
        if os.path.exists(packaged_res):
          return packaged_res

    return None

  def do_GET(self):
    """Serve a GET request."""

    if self.path == '/':
      self.send_webpipe_index()
      return

    if self.path == '/plugins':
      # As is done in send_head
      self.send_response(301)
      self.send_header("Location", self.path + "/")
      self.end_headers()
      return

    if self.path == '/plugins/':
      self.send_plugins_index()
      return

    m = PATH_RE.match(self.path)
    if m:
      session, num = m.groups()
      num = int(num)

      waiter = self.waiters.get(session)
      if waiter is not None:
        log('PATH: %s', self.path)

        log('MaybeWait session %r, part %d', session, num)
        result = waiter.MaybeWait(num)
        log('Done %d', num)
        # result could be:
        # 404: too big
        # 503: 503

    # Serve static file.

    # NOTE: url_to_fs_path is called in send_head.
    f = self.send_head()

    # f is None if the file doesn't exist, and send_error(404) was called.
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

    # even, odd scheme.  When one event is notified, the other is reset.
    self.events = [threading.Event(), threading.Event()]
    self.lock = threading.Lock()  # protects self.events
    self.counter = 1

  def SetCounter(self, n):
    # TODO: Make this a constructor param?
    assert self.counter == 1, "Only call before using"
    self.counter = n

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
      log('Waiting for event %d (%d)', i, i % 2)
      self.events[i % 2].wait()  # wait for it to be added
      return WAIT_OK
    else:
      return WAIT_TOO_BIG

  def Notify(self):
    # *Atomically* increment counter and add event event N+1.
    with self.lock:
      n = self.counter
      self.counter += 1

      # instantiate a new event in the other space
      self.events[self.counter % 2] = threading.Event()

    # unblock all MaybeWait() calls
    self.events[n % 2].set()

  def Length(self):
    return self.counter

