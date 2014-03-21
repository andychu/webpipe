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
  # test if ostype begins with "darwin".  ignore stdout of expr.
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
  # Where user can install their own plugins
  mkdir --verbose -p ~/webpipe/plugins
  # Where files from $INPUT_DIR are moved and renamed to, so they are HTML and
  # shell safe.
  mkdir --verbose -p ~/webpipe/renamed
}

# People can run print-events | file2html to directly to render on a different
# host.  For now we keep them separate, so we have an explicit and flexible
# pipeline.

print-events() {
  local input_dir=${1:-$INPUT_DIR}

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
  $THIS_DIR/webpipe/file2html.py "$@"
}

# serve HTML and static files.
server() {
  $THIS_DIR/webpipe/webpipe.py "$@"
}

# Run the whole pipeline.
#
# TODO: should the input dir be a flag?
# Right now people have to do:
#
# $ webpipe run '' --port 8888

run() {
  local input_dir=${1:-$INPUT_DIR}
  shift

  check-tools

  export PYTHONUNBUFFERED=1

  # TODO: determine session here.  Latest dir in ~/webpipe/s/ or
  # ~/webpipe/session.
  print-events $input_dir \
    | file2html $input_dir \
    | server serve "$@"
}

# TODO:
# - file2html can read from a named pipe ~/webpipe/input
# - webpipe.R can write to the fifo directly.  It knows what filename it is
# going to write.
# - You can have a ~/webpipe/watched dir for inotifywait if you really need it.
# However, inotifywait seems more useful for "latch".

run2() {
  local input_dir=${1:-$INPUT_DIR}
  shift

  check-tools

  export PYTHONUNBUFFERED=1

  # NOTE: Could recover state here too.
  # file2html has to know what filenames to write/generate.  Serve has to know
  # which one to block on.  Or I guess serve could recover it too by looking at
  # the file system.  But there is a race condition there.  Because

  #local session=~/webpipe/s/webpipe-test
  local session=~/webpipe/s/$(date +%Y-%m-%d)
  log "session $session"
  # Right now, it has to exist.  I guess the shell wrappers should be
  # responsible for making it.
  mkdir -p $session
  print-events $input_dir \
    | file2html $input_dir $session \
    | server serve2 $session
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
