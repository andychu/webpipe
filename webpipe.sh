#!/bin/bash
#
# User facing executables for webpipe.
#
# Usage:
#   ./webpipe.sh <function name>

set -o nounset
set -o pipefail

# cross platform readlink -f
realpath() {
  local path=$0
  local ostype=${OSTYPE:-}
  # test if ostype begins with "drawin".  ignore stdout of expr.
  if expr $ostype : darwin >/dev/null; then
    python -S -c 'import os,sys; print os.path.realpath(sys.argv[1])' $path
  else
    readlink -f $path
  fi
}

# dereference symlinks in $0
readonly THIS_DIR=$(dirname $(realpath $0))

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

  # close_write: when a file is closed after writing
  # create: creating a symlink (ln -sf of a dir alway does DELETE then CREATE)

  log "webpipe: Watching $input_dir"
  inotifywait --monitor --quiet -e close_write,create $input_dir --format '%f'
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
#
# TODO: should the input dir be a flag?
# Right now people have to do:
#
# $ webpipe run '' --port 8888

run() {
  local input_dir=${1:-~/webpipe/input}
  shift

  check-tools

  export PYTHONUNBUFFERED=1

  print-events $input_dir \
    | file2html $input_dir \
    | serve "$@"
}

help() {
  log "Usage: webpipe [ init | run | help | version ]"
}

recv() {
  export PYTHONUNBUFFERED=1
  $THIS_DIR/webpipe/recv.py "$@"
}

#
# Introspection
#

# So people can do scp $(webpipe stub-path) user@example.org:bin
stub-path() {
  local path=$THIS_DIR/webpipe-stub.sh
  if test -f $path; then
    echo $path
  else
    die "Invalid installation; $path doesn't exist"
  fi
}

version() {
  realpath $0
}


"$@"
