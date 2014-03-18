#!/bin/sh
#
# Testing under /bin/sh.
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
