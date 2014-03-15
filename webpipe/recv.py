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


# Wrapper around tnet.laod
# - string or dict
# - True for error success
# - False for error fail


def GenRecords(f):
  while True:
    try:
      v = tnet.load(f)
      if not isinstance(v, (str, dict)):  # byte string or dict
        log('Invalid value %r', v)
        yield False
      yield v
    except ValueError, e:
      log('fatal: %s', e)
      yield False  # fatal error
    except EOFError:
      yield True  # end of stream, success


def main(argv):
  """Returns an exit code."""

  base_dir = argv[1]

  g = GenRecords(sys.stdin)

  try:
    header = g.next()
  except StopIteration:
    log('Expected header')
    return 0

  if isinstance(header, bool):
    return 0 if header else 1

  if not isinstance(header, dict):
    log('Invalid header: %r', header)
    return 1

  # For now, don't do anything with it.
  log('header: %s', header)

  while True:

    #
    # Get metadata
    #

    try:
      metadata = g.next()
    except StopIteration:
      return 0

    if isinstance(metadata, bool):
      return 0 if metadata else 1

    if not isinstance(metadata, dict):
      log('Invalid metadata: %r', metadata)
      return 1

    try:
      filename = metadata['filename']
    except KeyError, e:
      log('Record should have filename')
      return 1
    hostname = metadata.get('hostname')
    filetype = metadata.get('filetype')

    #
    # Get body
    #

    try:
      body = g.next()
    except StopIteration:
      log('Expected body record')
      return 1

    if isinstance(body, bool):
      return 0 if body else 1

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


if __name__ == '__main__':
  try:
    sys.exit(main(sys.argv))
  except Error, e:
    print >> sys.stderr, e.args[0]
    sys.exit(1)
