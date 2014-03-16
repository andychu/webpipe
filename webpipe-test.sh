#!/bin/bash
#
# Usage:
#   ./webpipe-test.sh <function name>

set -o nounset

file2html() {
  ./webpipe-dev.sh file2html "$@"
}

serve() {
  ./webpipe-dev.sh serve "$@"
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

write-demo() {
  local dest=~/webpipe/input
  set -x

  sleep 1
  touch $dest/Rplot001.png

  sleep 1
  html-demo > $dest/test.html

  sleep 1
  txt-demo > $dest/test.txt

  sleep 1
  csv-demo > $dest/test.csv

  sleep 1
  echo 'file with unknown extension' > $dest/other.other
}

#
# Tests
#

test-file2html() {
  cp testdata/typescript ~/webpipe/input

  # TODO: These files don't exist
  file2html ~/webpipe/input ~/webpipe/s/webpipe-test <<EOF
Rplot001.png
test.csv
typescript
EOF
}

test-serve() {
  # Test it without a renderer.
  local stub=$PWD/webpipe-stub.sh
  local dev=$PWD/webpipe-dev.sh
  cd testdata
  # TODO: It expects a message with "files" on stdin.  It could just take a
  # line like '1.html'
  echo hello.html | $stub send | $dev serve
}

# not fatal
test-recv-bad-fields() {
  echo -n '0:}8:1:a,1:b,}' | ./webpipe-dev.sh recv ~/webpipe/input
  echo $?
}

# fatal, because the stream could be messed up
test-recv-bad-message() {
  echo -n 'abc' | ./webpipe-dev.sh recv ~/webpipe/input
  echo $?
}

test-recv-empty() {
  echo -n '' | ./webpipe-dev.sh recv ~/webpipe/input
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
    | ./webpipe-dev.sh recv ~/webpipe/input
  ls -al $out
  diff webpipe-stub.sh $out
  echo $?
}

"$@"
