#!/usr/bin/python -S
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

  def testGuessFileType(self):
    self.assertEqual('png', xrender.GuessFileType('Rplot001.png'))
    self.assertEqual('ansi', xrender.GuessFileType('typescript'))

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


if __name__ == '__main__':
  unittest.main()
