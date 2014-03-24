#!/usr/bin/python
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
  d = os.path.join(root_dir, rel_path)

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
    p = os.path.join(self.package_dir, 'publish', name)
    u = os.path.join(self.user_dir, 'publish', name)

    # TODO: test if it's executable.  Show clear error if not.
    if os.path.exists(p):
      return p
    if os.path.exists(u):
      return u
    log("Couldn't find %s or %s", p, u)
    return None

  def Run(self, plugin_path, rel_path):
    # TODO: this finds relative paths.  We have to resolve them to p or u.
    deps = ScanForStaticDeps(self.user_dir, rel_path)

    # First 
    argv = [plugin_path, self.user_dir, rel_path + '.html', self.user_dir, rel_path]
    argv.extend(deps)
    log('Running %s', argv)
    subprocess.call(argv)


def main(argv):
  """Returns an exit code."""
  # Usage:
  #   publish.py <scroll>/<part> <dest>
  #
  # Could you publish an entire scroll?

  # can be either absolute or relative to ~/webpipe/s
  entry_path = argv[1]
  # name of a plugin in ~/webpipe/publish or $package_dir/publish
  dest = argv[2]

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
    print >> sys.stderr, e.args[0]
    sys.exit(1)
