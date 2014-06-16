#!/bin/bash
#
# Copyright 2014 Google Inc. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found
# in the LICENSE file or at https://developers.google.com/open-source/licenses/bsd

#
# Usage:
#   ./wp-test.sh <function name>

set -o nounset

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
