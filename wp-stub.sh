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

# minimal custom TNET encoder.  Avoid dependencies on Python, C, etc.
tnetEncodeFile() {
  local path="$1"
  local hostname="$2"
  local size="$3"

  # only send filename, not full path.  Later we could send it as a "comment".
  local filename=$(basename $path)

  # { file: example.txt, body: foobar }

  local k1='8:filename,'
  # $#s gets the length of s; should be portable
  local v1="${#filename}:${filename},"

  local meta="$k1$v1"
  echo -n "${#meta}:$meta}"

  echo -n "$size:"
  cat $path
  echo -n ,
}

sendHeader() {
  # Send empty dictionary for now.  Send other stream options here in the
  # future.
  echo -n '0:}'
}

# TODO:
# - send filename, optional hostname, optional file type as fields
# - send body as separate message

send() {
  local base_dir=$1  # base dir for relative filenames
  cd $base_dir
  log "send: changed working directory to $base_dir"

  # Add hostname prefix to every filename.
  # TODO: make this a tag instead in the metadata message?
  local hostname
  hostname=$(hostname)  # could be empty if this fails

  sendHeader

  while read path; do
    local size
    size=$(stat --printf '%s' $path)  # stat should be portable?
    local exit_code=$?
    if test $exit_code -eq 0; then
      tnetEncodeFile "$path" "$hostname" "$size"
    else
      log "stat error, ignoring $path"
    fi
  done
}

# TODO: This should be:
# $ ls | wps sink
# $ wps show foo.txt

sendfile() {
  local path=$1
  local size=$(stat --printf '%s' $path)  # stat should be portable?
  local hostname=$(hostname)
  filename=$
  tnetEncodeFile "$path" "$hostname" "$size"
}

# Example:
#   ls | wp sink         # txt file
#   ps aux | wp sink ps  # file type

sink() {
  local ext=${1:-txt}
  local basename=$$  # use PID for now.
  cat > ~/webpipe/input/$basename.$ext
  # TODO: later, write filename FIFO ~/webpipe/input.
  # That can go in ~/webpipe/sink or something.
  # This is better because file system events are unreliable.  > in bash seems
  # to generate both close and close_write events.
}

"$@"
