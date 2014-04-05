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

make-plot-png() {
  local path=plugins/png/testdata/tiny.png
  R --vanilla --slave <<EOF
print('hi')
png('$path')
plot(1:3)
dev.off()
EOF
  ls -l $path
}

make-tar-bz2() {
  tar --verbose --create --bzip --file _tmp/test.tar.bz2 README.md
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
  ln -s -v ansi typescript
  ln -s -v jpeg jpg
  ln -s -v html htm
  ln -s -v markdown md
  popd
}

"$@"
