#!/usr/bin/python -S
"""
webpipe_test.py: Tests for webpipe.py
"""

import os
import Queue
import unittest

import webpipe


class StagesTest(unittest.TestCase):

  def testReadStdin(self):
    q = Queue.Queue()
    r = webpipe.ReadStdin(q)


class FunctionsTest(unittest.TestCase):

  def testSuffixGen(self):
    s = webpipe.SuffixGen()
    suffixes = [s.next() for _ in range(100)]
    print suffixes
    print sorted(suffixes)

  def testMakeSession(self):
    s = webpipe.MakeSession(os.path.expanduser('~/webpipe/s'))
    print s


if __name__ == '__main__':
  unittest.main()
