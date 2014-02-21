#!/bin/bash
#
# Usage:
#   ./doc.sh <function name>

# Add the HTML shell.  A data dictionary should be readable stdin.  Does NOT
# depend on $PWD, so callers can cd.

set -o nounset
set -o errexit

to-html() {
  local out=$1
  jsont doc/html.jsont > $out
}

make-dict() {
  local body_filename=$1
  pin --title-tag=h1 $body_filename
}

main() {
  local in=$1
  local out=$2

  local base_in=$(basename $in)  # For now, get rid of subdirs
  local body=_tmp/$base_in-body.html

  echo "Building $in -> $body -> $out"

  markdown $in >$body

  ls -al $body

  make-dict $body | to-html $out

  ls -al $out
}

main "$@"

#"$@"
