#!/usr/bin/python
"""
xrender.py

A filter that reads filenames from stdin, and prints HTML directories on
stdout.

File types:

- .png -> inline HTML images (data URIs) 
- .csv -> table

Next:

- .script -- type script for Shell session
  - a configurable prefix, like "hostname; whoami;" etc. would be useful.
- .grep -- grep results
  - But then do we have to copy a ton of files over?
  - xrender needs have access to the original directory.
  - and the command

Ideas:

- .url file -> previews of URLs?
- .foo-url -> previews of a certain page?

Should this call a shell script then?  Or it could be a shell script?  The
function will use the tnet tool?

TODO: Make this usable as a library too?  So in the common case you can have a
single process.

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
  - if you make a symlink, then the plugin can read that stuff, create a summary
  - and then can it output a *capability* for the server to serve files
    anywhere on the file system?
    - or perhaps the symlink is enough?  well it could change.
    - maybe you have to dereference the link.
"""

import cgi
import errno
import json
import os
import re
import subprocess
import sys

import tnet

from common import util


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

def GuessFileType(filename):
  filename, ext = os.path.splitext(filename)
  if ext == '':
    # The 'script' command defaults to a file called 'typescript'.  We assume
    # the terminal is ansi, so we use the ansi plugin to handle it.
    if filename == 'typescript':
      return 'ansi'
    else:
      return None
  else:
    # .png -> png
    return ext[1:]

  return file_type


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


def main(argv):
  """Returns an exit code."""

  # NOTE: This is the input base path.  We just join them with the filenames on
  # stdin.
  in_dir = argv[1]
  out_dir = argv[2]
  # TODO:
  # - input is a single line for now.  Later it could be a message, if you want
  # people to specify an explicit file type.  I guess that can be done with a
  # file extension too, like typescript.ansi.  The problem is that you can't
  # get any other options with it.
  # - output is pointer to files/dirs written.

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
    line = sys.stdin.readline()
    if not line:
      break

    # TODO: If file contains punctuation, escape it to be BOTH shell and HTML
    # safe, and then MOVE It to ~/webpipe/safe-name
    filename = line.strip()

    # NOTE: Right now, this allows absolute paths too.
    input_path = os.path.join(in_dir, filename)

    # TODO: Plugins should be passed directories directly.
    if os.path.isdir(input_path):
      log('Skipping directory %s (for now)', input_path)
      continue

    # TODO: handle errors
    with open(input_path) as f:
      contents = f.read()

    orig_rel_path = '%d/%s' % (counter, filename)
    orig = None  # original contents

    file_type = GuessFileType(filename)
    log('file type: %s', file_type)

    if file_type is None:
      log("Couldn't determine file type for %r; ignored", filename)
      continue

    out_html_filename = '%d.html' % counter
    out_html_path = os.path.join(out_dir, out_html_filename)

    # Order of resolution:
    #
    # 1. Check user's ~/webpipe dir for plugins
    # 2. Check installation dir for plugins distributed with the webpipe
    #    package
    # 3. Builtins

    plugin_bin = res.GetPluginBin(file_type)
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
      exit_code = subprocess.call(argv, cwd=out_dir)
      if exit_code != 0:
        log('ERROR: %s exited with code %d', argv, exit_code)
        with open(out_html_path, 'w') as f:
          # TODO:
          # - make a nicer template.  
          # - show stderr
          f.write('ERROR: %s exited with code %d' % (argv, exit_code))
        counter += 1
        continue

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
      log('No renderer for %r; ignored', filename)
      continue

    counter += 1

  return 0


if __name__ == '__main__':
  try:
    sys.exit(main(sys.argv))
  except KeyboardInterrupt:
    log('Stopped')
    sys.exit(0)
  except Error, e:
    print >> sys.stderr, e.args[0]
    sys.exit(1)
