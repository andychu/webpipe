#!/bin/bash
#
# Copyright 2014 Google Inc. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found
# in the LICENSE file or at https://developers.google.com/open-source/licenses/bsd

#
# Usage:
#   ./webpipe-test.sh <function name>

set -o nounset

# TODO: make this a proper dep
. ~/hg/taste/taste.sh

#
# Components
#

# client
wp() {
  ./wp-dev.sh "$@"
}

xrender() {
  ./wp-dev.sh xrender "$@"
}

serve() {
  ./wp-dev.sh serve "$@"
}

#
# Demo files
#

#  http://hci.stanford.edu/jheer/workshop/data/
big-csv() {
  ln --verbose --force -s $PWD/testdata/census_marriage.csv ~/webpipe/input
}

# TODO: need a client to generate this data file.
#
# fs-treemap
treemap-testdata() {
  ~/hg/treemap/run.sh find-with-format-string '%s %p\n' . \
    | tee plugins/treemap/testdata/tiny.treemap
}

zip-testdata() {
  echo foo > _tmp/foo.txt
  zip plugins/zip/testdata/tiny.zip _tmp/foo.txt
}

treemap-plugin() {
  local dest=${1:-~/webpipe/input}
  plugins/treemap/render $dest/demo.treemap 3
}

write-tiny() {
  for p in html txt markdown csv json treemap zip; do
    echo $p
    wp show plugins/$p/testdata/tiny.$p
    sleep 0.5
  done
}

write-demo() {
  local dest=~/webpipe/input
  set -x

  write-tiny

  # TODO: generate png testdata
  touch $dest/Rplot001.png
  sleep 1

  # TODO: typescript should be its own file type.  People might want to use a
  # different plugin.  Need aliases.
  wp show plugins/typescript/testdata/typescript
  sleep 1

  wp show plugins/dot/examples/cluster.dot
  sleep 1

  wp show testdata/file.unknown
  sleep 1
}

#
# Tests
#

test-xrender-badport() {
  xrender -p invalid
  check $? -eq 1
}

test-xrender() {
  xrender ~/webpipe/input ~/webpipe/s/webpipe-test <<EOF
$PWD/plugins/txt/testdata/example.txt
$PWD/plugins/html/testdata/example.html
EOF

  # Make sure a nonexistent file doesn't stop the loop
  xrender ~/webpipe/input ~/webpipe/s/webpipe-test <<EOF
$PWD/plugins/txt/testdata/example.txt
nonexistent
$PWD/plugins/html/testdata/example.html
EOF
}

test-serve() {
  # Test it without a renderer.
  local dev=$PWD/wp-dev.sh
  # TODO: It expects a message with "files" on stdin.  It could just take a
  # line like '1.html'
  local session=~/webpipe/s/webpipe-test
  echo '<i>one</i>' > $session/1.html
  { echo '2:{}'; echo 1.html; } | $dev serve serve $session
}

# not fatal
test-recv-bad-fields() {
  echo -n '0:}8:1:a,1:b,}' | ./wp-dev.sh recv ~/webpipe/input
  echo $?
}

# fatal, because the stream could be messed up
test-recv-bad-message() {
  echo -n 'abc' | ./wp-dev.sh recv ~/webpipe/input
  echo $?
}

test-recv-empty() {
  echo -n '' | ./wp-dev.sh recv ~/webpipe/input
  echo $?
}

# TODO: 'wp-stub send' tests are broken.  Semantics are unclear.

test-send() {
  ( echo wp-stub.sh;
    echo nonexistent ) \
  | ./wp-stub.sh send
}

# Since the stub can be copied to many machines, test that it an run with a
# non-bash shell.
test-stub-with-busybox() {
  ( echo wp-stub.sh;
    echo nonexistent ) \
  | busybox sh wp-stub.sh send
}

test-send-recv() {
  local out=~/webpipe/input/wp-stub.sh
  rm $out
  echo wp-stub.sh \
    | ./wp-stub.sh send \
    | ./wp-dev.sh recv ~/webpipe/input
  ls -al $out
  diff wp-stub.sh $out
  echo $?
}

#
# Publishing
#

publish-demo() {
  ./wp-dev.sh publish ~/webpipe/s/2014-03-23/5 dreamhost
}

"$@"
