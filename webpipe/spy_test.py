#!/usr/bin/python -S
"""
spy_test.py: Tests for spy.py
"""

import unittest

import spy  # module under test


class FooTest(unittest.TestCase):
  def setUp(self):
    pass

  def tearDown(self):
    pass

  def testFoo(self):
    print 'Hello from spy_test.py'


  def testUsage(self):
    u = spy.UsageReporter(('localhost', 8988))
    u.Send('unit test')
    u.SendDict({'method': 'SendDict'})
    u.SendRecord({'method': 'SendRecord'})

    # TODO:
    # - send function values which raise errors
    # - make sure KeyboardInterrupt isn't swallowed

if __name__ == '__main__':
  unittest.main()
