#!/bin/bash
#
# Misc scripts.
#
# Usage:
#   ./run.sh <function name>

set -o nounset

log() {
  echo 1>&2 "$@"
}

unit() {
  "$@"
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
# Manually demo plugins
#

ansi() {
  plugins/bin/ansi typescript ~/webpipe/input/ansi.html
  sleep 1
  plugins/bin/ansi diff.ansi ~/webpipe/input/diff.html
}


#
# Latch
#

# for doc.sh, use Makefile perhaps?

latch-demo() {
  ./latch.sh rebuild ./doc.sh README.md doc/*.md
}

"$@"
