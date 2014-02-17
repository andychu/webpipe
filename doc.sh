#!/bin/bash
#
# Usage:
#   ./doc.sh <function name>

# Add the HTML shell.  A data dictionary should be readable stdin.  Does NOT
# depend on $PWD, so callers can cd.

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

  echo "Building $in -> $out"

  local body=_tmp/$in-body.html
  markdown $in >$body

  ls -al $body

  make-dict $body | to-html $out

  ls -al $out
}

main "$@"

#"$@"
