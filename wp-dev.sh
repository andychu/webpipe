#!/bin/bash
#
# Copyright 2014 Google Inc. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found
# in the LICENSE file or at https://developers.google.com/open-source/licenses/bsd

#
# Usage:
#   ./wp-dev.sh <function name>

# This wrapper just sets PYTHONPATH and then WEBPIPE_DEV, so that wp.sh
# won't set PYTHONPATH.

main() {
  local this_dir=$(dirname $(readlink -f $0))
  export PYTHONPATH=$this_dir:~/hg/tnet/python:~/hg/json-template/python
  export WEBPIPE_DEV=1
  exec $this_dir/wp.sh "$@"
}

main "$@"

