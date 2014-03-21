#!/usr/bin/python -S
"""
handlers_test.py: Tests for handlers.py
"""

import unittest

import handlers  # module under test


class WaitTest(unittest.TestCase):

  def testSequenceWaiter(self):
    s = handlers.SequenceWaiter()
    result = s.MaybeWait(2)
    self.assertEqual(handlers.WAIT_TOO_BIG, result)

  def testListPlugins(self):
    # This takes the place of the package dir.
    print handlers._ListPlugins('.')


if __name__ == '__main__':
  unittest.main()
