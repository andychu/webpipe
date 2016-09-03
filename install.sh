#!/bin/bash
#
# Usage:
#   ./install.sh <function name>

set -o nounset
set -o pipefail
set -o errexit

_link() {
  ln -s -f -v "$@"
}

bin() {
  _link $PWD/latch.sh ~/bin/latch
  _link $PWD/wp.sh ~/bin/wp
}


"$@"
