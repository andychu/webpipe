#!/bin/bash
#
# Scripts to handle plugin dependencies.  This can be done in a more principled
# way later.
#
# Usage:
#   ./deps.sh <function name>

set -o nounset

get-json-tree() {
  local out=_tmp/json-tree
  wget --directory $out https://github.com/lmenezes/json-tree/archive/master.zip
  cd $out
  unzip master.zip
}

install-user() {
  local dest=~/webpipe/plugins/json/static
  mkdir -p $dest
  cp -v _tmp/json-tree/json-tree-master/jsontree.js $dest
  tree $dest
}

"$@"
