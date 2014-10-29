#!/usr/bin/python
"""
latch.py

Latch server (based on code from polyweb repo).
"""

import optparse
import re
import os
import sys
import threading

import jsontemplate

from common import httpd
from common import util
from common import spy

import templates

log = util.Logger(util.ANSI_BLUE)


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


class Latches(object):

  def __init__(self, num_slots=5):
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
    self.latches = {}
    self.lock = threading.Lock()  # protect self.latches

  def Wait(self, name):
    assert isinstance(name, str) and len(name) > 0, name

    with self.lock:  # don't want a race between checking and setting
      event = self.latches.get(name)
      if event is None:
        event = threading.Event()
        self.latches[name] = event

    log('waiting on %r', name)
    event.wait()

  def Notify(self, name):
    """Returns whether the named latch was successfully notified."""
    event = self.latches.get(name)
    if event:
      event.set()
      # Reset the flag so we can wait again.
      event.clear()
      return True
    else:
      return False


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


HOME_PAGE = jsontemplate.Template("""\
<h3>latch</h3>

{.repeated section pages}
  <a href="{@|htmltag}">{@}</a> <br/>
{.end}
""", default_formatter='html')


LATCH_PATH_RE = re.compile(r'/-/latch/(\S+)$')

# TODO: Rewrite latch.js using raw XHR, and get rid of jQuery.  This could
# interfere with pages that have jQuery already.
LATCH_HEAD = """\
<script type='text/javascript'
  src="https://ajax.googleapis.com/ajax/libs/jquery/1.8.3/jquery.min.js">
</script>

<script src="/-/latch.js"></script>
"""

LATCH_BODY = """\
<p id="latch-status">Waiting for latch...</p>
"""

class LatchRequestHandler(httpd.BaseRequestHandler):
  """
  Notify latches
  """
  server_version = "Latch"
  latches = None
  latch_js = None

  def send_index(self):
    self.send_response(200)
    self.send_header('Content-Type', 'text/html')
    self.end_headers()
    
    pages = os.listdir(self.root_dir)
    pages.sort(reverse=True)
    html = HOME_PAGE.expand({'pages': pages})
    self.wfile.write(html)

  def send_content(self, content_type, body):
    self.send_response(200)
    self.send_header('Content-Type', content_type)
    self.end_headers()

    self.wfile.write(body)

  def send_404(self, msg):
    self.send_response(404)
    self.send_header('Content-Type', 'text/plain')
    self.end_headers()

    self.wfile.write(msg + '\n')

  def do_GET(self):
    """Serve a GET request."""

    # NOTE:
    # GET notifies?
    # POST notifies?
    # do_POST?

    if self.path == '/':
      self.send_index()
      return

    if self.path == '/-/latch.js':
      self.send_content('application/javascript', self.latch_js)
      return

    m = LATCH_PATH_RE.match(self.path)
    if m:
      name = m.group(1)
      log('GET LATCH %s', name)

      # wait on or create the latch
      self.latches.Wait(name)

      self.send_content('text/plain', 'ok')
      return

    # Serve static file.
    # TODO: if it ends with HTML, search for <!-- INSERT LATCH JS -->

    f = self.send_head()
    if f:
      for line in f:
        stripped = line.strip()
        if stripped == '<!-- INSERT LATCH JS -->':
          out = LATCH_HEAD
          log('replaced %r', stripped)
        elif stripped == '<!-- INSERT LATCH HTML -->':
          out = LATCH_BODY
          log('replaced %r', stripped)
        else:
          out = line
        self.wfile.write(out)
      f.close()

  def do_POST(self):
    """Serve a POST request."""
    m = LATCH_PATH_RE.match(self.path)
    if not m:
      self.send_404('invalid resource %r' % self.path)
      return

    name = m.group(1)
    log('POST LATCH %s', name)

    success = self.latches.Notify(name)
    log('success %s', success)

    if success:
      self.send_content('text/plain', 'notified %r\n' % name)
    else:
      self.send_404('no latch named %r' % name)


def main(argv):
  """Returns an exit code."""

  (opts, _) = CreateOptionsParser().parse_args(argv[2:])

  # TODO:
  # pass request handler map
  # - index
  #   - list self.latches ?
  #   - if you click, does it wait?
  # /-/latch.js
  # /-/latch/README.html
  # /-/wait/
  # /-/notify/  -- or do those come on stdin?  or POST?

  # - latch
  # - static
  #   - except this filters self.wfile
  #   - <!-- INSERT LATCH JS -->

  latches = Latches()

  d = os.path.dirname(sys.argv[0])
  path = os.path.join(d, 'latch.js')
  with open(path) as f:
    latch_js = f.read()

  handler_class = LatchRequestHandler
  handler_class.root_dir = opts.root_dir
  handler_class.latches = latches
  handler_class.latch_js = latch_js

  s = httpd.ThreadedHTTPServer(('', opts.port), handler_class)

  log("Serving on port %d... (Ctrl-C to quit)", opts.port)
  s.serve_forever()


if __name__ == '__main__':
  try:
    sys.exit(main(sys.argv))
  except Error, e:
    print >> sys.stderr, e.args[0]
    sys.exit(1)
