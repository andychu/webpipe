#!/bin/bash
#
# Usage:
#   ./webpipe-test.sh <function name>

set -o nounset

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

# TODO: fold this into the repo
treemap-demo() {
  local dest=${1:-~/webpipe/input}
  ~/hg/treemap/run.sh find-with-format-string '%s %p\n' . | tee $dest/demo.treemap
}

treemap-plugin() {
  local dest=${1:-~/webpipe/input}
  plugins/treemap/render $dest/demo.treemap 3
}

write-demo() {
  local dest=~/webpipe/input
  set -x

  # TODO: generate png testdata
  touch $dest/Rplot001.png
  sleep 1

  wp show plugins/html/testdata/tiny.html
  sleep 1

  wp show plugins/txt/testdata/tiny.txt
  sleep 1

  wp show plugins/markdown/testdata/tiny.markdown
  sleep 1

  wp show plugins/csv/testdata/tiny.csv
  sleep 1

  # TODO: typescript should be its own file type.  People might want to use a
  # different plugin.  Need aliases.
  wp show plugins/ansi/testdata/typescript
  sleep 1

  wp show testdata/file.unknown
  sleep 1

  wp show plugins/dot/examples/cluster.dot
}

#
# Tests
#

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
  local stub=$PWD/webpipe-stub.sh
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

test-send() {
  ( echo webpipe-stub.sh;
    echo nonexistent ) \
  | ./webpipe-stub.sh send
}

# Since the stub can be copied to many machines, test that it an run with a
# non-bash shell.
test-stub-with-busybox() {
  ( echo webpipe-stub.sh;
    echo nonexistent ) \
  | busybox sh webpipe-stub.sh send
}

test-send-recv() {
  local out=~/webpipe/input/webpipe-stub.sh
  rm $out
  echo webpipe-stub.sh \
    | ./webpipe-stub.sh send \
    | ./wp-dev.sh recv ~/webpipe/input
  ls -al $out
  diff webpipe-stub.sh $out
  echo $?
}

#
# Publishing
#

publish-demo() {
  ./wp-dev.sh publish ~/webpipe/s/2014-03-23/5 dreamhost
}

"$@"
