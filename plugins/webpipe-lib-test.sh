#!/bin/sh
#
# Testing under /bin/sh.
#
# Usage:
#   ./webpipe-lib-test.sh <function name>

. $PWD/webpipe-lib.sh

testBasenameExt() {
  BasenameWithoutExt foo
  BasenameWithoutExt foo.bar
  BasenameWithoutExt /foo
  BasenameWithoutExt /foo.bar
  BasenameWithoutExt ../foo
  BasenameWithoutExt ../foo.bar
  BasenameWithoutExt spam/../foo
  BasenameWithoutExt spam/../foo.bar
}

main() {
  testBasenameExt
}

main "$@"
