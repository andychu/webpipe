#!/usr/bin/python -S
"""
wait_server_test.py: Tests for wait_server.py
"""

import unittest

import wait_server  # module under test


class WaitTest(unittest.TestCase):

  def setUp(self):
    pass

  def tearDown(self):
    pass

  def testSequenceWaiter(self):
    s = wait_server.SequenceWaiter()
    result = s.MaybeWait(1)
    self.assertEqual(wait_server.WAIT_TOO_BIG, result)


if __name__ == '__main__':
  unittest.main()
