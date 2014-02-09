#!/bin/bash
#
# User facing executables for webpipe.
#
# Usage:
#   ./webpipe.sh <function name>

set -o nounset
set -o pipefail

readonly THIS_DIR=$(dirname $(readlink -f $0))

log() {
  echo 1>&2 "$@"
}

die() {
  log "$@"
  exit 1
}

readonly INPUT_DIR=~/webpipe/input


check-tools() {
  local err="inotifywait not found.  Run 'sudo apt-get install inotify-tools'"
  which inotifywait || die "$err"
}

print-events() {
  local input_dir=${1:-~/webpipe/input}

  # --quiet: only print events
  # --monitor: loop forever

  # The filename is third token.  The fflush fixes buffering issues in awk
  # (like PYTHONUNBUFFERED does for Python).

  inotifywait --monitor --quiet -e close_write $input_dir | awk '{print $3; fflush()}'
  log "Watching $input_dir"
}

webpipe-main() {
  ./webpipe.py "$@"
}


#
# Public functions
#

# Set up the default dir to watch.
init() {
  mkdir --verbose -p $INPUT_DIR
}

# TODO: package these together.  Or make a dev version.
export PYTHONPATH=~/hg/tnet/python:~/hg/json-template/python

# People can run this directly to render on a different host.
file2html() {
  local dir=$1
  $THIS_DIR/file2html.py $dir
}

serve() {
  local input_dir=${1:-~/webpipe/input}
  shift

  check-tools

  export PYTHONUNBUFFERED=1

  print-events $input_dir \
    | file2html $input_dir \
    | $THIS_DIR/webpipe.py serve "$@"
}


"$@"
