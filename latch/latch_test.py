#!/usr/bin/python -S
#
# Copyright 2014 Google Inc. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found
# in the LICENSE file or at https://developers.google.com/open-source/licenses/bsd

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
