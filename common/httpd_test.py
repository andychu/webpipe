#!/usr/bin/python -S
"""
httpd_test.py: Tests for httpd.py
"""

import unittest

import httpd  # module under test


class HandlerTest(unittest.TestCase):
  def setUp(self):
    pass

  def tearDown(self):
    pass

  def testHandler(self):
    # Can't really instantiate this.  req should be a socket?
    return
    req = None
    client_address = None
    server = None
    handler = httpd.BaseRequestHandler(req, client_address, server)
    print handler.translate_path('/')


if __name__ == '__main__':
  unittest.main()
