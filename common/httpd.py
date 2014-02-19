#!/usr/bin/python
"""
httpd.py
"""

import BaseHTTPServer
import os
import posixpath
import SimpleHTTPServer
import SocketServer
import urllib


class ThreadedHTTPServer(SocketServer.ThreadingMixIn,
                         BaseHTTPServer.HTTPServer):
  """
  The main reason we inherit from HTTPServer instead of SocketServer is that it
  sets allow_reuse_address, which prevents the issue where we can't bind the
  same port for a period of time after restarting.

  NOTE: This doesn't use a thread pool or anything.  It will just start a new
  thread for each request.
  
  For webpipe, since every thread will block waiting for the next part of the
  scroll, you can create a huge number of threads just by having a huge number
  of clients.  But since this is mainly a single-user server, it doesn't
  matter.

  TODO: There's a still a Ctrl-C bug here, because I think the request threads
  get blocked on the threading.Event().  Need to setDaemon() all threads,
  including the ones that the web server makes.
  """
  # override class variable in ThreadingMixIn.  This makes it so that Ctrl-C works.
  daemon_threads = True


class BaseRequestHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
  """
  NOTE: The structure of Python's SimpleHTTPServer / BaseHTTPServer is quite
  bad.  But we are reusing it for now, since it is built in to the standard
  library, and it gives "Apache-like" static serving semantics.

  If we end up having to hack this up too much, it might be worth it to write
  our own (or at least copy and modify that code, rather than this fragile
  inheritance.
  """
  server_version = None
  root_dir = None

  def translate_path(self, path):
    """Translate a /-separated PATH to the local filename syntax.

    NOTE: This is copied from Python stdlib SimpleHTTPServer.py.  I just
    changed os.getcwd() to self.root_dir.
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

