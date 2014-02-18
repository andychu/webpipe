"""
util.py
"""

import os
import sys

basename = os.path.basename(sys.argv[0])
prefix, _ = os.path.splitext(basename)

def log(msg, *args):
  if args:
    msg = msg % args
  print >>sys.stderr, prefix + ': ' + msg

