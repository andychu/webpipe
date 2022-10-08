#!/bin/bash
#
# Copyright 2014 Google Inc. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found
# in the LICENSE file or at https://developers.google.com/open-source/licenses/bsd

#
# latch.sh
#
# Usage:
#   ./latch.sh <function>
#
# To reload edit docs quickly, do:
#
#   ./latch.sh rebuild <command> <files>...
#
# This rebuilds files in a loop.
#
# Then.
#
#   ./latch.sh serve
#
# TODO: There should be a 'latch run' command that does 'watch and 'serve'
# together.  This is like 'webpipe run'.


set -o nounset

readonly THIS_DIR=$(dirname $(readlink -f $0))

log() {
  echo 1>&2 "$@"
}

die() {
  log "$@"
  exit 1
}


# NOTE: inotifywait is very fiddly.
# - --monitor doesn't work here because vim creates new files, with new inodes,
# and inotifywait is stuck on the old ones
# - -e modify/close_write foo.txt bar.txt doesn't seem to print the filename?
# odd.
# - -e move_self foo.txt bar.txt seems to work, but that could be vim specific?

# Protocol we want: just print out the filename (which is the same as the latch
# name).  This unfortunately seems to require editor-specific info.

print-files() {
  set -x
  #inotifywait --monitor --event close_write "$@"
  inotifywait --monitor --event modify "$@"
  #inotifywait --monitor --quiet --event close_write "$@"
}

check-tools() {
  which inotifywait >/dev/null \
    || die "inotifywait must be installed (sudo apt-get install inotify-tools)."

  which which >/dev/null \
    || die "curl must be installed (sudo apt-get install curl)."
}

wait-vscodium() {
  log "wait-vscodium: Watching $@"
  inotifywait --quiet --format '%w' --event modify "$@"
}

# Wait on the first change to a group of files by vim.
#
# NOTE: This has to be a list of files, like *.txt.  Directories would require
# a different %w format.

wait-vim() {
  log "wait-vim: Watching $@"
  inotifywait --quiet --format '%w' --event move_self "$@"
}

# NOTE: This does NOT work, because the watch is set on a file, and then it
# BECOMES a different file.  wait-vim in a loop is what we want.

_monitor-vim() {
  inotifywait --monitor --format '%w' --event move_self "$@"
}

# Rebuild in a loop.
#
# Should there be another loop to watch _tmp and notify the latch?  Or can it
# be the same loop?
#
# some files are for rebuilding, some are for serving?

# if there is no build process, then just use "true" ?  or maybe cp?


readonly LATCH_HOST=localhost:8990

# Usage:
# ./latch.sh rebuild <build cmd> <files to watch>...

rebuild() {
  local build_cmd=$1
  local wait_cmd=${2:-wait-vim}
  shift 2

  log "build_cmd: $build_cmd"

  check-tools

  while true; do
    # Wait for a changed file
    local changed=$($wait_cmd "$@")
    log "changed file: $changed"

    # We need to know the output name here relative to _tmp to notify the
    # server.
    local rel_output="$(dirname $changed)/$(basename $changed .md).html"
    # Hacky normalization to remove /./ , since that isn't valid in a URL
    rel_output=$(echo $rel_output | sed 's|/./|/|g')
    log "rel_output: $rel_output"

    # TODO: Don't hard-code _site!
    local output="_site/$rel_output"

    # HACK to sleep 100ms before building.  Otherwise we get:
    #
    # Couldn't watch doc/tutorial.md: No such file or directory
    # changed 
    # ./build.sh: line 68: doc/tutorial.md: No such file or directory
    #
    # What is happening is that:
    # - we get notification of a changed inode
    # - but vim hasn't actually saved the new file yet
    # - we can't build without the new file
    # - TODO: should we listen for another event in wait-vim?  move_self vs
    # modify?

    sleep 0.1

    # Rebuild
    $build_cmd $changed $output

    log "notify $rel_output"

    # Release latch so that the page is refreshed.
    notify $rel_output
  done
}

# For Oil posts with presenter notes
one-rebuild-loop() {
  local in=$1
  local rel_output=$2  # URL
  local build_cmd=$3

  while true; do
    wait-vim $in

    $build_cmd
    notify $rel_output
  done
}

watch() {
  which inotifywait \
    || die "inotifywait must be installed (sudo apt-get install inotifytools)."

  local tool=$1
  shift

  while true; do
    echo Watching "$@"
    local exit_code=$?
    if test $? -ne 0; then
      die "inotifywait failed with code $exit_code"
    fi

    # Add latch automatically.
    #PULP_latch=1 poly build .

    #curl -d X http://localhost:1212/HOST/latch/default
    echo
  done
}

serve() {
  export PYTHONPATH=$THIS_DIR:~/git/json-template/python
  $THIS_DIR/latch/latch.py "$@"
}

notify() {
  local name=$1
  curl --request POST http://$LATCH_HOST/-/latch/$name
}

help() {
  cat $THIS_DIR/doc/latch-help.txt
}

if test $# -eq 0; then
  help
  exit 0
fi

"$@"
