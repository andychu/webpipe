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
