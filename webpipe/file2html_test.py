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

class FooTest(unittest.TestCase):
  def setUp(self):
    pass

  def tearDown(self):
    pass

  def testRenderCsv(self):
    print file2html.RenderCsv('dir/foo.csv', 'foo.csv', CSV)


if __name__ == '__main__':
  unittest.main()
