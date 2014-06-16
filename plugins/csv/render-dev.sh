#!/bin/bash
#
# Copyright 2014 Google Inc. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found
# in the LICENSE file or at https://developers.google.com/open-source/licenses/bsd

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
