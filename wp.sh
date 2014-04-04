#!/bin/bash
#
# User facing executables for webpipe.
#
# Usage:
#   ./wp.sh <function name>

set -o nounset
set -o pipefail

#
# Path stuff
#

# cross platform readlink -f
realpath() {
  local path=$0
  local ostype=${OSTYPE:-}
  # test if ostype begins with "darwin".  ignore stdout of expr.
  if expr $ostype : darwin >/dev/null; then
    python -S -c 'import os,sys; print os.path.realpath(sys.argv[1])' $path
  else
    readlink -f $path
  fi
}

# dereference symlinks in $0
readonly THIS_DIR=$(dirname $(realpath $0))

webpipe_dev=${WEBPIPE_DEV:-}
if test -z "$webpipe_dev"; then
  export PYTHONPATH=$THIS_DIR
fi

#
# Utilities
#

log() {
  echo 1>&2 "$@"
}

die() {
  log "$@"
  exit 1
}

readonly INPUT_DIR=~/webpipe/input
# is watched necessary anymore?  no reason most people can't shell out to nc.
# but it is still possible.
readonly WATCH_DIR=~/webpipe/watched

check-tools() {
  local err="'nc' not found.  Run 'sudo apt-get install netcat'?"
  which nc >/dev/null || die "$err"
}

#
# Public
#

# Set up the default dir to watch.
init() {
  # Where files from the input dirs are moved and renamed to, so they are HTML
  # and shell safe.
  mkdir --verbose -p \
    ~/webpipe/renamed \
    $INPUT_DIR/sink \
    $WATCH_DIR \
    ~/webpipe/plugins
  # Where user can install their own plugins

  # Named pipe that receives paths relative to the sink dir.  We remove and
  # create the pipe to reset it?
  # NOTE: We want at least two ways of showing files:
  # - put something in the 'watched' dir
  # - wp show <filename>
  #
  # A named pipe can't handle both.  You would need a Unix socket.

  #rm --verbose ~/webpipe/input
  #mkfifo ~/webpipe/input
  #local exit_code=$?
  #if test $exit_code -eq 0; then
  #  log "Created ~/webpipe/input"
  #else
  #  log "mkfifo error"
  #fi

  # Do this last, since it dies.
  check-tools

  log "wp: init done"
}

# People can run print-events | xrender to directly to render on a different
# host.  For now we keep them separate, so we have an explicit and flexible
# pipeline.

print-events() {
  local input_dir=${1:-$WATCH_DIR}

  # --quiet: only print events
  # --monitor: loop forever
  # --format %f: print out the filename in the directory we're watching

  # close_write: when a file is closed after writing
  # create: creating a symlink (ln -sf of a dir alway does DELETE then CREATE)

  log "wp: Watching $input_dir"
  inotifywait --monitor --quiet -e close_write,create $input_dir --format '%f'
}

# render files to HTML.
xrender() {
  $THIS_DIR/webpipe/xrender.py "$@"
}

# serve HTML and static files.
serve() {
  $THIS_DIR/webpipe/serve.py "$@"
}

nc-listen() {
  local port=$1
  # -k: keep listening after one connection
  # -l listen
  nc -v -k -l localhost $port </dev/null
}

# Run the whole pipeline.
#
# TODO:
# - Add flags that are common: --user-dir, --port (for server), etc.
# - What about rendering flags?
#
# $ webpipe run --port 8888

run() {
  local sessionName=${1:-}
  check-tools

  local stamp=$(date +%Y-%m-%d)
  if test -z "$sessionName"; then
    sessionName=$stamp
  else
    # Special syntax: + prepends the current date.
    # run +foo  ==>  session name is 2014-03-30-foo
    sessionName=$(echo $sessionName | sed s/+/$stamp-/)
  fi

  local session=~/webpipe/s/$sessionName
  mkdir -p $session

  export PYTHONUNBUFFERED=1

  nc-listen 8988 \
    | xrender $INPUT_DIR $session \
    | serve serve $session
}

# Like run, but just test latency.
noop() {
  local sessionName=${1:-}
  check-tools

  local stamp=$(date +%Y-%m-%d)
  if test -z "$sessionName"; then
    sessionName=$stamp
  else
    # Special syntax: + prepends the current date.
    # run +foo  ==>  session name is 2014-03-30-foo
    sessionName=$(echo $sessionName | sed s/+/$stamp-/)
  fi

  export PYTHONUNBUFFERED=1

  # make sure it succeeds
  echo foo >/tmp/foo.txt
  echo foo.txt \
    | xrender /tmp /tmp \
    | serve noop
}

show() {
  for filename in "$@"; do
    if test ${filename:0:1} = /; then
      echo "$filename" | nc localhost 8988
    else
      # relative path, make it absolute.
      echo "$PWD/$filename" | nc localhost 8988
    fi
  done
}

# Sink for local render.
# Example:
#   ls | wp sink
sink() {
  local ext=${1:-txt}  # e.g. dot graph
  # Use process ID for now.  It's OK if it's overwritten.
  local tempfile=$INPUT_DIR/sink/$$.$ext
  cat > $tempfile
  echo $tempfile | nc localhost 8988
}

publish() {
  $THIS_DIR/webpipe/publish.py "$@"
}

# set up reverse tunnel for receiving files.
wp-ssh() {
  log "webpipe: Setting up SSH reverse tunnel from remote port 8987 to localhost port 8987."
  ssh -R 8987:localhost:8987 "$@"
}

# Other actions:
# - sink (move from the stub?)
# - show <files...>
# - watch -- start the inotify daemon on watched
#
# Individual actions (for advanced users):
# - xrender
# - serve

help() {
  local topic=${1:-}
  case "$topic" in
    advanced)
      cat $THIS_DIR/doc/wp-help-advanced.txt
      ;;
    *)
      cat $THIS_DIR/doc/wp-help.txt
      ;;
  esac
}

recv() {
  export PYTHONUNBUFFERED=1
  $THIS_DIR/webpipe/recv.py "$@"
}

run-recv() {
  nc-listen 8987 \
    | recv ~/webpipe/input \
    | while read line; do echo $line | nc localhost 8988; done
}

#
# Introspection
#

# So people can do scp $(webpipe stub-path) user@example.org:bin
stub-path() {
  local path=$THIS_DIR/wp-stub.sh
  if test -f $path; then
    echo $path
  else
    die "Invalid installation; $path doesn't exist"
  fi
}

scp-stub() {
  local path=$(stub-path)
  scp $path "$@"
}

version() {
  # TODO: Show the actual version?  For now just show the package-dir.
  # assuming that has the version.
  package-dir
}

# Use this to find stub path?
# TODO: Should there also be a user-dir thing?  I think that should always be
# ~/webpipe.
package-dir() {
  echo $THIS_DIR
}

if test $# -eq 0; then
  help
  exit 0
fi

case $1 in 
  # generally public ones
  help|init|run|noop|run-recvpackage-dir|publish|show|sink|stub-path|scp-stub|version)
    "$@"
    ;;
  ssh)
    # need to special case this to avoid recursion
    shift
    wp-ssh "$@"
    ;;
  # advanced ones
  recv|serve|xrender)
    "$@"
    ;;
  # demo
  sendrecv-demo)
    "$@"
    ;;
  --help|-h)
    help
    ;;
  *)
    # uncomment to run internal functions
    #"$@"
    die "wp: Invalid action '$1'"
    ;;
esac

