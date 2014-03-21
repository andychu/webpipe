#!/usr/bin/python -S
"""
serve_test.py: Tests for serve.py
"""

import os
import Queue
import unittest

import serve


class StagesTest(unittest.TestCase):

  def testReadStdin(self):
    q = Queue.Queue()
    r = serve.ReadStdin(q)


class FunctionsTest(unittest.TestCase):

  def testSuffixGen(self):
    s = serve.SuffixGen()
    suffixes = [s.next() for _ in range(100)]
    print suffixes
    print sorted(suffixes)

  def testMakeSession(self):
    s = serve.MakeSession(os.path.expanduser('~/serve/s'))
    print s


if __name__ == '__main__':
  unittest.main()
