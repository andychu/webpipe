#!/usr/bin/python
"""
publish.py

Implement publishing plugins.

"""

import os
import subprocess
import sys


class Error(Exception):
  pass


def main(argv):
  """Returns an exit code."""
  # Usage:
  #   publish.py <scroll>/<part> <dest>
  #
  # could you publish an entire scroll?
  # 

  # can be either absolute or relative to ~/webpipe/s
  entry_path = argv[1]
  # name of a plugin in ~/webpipe/publish or $package_dir/publish
  dest = argv[2]

  # TODO: Share Resources class in xrender.py

  user_dir = os.path.expanduser('~/webpipe')
  plugin_path = os.path.join(user_dir, 'publish', dest)

  argv = [plugin_path, entry_path]
  print argv
  subprocess.call(argv)

  return 0


if __name__ == '__main__':
  try:
    sys.exit(main(sys.argv))
  except Error, e:
    print >> sys.stderr, e.args[0]
    sys.exit(1)
