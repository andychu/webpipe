#!/bin/bash
#
# Usage:
#   ./doc.sh <function name>

main() {
  local in=$1
  local out=$2

  echo "Building $in -> $out"
  echo '<!-- INSERT LATCH JS -->' >$out
  markdown $in >>$out
  ls -al $out
}

main "$@"
