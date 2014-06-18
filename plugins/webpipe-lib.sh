# Copyright 2014 Google Inc. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found
# in the LICENSE file or at https://developers.google.com/open-source/licenses/bsd

# webpipe-lib.sh
#
# Not executable, but should be sourceable by /bin/sh.

# every script needs this
set -o nounset

# stdout is important, so provide something to log to stderr.
log() {
  echo 1>&2 "$@"
}

# failure to create tools
die() {
  log "$@"
  exit 1
}

# Extract base filename, without extension.  Useful determining the output path
# of converters.
#
# GNU basename doesn't seem to let you remove an arbitrary extension.
WP_BasenameNoExt() {
  local path=$1
  python -S -c '
import os, sys
filename = os.path.basename(sys.argv[1])  # spam/eggs.c -> eggs.c
base, _ = os.path.splitext(filename)      # eggs.c -> eggs
print base' \
  $path
}

# Takes raw text on stdin, and outputs HTML safe text on stdout.  We always
# escape & < > and ".  (Don't use single quotes for attributes!)

# NOTE: sed probably makes multiple passes to do this, but so does Python's
# cgi.escape.
WP_HtmlEscape() {
  sed 's|&|\&amp;|g; s|<|\&lt;|g; s|>|\&gt;|g; s|"|\&quot;|g'
}

