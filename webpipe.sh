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
  export PYTHONPATH=$THIS_DIR
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

#
# Public functions
#

# Set up the default dir to watch.
init() {
  mkdir --verbose -p $INPUT_DIR
}

# People can run print-events | file2html to directly to render on a different
# host.  For now we keep them separate, so we have an explicit and flexible
# pipeline.

print-events() {
  local input_dir=${1:-~/webpipe/input}

  # --quiet: only print events
  # --monitor: loop forever
  # --format %f: print out the filename in the directory we're watching

  log "webpipe: Watching $input_dir"
  inotifywait --monitor --quiet -e close_write $input_dir --format '%f'
}

# render files to HTML.
file2html() {
  local dir=$1
  $THIS_DIR/webpipe/file2html.py $dir
}

# serve HTML and static files.
serve() {
  $THIS_DIR/webpipe/webpipe.py serve "$@"
}

# Run the whole pipeline.
run() {
  local input_dir=${1:-~/webpipe/input}
  shift

  check-tools

  export PYTHONUNBUFFERED=1

  print-events $input_dir \
    | file2html $input_dir \
    | serve
}

help() {
  log "Usage: webpipe [ init | run | help | version ]"
}

version() {
  readlink -f $0
}


"$@"
