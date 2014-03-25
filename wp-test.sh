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
  # No actions is help too
  wp | check_grep 'help' -
  wp help | check_grep 'help' -
  wp --help | check_grep 'help' -
}

test-invalid-action() {
  wp zzz
  check $? -eq 1
}

taste-main "$@"
