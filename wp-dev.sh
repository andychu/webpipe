#!/bin/bash
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

