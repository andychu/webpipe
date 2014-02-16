#!/bin/bash
#
# Usage:
#   ./run.sh <function name>
#
# TODO: Separate out user facing parts?

# webpipe serve?
# webpipe copy?


# two scripts use TNET.
export PYTHONPATH=~/hg/tnet/python:~/hg/json-template/python

log() {
  echo 1>&2 "$@"
}

unit() {
  "$@"
}

#
# Combinations
#

serve-rendered() {
  local outdir=remote-out
  # Crap, I think I need this.
  export PYTHONUNBUFFERED=1
  ./webpipe.py serve-rendered --out-dir=$outdir "$@"
}


# watch a directory, and print HTML snippets on stdout
print-parts() {
  export PYTHONUNBUFFERED=1
  local dir=${1:-~/webpipe/default}
  print-events $dir | file2html $dir
}

test-file2html() {
  csv-demo > ~/webpipe/default/table.csv

  { ./file2html.py ~/webpipe/default <<EOF
Rplot001.png
table.csv
EOF
  } | remove-nonprintable
}

# Found here
# http://www.unix.com/shell-programming-scripting/14108-remove-non-printing-chars.html
remove-nonprintable() {
  tr -c '[:print:]' '_'
}

test-server() {
  ./webpipe.py <<EOF
<p>one</p>
<p>two</p>
EOF
}

usage-sink() {
  # listen in UDP mode on port 8988
  log 'usage sink'
  nc -v -u -l localhost 8988
}

usage-send() {
  echo foo | nc -u localhost 8988
}

usage-config() {
  echo localhost:8988 > usage-address.txt
}


#
# Demo
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
  local dest=~/webpipe/default
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
# Latch
#


# for doc.sh, use Makefile perhaps?

latch-demo() {
  latch/latch.sh rebuild ./doc.sh README
}


"$@"
