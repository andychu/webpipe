#!/bin/bash
#
# User facing executables for webpipe.
#
# Usage:
#   ./webpipe.sh <function name>

set -o nounset
set -o pipefail

# dereference symlinks in $0
readonly THIS_DIR=$(dirname $(readlink -f $0))

webpipe_dev=${WEBPIPE_DEV:-}
if test -z "$webpipe_dev"; then
  export PYTHONPATH=$THIS_DIR/..
fi

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
  which inotifywait >/dev/null || die "$err"
}

print-events() {
  local input_dir=${1:-~/webpipe/input}

  # --quiet: only print events
  # --monitor: loop forever

  # The filename is third token.  The fflush fixes buffering issues in awk
  # (like PYTHONUNBUFFERED does for Python).

  log "webpipe: Watching $input_dir"
  inotifywait --monitor --quiet -e close_write $input_dir \
    | awk '{print $3; fflush()}'
}

#
# Public functions
#

# Set up the default dir to watch.
init() {
  mkdir --verbose -p $INPUT_DIR
}

# People can run this directly to render on a different host.
file2html() {
  local dir=$1
  $THIS_DIR/file2html.py $dir
}

# Run the whole pipeline.
run() {
  local input_dir=${1:-~/webpipe/input}
  shift

  check-tools

  export PYTHONUNBUFFERED=1

  print-events $input_dir \
    | file2html $input_dir \
    | $THIS_DIR/webpipe.py serve "$@"
}

"$@"
