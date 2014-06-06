#!/usr/bin/python
#
# Copyright 2014 Google Inc. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found
# in the LICENSE file or at https://developers.google.com/open-source/licenses/bsd

"""
xrender.py

A filter that reads filenames from stdin, and prints HTML directories on
stdout.

TODO: Make this usable as a library too?  So in the common case you can have a
single process.

File types:

Next:

- .grep -- grep results
  - But then do we have to copy a ton of files over?
  - xrender needs have access to the original directory.
  - and the command


Plugins
-------

See comments below for the interface.

"Style Guide".  Things plugins should do:

- check size of file (whether in bytes, entries, depth, etc.)
  - small: just display it inline (and possibly summary)
  - large: display summary, then click through to full view
  - huge: display summary, and message that says it's too big to preview

- summary:
  - size in bytes
  - entries, etc.

- provide original file for download (in most cases)

- zero copy
  - if you make a symlink, then the plugin can read that stuff, create a
    summary
  - and then can it output a *capability* for the server to serve files
    anywhere on the file system?
    - or perhaps the symlink is enough?  well it could change.
    - maybe you have to dereference the link.
"""

import getopt
import json
import os
import re
import socket
import subprocess
import sys
import time

import tnet

from common import util
from common import spy


class Error(Exception):
  pass


log = util.Logger(util.ANSI_GREEN)


BAD_RE = re.compile(r'[^a-zA-Z0-9_\-]')

def CleanFilename(filename):
  """Return an escaped filename that's both HTML and shell safe.

  If it weren't shell safe, then
  
    cp $input $output

  Would fail if $input had spaces.

  If it weren't HTML safe, then

    <a href="$output"></a>

  would result in XSS if $output had a double quote.

  We use @hh, where h is a hex digit.  For example, @20 for space.
  """
  assert isinstance(filename, str)  # byte string, not unicode
  return BAD_RE.sub(lambda m: '@%x' % ord(m.group(0)), filename)


# TODO: use mime types here?
# The two-level hierarchy of:
# image/png, image/gif, etc. might be useful
#
# Also: aliases like htm, html, etc. are detected

def GetFileType(input_path):
  """
  Args:
    input_path: could be relative or absolute
  """
  basename = os.path.basename(input_path)

  # NOTE: Don't use os.path.splitext because it takes only the LAST extension.
  # We want "tar.gz", not "gz" it takes the LAST extension.  We want "tar.gz",
  # not "gz".

  i = basename.find('.')
  if i == -1:
    # e.g. 'Makefile'
    return basename
  else:
    # e.g. tar.gz, png
    return basename[i+1:]


# TODO: Move this to util/resources or something
# find rendering plugins, publishing plugins, etc.
# used in publish.py, xrender.py, handlers.py

class Resources(object):
  def __init__(self, package_dir=None):
    self.package_dir = util.GetPackageDir()
    self.user_dir = util.GetUserDir()

  def GetPluginBin(self, file_type):
    # plugins dir is parallel to webpipe python dir.
    u = os.path.join(self.user_dir, 'plugins', file_type, 'render')
    p = os.path.join(self.package_dir, 'plugins', file_type, 'render')

    # TODO: test if it's executable.  Show clear error if not.
    if os.path.exists(u):
      return u
    if os.path.exists(p):
      return p
    return None


def PluginDispatchLoop(in_dir, out_dir):
  """
  Coroutine that passes its input to a rendering plugin.
  """

  # TODO:
  # - input is a single line for now.  Later it could be a message, if you want
  # people to specify an explicit file type.  I guess that can be done with a
  # file extension too, like typescript.ansi.  The problem is that you can't
  # get any other options with it.
  # - output is pointer to files/dirs written.

  spy_client = spy.GetClientFromConfig()
  res = Resources()

  entries = os.listdir(out_dir)
  nums = []
  for e in entries:
    m = re.match(r'(\d+)\.html', e)
    if m:
      nums.append(int(m.group(1)))

  if nums:
    maximum = max(nums)
  else:
    maximum = 0

  counter = maximum + 1  # application is 1-indexed
  log('counter initialized to %d', counter)

  # e.g. we are about to write "1"
  header = json.dumps({'stream': 'netstring', 'nextPart': counter})

  # Print it on a single line.  Also allow netstring parsing.  Minimal
  # JSON/netstring header is: 2:{}\n.
  sys.stdout.write(tnet.dump_line(header))

  while True:
    # NOTE: This is a coroutine.
    filename = yield
    # TODO: If file contains punctuation, escape it to be BOTH shell and HTML
    # safe, and then MOVE It to ~/webpipe/safe-name

    # NOTE: Right now, this allows absolute paths too.
    input_path = os.path.join(in_dir, filename)

    # TODO: Plugins should be passed directories directly.
    if os.path.isdir(input_path):
      log('Skipping directory %s (for now)', input_path)
      continue

    # TODO: handle errors
    try:
      with open(input_path) as f:
        contents = f.read()
    except IOError, e:
      # e.g. file doesn't exist.  Just log and ignore for now.
      # Someone could type 'wp show nonexistent'.
      log('%s', e)
      continue

    file_type = GetFileType(filename)
    log('file type: %s', file_type)

    out_html_filename = '%d.html' % counter
    out_html_path = os.path.join(out_dir, out_html_filename)

    # Order of resolution:
    #
    # 1. Check user's ~/webpipe dir for plugins
    # 2. Check installation dir for plugins distributed with the webpipe
    #    package
    # 3. Builtins

    # The DEFAULT plugin should handle everything
    plugin_bin = res.GetPluginBin(file_type) or res.GetPluginBin('DEFAULT')
    if plugin_bin:

      # protocol is:
      # render <input> <output>
      #
      # output is just "3".  You are allowed to create the file 3.html, and
      # optionally the *directory* 3.
      #
      # You must print all the files you create to stdout, and output nothing
      # else.
      #
      # Other tools may output stuff on stdout.  You should redirect them to
      # stderr with: 1>&2.  stderr could show up in debug output on the web
      # page (probably only if the exit code is 1?)
      #
      # In the error case, xrender.py should write 3.html, along with a log
      # file?  The html should preview it, but only if it's long.  Use the .log
      # viewer.
      #
      # NOTE: In the future, we could pass $WEBPIPE_ACTION if we want a
      # different type of rendering?

      argv = [plugin_bin, input_path, str(counter)]
      log('argv: %s cwd %s', argv, out_dir)

      subprocess_exc = None  # record
      start_time = time.time()
      try:
        exit_code = subprocess.call(argv, cwd=out_dir)
      except OSError, e:
        subprocess_exc = e
        log('%s', e)
        # NOTE: should we be consistent and print in the HTML window?
        continue

      elapsed = time.time() - start_time

      if exit_code != 0:
        log('ERROR: %s exited with code %d', argv, exit_code)
        with open(out_html_path, 'w') as f:
          # TODO:
          # - make a nicer template.  
          # - show stderr
          f.write('ERROR: %s exited with code %d' % (argv, exit_code))
        counter += 1
        continue

      # BUG: These aren't send in error case!   Fix that.

      # Record how long rendering plugin takes.
      d = {'pluginPath': plugin_bin, 'exitCode': exit_code, 'elapsed': elapsed}
      if subprocess_exc:
        d['subprocessExc'] = str(subprocess_exc)
      spy_client.SendRecord('xrender-plugin', d)

      # Check that the plugin actually create the file.
      if not os.path.exists(out_html_path):
        log('Plugin error: %r not created', out_html_path)
        with open(out_html_path, 'w') as f:
          f.write('Plugin error: %r not created' % out_html_path)

        # TODO: Remove this counter duplication.  Failing here would make it
        # hard to develop plugins.
        counter += 1
        continue

    else:
      log('No renderer for %r and no DEFAULT; ignored', filename)
      continue

    counter += 1


def Lines(f, target):
  """
  Read lines from the given file object and deliver to the given coroutine.
  """
  target.next()  # "prime" coroutine

  while True:
    line = f.readline()
    if not line:  # EOF
      break

    filename = line.strip()
    try:
      target.send(filename)
    except StopIteration:
      break


# Max 1 megabyte.  We close it anyway.
BUF_SIZE = 1 << 20

# TODO: Should this be moved to "util" so other stages can use it?
def TcpServer(port, target):
  """
  Listen on a port, and read (small) values send from different clients, and
  deliver them to the given coroutine.

  This basically replaces "nc -k -l 8000 </dev/null", which is not portable
  across machines (especially OS X).
  """
  sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  # When we die, let other processes use port immediately.
  sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
  sock.bind(('', port))
  sock.listen(1)  # backlog of 1; meant to be used on localhost
  log('Listening on port %d', port)

  target.next()  # "prime" coroutine

  while True:
    client, addr = sock.accept()
    log('Connection from %s', addr)

    # The payload is a line right now.  Should we loop until we actually get a
    # newline?  Could test a trickle.
    line = client.recv(BUF_SIZE)
    client.close()
    if not line:
      break

    filename = line.strip()
    try:
      target.send(filename)
    except StopIteration:
      break


def main(argv):
  """Returns an exit code."""
  port = None

  # Just use simple getopt for now.  This isn't exposed to the UI really.
  opts, argv = getopt.getopt(argv, 'p:')
  for name, value in opts:
    if name == '-p':
      try:
        port = int(value)
      except ValueError:
        raise Error('Invalid port %r' % value)
    else:
      raise AssertionError

  # NOTE: This is the input base path.  We just join them with the filenames
  # on stdin.
  in_dir = argv[0]
  out_dir = argv[1]

  # PluginDispatchLoop is a coroutine.  It takes items to render on stdin.
  loop = PluginDispatchLoop(in_dir, out_dir)

  # TODO:
  # create a tcp server.  reads one connection at a timv 

  if port:
    TcpServer(port, loop)
  else:
    Lines(sys.stdin, loop)

  return 0


if __name__ == '__main__':
  try:
    sys.exit(main(sys.argv[1:]))
  except KeyboardInterrupt:
    log('Stopped')
    sys.exit(0)
  except Error, e:
    print >> sys.stderr, e.args[0]
    sys.exit(1)
