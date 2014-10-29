#!/bin/bash
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

# Wait on the first change to a group of files by vim.
#
# NOTE: This has to be a list of files, like *.txt.  Directories would require
# a different %w format.

wait-vim() {
  log "Watching $@"
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
  shift
  log "build_cmd $build_cmd"

  check-tools

  while true; do
    # Wait for a changed file
    local changed=$(wait-vim "$@")
    log "changed $changed"

    # We need to know the output name here relative to _tmp to notify the
    # server.
    local rel_output="doc/$(basename $changed .md).html"

    local output="_tmp/$rel_output"

    # Rebuild
    $build_cmd $changed $output

    log "notify $rel_output"

    # Release latch so that the page is refreshed.
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
  export PYTHONPATH=$THIS_DIR:~/hg/json-template/python
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
