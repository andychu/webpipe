#!/bin/sh
#
# Copyright 2014 Google Inc. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found
# in the LICENSE file or at https://developers.google.com/open-source/licenses/bsd

# Testing under /bin/sh.
#
#
# Usage:
#   ./webpipe-lib-test.sh <function name>

. $PWD/webpipe-lib.sh

testBasenameExt() {
  WP_BasenameNoExt foo
  WP_BasenameNoExt foo.bar
  WP_BasenameNoExt /foo
  WP_BasenameNoExt /foo.bar
  WP_BasenameNoExt ../foo
  WP_BasenameNoExt ../foo.bar
  WP_BasenameNoExt spam/../foo
  WP_BasenameNoExt spam/../foo.bar
}

main() {
  testBasenameExt
}

main "$@"
