# webpipe-lib.sh
#
# Not executable, but should be sourceable by /bin/sh.
#

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
