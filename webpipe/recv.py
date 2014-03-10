#!/usr/bin/python
"""
recv.py
"""

import os
import sys

# outside
import tnet


class Error(Exception):
  pass


def log(msg, *args):
  if args:
    msg = msg % args
  print >>sys.stderr, 'recv: ' + msg


def main(argv):
  """Returns an exit code."""
  print 'Hello from recv.py'
  base_dir = argv[1]
  while True:
    # must be unbuffered
    try:
      record = tnet.load(sys.stdin)
    except ValueError, e:
      log('fatal: %s', e)
      return
    except EOFError:
      break

    try:
      filename = record['filename']
      body = record['body']
    except KeyError, e:
      missing = e.args[0]
      log('Record should have filename and body (missing %s)', missing)
      continue

    # either foo.txt or /full/path/foo.txt accepted, but not
    # rel/path/foo.txt.
    if not os.path.isabs(filename) and '/' in filename:
      log('Relative paths not accepted')
      continue

    path = os.path.join(base_dir, filename)
    with open(path, 'w') as f:
      f.write(body)

    basename = os.path.basename(filename)
    # Now the file is in base_dir, so just print the basename.
    print basename


if __name__ == '__main__':
  try:
    sys.exit(main(sys.argv))
  except Error, e:
    print >> sys.stderr, e.args[0]
    sys.exit(1)
