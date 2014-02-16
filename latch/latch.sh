#!/bin/bash
#
# file-latch.sh
#
# Usage:
#   ...

set -o nounset

die() {
  echo 1>&2 "$@"
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

# Wait on the first change to a group of files by vim.
#
# NOTE: This has to be a list of files, like *.txt.  Directories would require
# a different %w format.

wait-vim() {
  inotifywait --quiet --format '%w' --event move_self "$@"
}

# NOTE: This does NOT work, because the watch is set on a file, and then it
# BECOMES a different file.  wait-vim in a loop is what we want.

_monitor-vim() {
  inotifywait --monitor --format '%w' --event move_self "$@"
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

"$@"
