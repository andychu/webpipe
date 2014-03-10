#!/bin/sh
#
# This is a self-contained shell script that can be copied to a remote machine.
# It has the minimum necessary stuff to interface with a local webpipe server.
# This way you can view remote files without installing stuff.
#
# NOTE: Uses /bin/sh, not /bin/bash.  In theory this could run on BSD, although
# it hasn't been tested at all.
#
# TODO:
#   init: create ~/webpipe/input and fifo?
#   send: send a specific file
#   sendloop: send files from ~/webpipe fifo
#   print-events?  Move it here they have inotify-tools installed
#
# How to get it to the remote machine:
#
#   $ scp $(webpipe stub-path) user@example.org:bin
#
# Usage:
#   ./webpipe-stub.sh <function name>

set -o nounset

log() {
  echo 1>&2 "$@"
}

# very 
send() {
  log 'send'
  while read filename; do
    # is stat on
    stat --printf '%s' $filename
    local exit_code=$?
    if test $exit_code -eq 0; then
      echo
    else
      log "stat error, ignoring $filename"
    fi
  done
}

"$@"
