"""
util.py
"""

import os
import sys

ANSI_BLUE = '\033[36m'
ANSI_GREEN = '\033[32m'

ANSI_RESET = '\033[0;0m'

class Logger(object):
  def __init__(self, color):
    self.color = color

    basename = os.path.basename(sys.argv[0])
    name, _ = os.path.splitext(basename)

    self.prefix = name + ':'
    if sys.stderr.isatty():
      self.prefix = self.color + self.prefix + ANSI_RESET

  def __call__(self, msg, *args):
    if args:
      msg = msg % args
    print >>sys.stderr, self.prefix, msg
