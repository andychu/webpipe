#!/usr/bin/python -S
#
# Copyright 2014 Google Inc. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found
# in the LICENSE file or at https://developers.google.com/open-source/licenses/bsd

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
    u.SendRecord('start', {'method': 'SendRecord'})

    # TODO:
    # - send function values which raise errors
    # - make sure KeyboardInterrupt isn't swallowed

if __name__ == '__main__':
  unittest.main()
