#!/usr/bin/python -S
"""
file2html_test.py: Tests for file2html.py
"""

import unittest

import file2html  # module under test

CSV = """\
name,age
<carol>,10
<dave>,20
"""

class FunctionsTest(unittest.TestCase):

  def testRenderCsv(self):
    html, orig = file2html.RenderCsv('dir/foo.csv', 'foo.csv', CSV)
    print html

  def testGuessFileType(self):
    self.assertEqual('png', file2html.GuessFileType('Rplot001.png'))
    self.assertEqual('ansi', file2html.GuessFileType('typescript'))


class ResourcesTest(unittest.TestCase):

  def testResources(self):
    res = file2html.Resources()
    s = res.ReadFile('index.html')
    print 'index', len(s)

    p = res.GetPluginBin('ansi')
    print p

    p = res.GetPluginBin('unknown')
    print p


if __name__ == '__main__':
  unittest.main()
