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

# Found here
# http://www.unix.com/shell-programming-scripting/14108-remove-non-printing-chars.html
remove-nonprintable() {
  tr -c '[:print:]' '_'
}

#
# Tests
#

test-file2html() {
  csv-demo > ~/webpipe/default/table.csv

  # TODO: These files don't exist
  { file2html ~/webpipe/default <<EOF
Rplot001.png
table.csv
EOF
  } | remove-nonprintable
}

test-serve() {
  # TODO: need tnet input
  serve <<EOF
<p>one</p>
<p>two</p>
EOF
}

# not fatal
test-recv-bad-fields() {
  export PYTHONUNBUFFERED=1
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
  local out=~/webpipe/input/$(hostname)_webpipe-stub.sh
  rm $out
  echo webpipe-stub.sh \
    | ./webpipe-stub.sh send \
    | ./webpipe-dev.sh recv ~/webpipe/input
  ls -al $out
  diff webpipe-stub.sh $out
  echo $?
}

"$@"
