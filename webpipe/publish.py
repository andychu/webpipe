#!/usr/bin/python
"""
publish.py

Implement publishing plugins.

"""

import os
import subprocess
import sys

from common import util

class Error(Exception):
  pass


log = util.Logger(util.ANSI_BLUE)


class Publisher(object):
  def __init__(self, user_dir):
    self.package_dir = util.GetPackageDir()
    self.user_dir = user_dir

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

  user_dir = util.GetUserDir()
  pub = Publisher(user_dir)

  # change entry_path to relative URL
  parts = entry_path.split('/')[-3:]  # split off the parts s/2014-03-23/1
  rel_path = '/'.join(parts)

  plugin_path = pub.GetPublisher(dest)
  if not plugin_path:
    raise Error()

  # TODO: 
  # send over preview, dir, and then scan .html in the dir for static resources
  # ../../../plugins/

  # First 
  argv = [plugin_path, user_dir, rel_path + '.html', user_dir, rel_path]
  print argv
  subprocess.call(argv)

  return 0


if __name__ == '__main__':
  try:
    sys.exit(main(sys.argv))
  except Error, e:
    print >> sys.stderr, e.args[0]
    sys.exit(1)
