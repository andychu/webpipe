#!/bin/bash
#
# Misc scripts.
#
# Usage:
#   ./run.sh <function name>

set -o nounset

log() {
  echo 1>&2 "$@"
}

unit() {
  local this_dir=$(dirname $0)
  export PYTHONPATH=$this_dir:~/hg/tnet/python:~/hg/json-template/python
  "$@"
}

usage-sink() {
  # listen in UDP mode on port 8988
  log 'usage sink'
  nc -v -u -l localhost 8988
}

usage-send() {
  echo foo | nc -u localhost 8988
}

usage-config() {
  local addr='localhost:19999'
  echo $addr > webpipe/usage-address.txt
  echo $addr > latch/usage-address.txt
}

#
# Gen testdata
#

make-Rplot-testdata() {
  local dir=plugins/Rplot.png/testdata
  mkdir -p $dir
  local path=$dir/tiny.Rplot.png

  R --vanilla --slave <<EOF
png('$path')
plot(1:3)
dev.off()
EOF
  ls -l $path
}


make-tar-file() {
  local ext=$1
  local flag=$2
  local out_dir=plugins/tar.$ext/testdata
  mkdir -p $out_dir
  tar --verbose --create $flag --file $out_dir/tiny.tar.$ext README.md
}

make-tar-testdata() {
  make-tar-file gz --gzip
  make-tar-file bz2 --bzip2
  make-tar-file xz --xz
}

#
# Latch
#

# for doc.sh, use Makefile perhaps?

latch-demo() {
  ./latch.sh rebuild './doc.sh main' README.md doc/*.md
}

#
# Aliases
#

make-alias() {
  pushd plugins
  # assume terminal is ansi
  ln -s -v -T ansi typescript
  ln -s -v -T jpeg jpg
  ln -s -v -T html htm
  ln -s -v -T markdown md

  # TODO: make your own png plugin, should show metadata, etc.
  # "file" shows dimensions, colormap, etc. of png
  ln -s -v -T Rplot.png png

  # For now, jpeg does what png does.
  ln -s -v -T png jpeg
  ln -s -v -T png gif

  popd
}

"$@"
