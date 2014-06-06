#!/usr/bin/python -S
#
# Copyright 2014 Google Inc. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found
# in the LICENSE file or at https://developers.google.com/open-source/licenses/bsd

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
