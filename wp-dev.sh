#!/bin/bash
#
# Usage:
#   ./webpipe-dev.sh <function name>

# This wrapper just sets PYTHONPATH and then WEBPIPE_DEV, so that webpipe.sh
# won't set PYTHONPATH.

main() {
  local this_dir=$(dirname $0)
  export PYTHONPATH=$this_dir:~/hg/tnet/python:~/hg/json-template/python
  export WEBPIPE_DEV=1
  exec $this_dir/wp.sh "$@"
}

main "$@"

