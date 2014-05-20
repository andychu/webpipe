#!/bin/bash
#
# This is an idea to get live visualizations in the browser.
#
# You have a tiny shell/Python program which writes to stdout.  It gets piped
# to netcat, through ssh tunnel, and then to the webpipe server.
#
# Is netcat reliable?  Yeah it seems to work better for this "stream" use case.
# Still use it as a client only though.
#
# PLUGIN INTERFACE
#
# The plugins need to send the initial HTML and JS as they always do.
# (NOTE: right now the server directly reads the JS; it isn't sent)
#
# NOTE: This isn't possible for static publishing... only live a live server.
# (although a crazy idea is if you load a JS file that replays it somehow)
#
# webpipe server should listen on an auxiliary port perhaps.
# And then every live plugin will make a new connection on that port, send its
# ID?  
#
# And then the server has to deliver those to different JS clients.
# It probably needs some kind of ID.
#
# NOTE: This should possibly be a different server than webpipe.  The model is
# different; it's not compatible with static web hosting.
#
# And you probably don't want a "scroll".  You probably want a page of live
#
# And you need a different protocol than just a hanging get.  Although I guess
# you can dispatch by URL.  Every plugin can send the URL it wants?
#
# 8901 - jspipe?  This name is too common.  livepipe?
#
# Usage:
#   ./demo.sh <function name>

set -o nounset
set -o pipefail
# set -o errexit  # most scripts should set this

cpu() {
  while true; do
    head -n1 /proc/stat
    sleep 1
  done
}

"$@"
