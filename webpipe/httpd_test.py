#!/usr/bin/python -S
"""
httpd_test.py: Tests for httpd.py
"""

import unittest

import httpd  # module under test


class FooTest(unittest.TestCase):
  def setUp(self):
    pass

  def tearDown(self):
    pass

  def testFoo(self):
    print 'Hello from httpd_test.py'


if __name__ == '__main__':
  unittest.main()
