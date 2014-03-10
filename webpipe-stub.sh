#!/bin/bash
#
# This is a self-contained shell script that can be copied to a remote machine.
# It has the minimum necessary stuff to interface with a local webpipe server.
# This way you can view remote files without installing stuff.
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

send() {
  echo 'Hello from webpipe-stub.sh'
}

"$@"
