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

# Build main docs
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

# Generate a named snippet for each plugin type.  Then join them into an HTML
# doc.
gallery() {
  local base=$PWD/_tmp/gallery  # absolute path
  rm -rf $base/out  # so it's numbered from 1
  mkdir -p $base/in $base/out

  for p in txt html; do
    local plugin=$PWD/plugins/$p/render 
    local in=$PWD/plugins/$p/testdata/tiny.$p
    # NOTE: we are not providing a number
    local out=$base/out/$p

    # plugins are written to be in the output dir.
    pushd $base/out
    $plugin $in $out
    popd
  done

  ls -al $base/out
}

"$@"
