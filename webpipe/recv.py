#!/usr/bin/python
"""
recv.py

Receive file contents from stdin, write to the base directory, and print
filename on stdout.

A main use case is to emulate the print-events (inotifywait) interface, but
on a remote machine.  webpipe send takes the filename stdin, the file is
transferred from remote to local, and webpipe recv echoes the filename to
stdout.
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

  base_dir = argv[1]

  try:
    header = tnet.load(sys.stdin)
  except ValueError, e:
    log('fatal: %s', e)
    return 1
  except EOFError:
    return 1  # a header is expected

  log('header: %s', header)

  while True:
    # must be unbuffered
    try:
      record = tnet.load(sys.stdin)
    except ValueError, e:
      log('fatal: %s', e)
      return 1
    except EOFError:
      break

    # TODO: instead of a single record, make this pairs of (metadata, data),
    # like DFO.
    try:
      filename = record['filename']
      body = record['body']
    except KeyError, e:
      missing = e.args[0]
      log('Record should have filename and body (missing %s)', missing)
      continue

    # TODO: also receive { dirname tar } messages?  Or { dirname vat } ?

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

  return 0


if __name__ == '__main__':
  try:
    sys.exit(main(sys.argv))
  except Error, e:
    print >> sys.stderr, e.args[0]
    sys.exit(1)
