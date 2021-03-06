#!/usr/bin/python
#
# Copyright 2014 Google Inc. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found
# in the LICENSE file or at https://developers.google.com/open-source/licenses/bsd

"""
publish.py

Implement publishing plugins.
"""

import os
import re
import subprocess
import sys

from common import util

class Error(Exception):
  pass


log = util.Logger(util.ANSI_BLUE)


# ../../../plugins/ because a scroll is 3 levels up from the root.
DEP_RE = re.compile(r'\.\./\.\./\.\./(plugins/\S+/static)/')

def ScanForStaticDeps(root_dir, rel_path):
  # TODO: Also scan the 1.html entry.

  d = os.path.join(root_dir, rel_path)

  # Some plugins don't even create this dir.
  if not os.path.exists(d):
    return []

  all_deps = []

  for name in os.listdir(d):
    path = os.path.join(d, name)
    if not path.endswith('.html'):
      continue
    log('Scanning %s for dependencies', path)

    # Search in the first 10 KB, since <script> and <link> tags should be in
    # the header.  Note also that there could be multiple deps per line.
    with open(path) as f:
      # open it, 
      head = f.read(10000)
    file_deps = DEP_RE.findall(head)
    log('Found deps %s', file_deps)
    all_deps.extend(file_deps)

  # Make it unique
  return sorted(set(all_deps))


class Publisher(object):

  def __init__(self, package_dir=None, user_dir=None):
    self.package_dir = package_dir or util.GetPackageDir()
    self.user_dir = package_dir or util.GetUserDir()

  def GetPublisher(self, name):
    # plugins dir is parallel to webpipe python dir.
    u = os.path.join(self.user_dir, 'publish', name)
    p = os.path.join(self.package_dir, 'publish', name)

    # TODO: test if it's executable.  Show clear error if not.
    if os.path.exists(u):
      return u
    if os.path.exists(p):
      return p
    log("Couldn't find %s or %s", p, u)
    return None

  def Run(self, plugin_path, rel_path):
    static_deps = ScanForStaticDeps(self.user_dir, rel_path)

    # Now find the root, using the same logic that the server uses (in
    # handlers.py).
    pairs = []
    for dep in static_deps:
      # Resolve it to the right one.  Right now we just test if the 'static'
      # directory exists, not anything inside.
      u = os.path.join(self.user_dir, dep)
      if os.path.exists(u):
        pairs.append(self.user_dir)
        pairs.append(dep)

      p = os.path.join(self.package_dir, dep)
      if os.path.exists(p):
        pairs.append(self.package_dir)
        pairs.append(dep)

    # Send the .html file, and the dir.
    argv = [plugin_path, self.user_dir, rel_path + '.html']

    entry_dir = os.path.join(self.user_dir, rel_path)
    if os.path.exists(entry_dir):
      argv.extend([self.user_dir, rel_path])

    # Now the static deps.
    argv.extend(pairs)

    log('Running %s', argv)
    subprocess.call(argv)


def main(argv):
  """Returns an exit code."""
  # Usage:
  #   publish.py <scroll>/<part> <dest>
  #
  # Could you publish an entire scroll?

  try:
    # can be either absolute or relative to ~/webpipe/s
    entry_path = argv[1]
    # name of a plugin in ~/webpipe/publish or $package_dir/publish
    dest = argv[2]
  except IndexError:
    raise Error("""\
usage: wp publish <entry> <dest>
Example:
  wp publish ~/webpipe/s/2014-01-01/5 myhost
""")


  # change entry_path to relative URL
  parts = entry_path.split('/')[-3:]  # split off the parts s/2014-03-23/1
  rel_path = '/'.join(parts)

  pub = Publisher()

  plugin_path = pub.GetPublisher(dest)
  if not plugin_path:
    raise Error()

  pub.Run(plugin_path, rel_path)
  return 0


if __name__ == '__main__':
  try:
    sys.exit(main(sys.argv))
  except Error, e:
    print >>sys.stderr, e.args[0]
    sys.exit(1)
