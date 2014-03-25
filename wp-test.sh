#!/bin/bash
#
# Usage:
#   ./wp-test.sh <function name>

# TODO: make this a proper dep
. ~/hg/taste/taste.sh

wp() {
  ./wp-dev.sh "$@"
}

#
# Tests
#

test-help() {
  wp help | check_grep 'help' -
}

taste-main "$@"
