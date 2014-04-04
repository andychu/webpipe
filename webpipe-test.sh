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

html-demo() {
  cat <<EOF
<p>HTML</p>
<ul>
  <li> <b>Bold</b> </li>
  <li> <i>Italic</i> </li>
  <li> <code>Code</code> </li>
</ul>
EOF
}

txt-demo() {
  cat <<EOF
This a plain text file.  <tags> & stuff aren't special.
Line two.
Line three.
EOF
}

csv-demo() {
  cat <<EOF
name,age
<carol>,10
<dave>,20
EOF
}

#  http://hci.stanford.edu/jheer/workshop/data/
big-csv() {
  ln --verbose --force -s $PWD/testdata/census_marriage.csv ~/webpipe/input
}

dot-demo() {
  local dest=${1:-~/webpipe/input}
  cp plugins/dot/examples/cluster.dot $dest
}

markdown-demo() {
  local dest=${1:-~/webpipe/input}
  cat >$dest/foo.markdown <<EOF
title
=====

This is *markdown* text.

    def foo():
      for i in range(10):
        print i
EOF
}

json-demo() {
  local dest=${1:-~/webpipe/input}
  cat >$dest/foo.json <<EOF
{"a": 1, "b": [1,2,3], "c": {"d": [4,5,6]}}
EOF
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

ansi-demo() {
  local dest=${1:-~/webpipe/input}
  cp testdata/typescript $dest
}

write-demo() {
  local dest=~/webpipe/input
  set -x

  sleep 1
  touch $dest/Rplot001.png

  sleep 1
  html-demo > $dest/test.html
  wp show $dest/test.html

  sleep 1
  txt-demo > $dest/test.txt
  wp show $dest/test.txt

  sleep 1
  csv-demo > $dest/test.csv

  sleep 1
  ansi-demo $dest

  sleep 1
  dot-demo $dest

  sleep 1
  echo 'file with unknown extension' > $dest/other.other
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
