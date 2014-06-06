#!/usr/bin/python -S
#
# Copyright 2014 Google Inc. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found
# in the LICENSE file or at https://developers.google.com/open-source/licenses/bsd

"""
xrender_test.py: Tests for xrender.py
"""

import unittest

import xrender  # module under test

CSV = """\
name,age
<carol>,10
<dave>,20
"""

class FunctionsTest(unittest.TestCase):

  def testGetFileType(self):
    self.assertEqual('png', xrender.GetFileType('Rplot001.png'))
    self.assertEqual('Rplot.png', xrender.GetFileType('001.Rplot.png'))

    self.assertEqual('tar.gz', xrender.GetFileType('foo.tar.gz'))

    self.assertEqual('typescript', xrender.GetFileType('mysession.typescript'))
    self.assertEqual('typescript', xrender.GetFileType('typescript'))
    self.assertEqual('typescript', xrender.GetFileType('/tmp/typescript'))

  def testCleanFilename(self):
    print xrender.CleanFilename('foo-bar_baz')
    print xrender.CleanFilename('foo bar')
    print xrender.CleanFilename('foo bar <>&')
    print xrender.CleanFilename('foo bar \\ @ ')


class ResourcesTest(unittest.TestCase):

  def testResources(self):
    res = xrender.Resources()

    p = res.GetPluginBin('ansi')
    print p

    p = res.GetPluginBin('unknown')
    print p


def Echo():
  while True:
    filename = yield
    if not filename:
      break
    print filename


class TcpServerTest(unittest.TestCase):

  def testServer(self):
    e = Echo()
    # This is a 'manual' test; it listens.
    return
    xrender.TcpServer(8002, e)


if __name__ == '__main__':
  unittest.main()
