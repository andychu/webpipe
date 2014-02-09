#!/usr/bin/python
"""
common.py
"""

import sys


def log(msg, *args):
  if args:
    msg = msg % args
  print >>sys.stderr, 'webpipe:', msg


