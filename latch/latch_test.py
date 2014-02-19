#!/usr/bin/python -S
"""
latch_test.py: Tests for latch.py
"""

import unittest

import latch  # module under test


class LatchTest(unittest.TestCase):
  def setUp(self):
    pass

  def tearDown(self):
    pass

  def testLatch(self):
    la = latch.Latches()
    print 'hi'
    #la.Wait('foo')
    success = la.Notify('foo')
    self.assertEqual(False, success)


if __name__ == '__main__':
  unittest.main()
