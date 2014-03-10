#!/usr/bin/python
"""
recv.py
"""

import sys

# outside
import tnet


class Error(Exception):
  pass


def main(argv):
  """Returns an exit code."""
  print 'Hello from recv.py'
  while True:
    # must be unbuffered
    try:
      record = tnet.load(sys.stdin)
    except EOFError:
      break

    print repr(record)


if __name__ == '__main__':
  try:
    sys.exit(main(sys.argv))
  except Error, e:
    print >> sys.stderr, e.args[0]
    sys.exit(1)
