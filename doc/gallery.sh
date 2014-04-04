#!/bin/bash
#
# Usage:
#   ./gallery.sh <function name>

# Generate an HTML page which shows all the plugins.

# TODO:
# Use plugins/*/testdata.
#   Run ./webpipe-test.sh, but pipe it through xrender.
# But weave them into static .html file.
# It needs a title + anchors I guess.
# use snip.
#

# Run this from root dir
xrender() {
  ./wp-dev.sh xrender "$@"
}

gen() {
  local base=_tmp/gallery
  rm -rf $base/out  # so it's numbered from 1
  mkdir -p $base/in $base/out

  xrender . $base/out <<EOF
$PWD/plugins/txt/testdata/tiny.txt
$PWD/plugins/html/testdata/tiny.html
EOF
  ls -al $base/out
}

"$@"
