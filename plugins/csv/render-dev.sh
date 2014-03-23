#!/bin/bash
#
# Development stub.  For now, when deployed, the plugin can import jsontemplate
# because PYTHONPATH leaks from xrender.py to its child processes.  May want to
# change that at some point, i.e. create a $WEBPIPE_LIB_DIR variable or
# something.
#
# Usage:
#   ./render-dev.sh <function name>

export PYTHONPATH=~/hg/json-template/python

exec $(dirname $0)/render.py "$@"
