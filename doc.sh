#!/bin/bash
#
# Copyright 2014 Google Inc. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found
# in the LICENSE file or at https://developers.google.com/open-source/licenses/bsd

#
# Usage:
#   ./doc.sh <function name>

# Add the HTML shell.  A data dictionary should be readable stdin.  Does NOT
# depend on $PWD, so callers can cd.

set -o nounset
set -o errexit

to-html() {
  local out=$1
  jsont doc/html.jsont > $out
}

# TODO: Get rid of bad dependencies:
#
# webpipe docs -> pin -> docopt
make-dict() {
  local body_filename=$1
  pin --title-tag=h1 $body_filename
}

# Build main docs.  Called by ./run.sh latch-demo, which calls './latch.sh
# rebuild'.
build() {
  local in=$1
  local out=$2

  local base_in=$(basename $in .md)  # For now, get rid of subdirs
  local body=_tmp/$base_in-body.html

  mkdir -p --verbose $(dirname $out)
  echo "Building $in -> $body -> $out"

  markdown $in >$body

  ls -al $body

  local template
  case $base_in in
    # Use simpler template from the screencast (so it's not skinny)
    screencast)
      template=doc/simple-html.jsont
      ;;
    *)
      template=doc/html.jsont
      ;;
  esac

  make-dict $body | jsont $template > $out

  ls -al $out
}

build-all() {
  build doc/webpipe.md _tmp/doc/webpipe.html
  build doc/screencast.md _tmp/doc/screencast.html
  shrink-screenshot
  gallery

  # For the video
  ln -v -s -f \
    ../../doc/screenshot.jpg \
    ../../doc/screencast.ogv \
    _tmp/doc

  tree _tmp/doc
}

shrink-screenshot() {
  convert doc/screenshot.jpg -scale '50%' _tmp/doc/screenshot_small.jpg
}

# TODO: Just list the plugins/ dir?
# - need to show symlinks

plugin-types() {
  echo dot html json markdown Rplot.png treemap tar.gz txt zip
  # TODO:
  # - csv has issue with importing JSON Template; not being hermetic
  # - R generates <html>, it's not a real snippet
  # - typescript is also generates html
}

# Generate a named snippet for each plugin type.  Then join them into an HTML
# doc.

gallery-snippets() {
  local plugin_types="$1"
  local out_dir=$2

  rm -rf $out_dir
  mkdir -p $out_dir

  for p in $plugin_types; do
    local plugin=$PWD/plugins/$p/render 
    local input
    case $p in
      dot)
        input=$PWD/plugins/dot/testdata/cluster.dot
        ;;
      typescript)
        # disabled
        input=$PWD/plugins/typescript/testdata/typescript
        ;;
      *)
        input=$PWD/plugins/$p/testdata/tiny.$p
        ;;
    esac

    # NOTE: we are not providing a number
    local output=$p

    # plugins are written to be in the output dir.
    pushd $out_dir
    $plugin $input $output
    popd >/dev/null
  done
}

print-gallery() {
  local plugin_types="$1"
  local base_dir=$2

  cat <<EOF
<h1>webpipe Gallery</h1>

<p>Here is a list of file types and example documents.  There is a JavaScript
visualization behind some links.</p>
EOF

  # Generate TOC.
  for p in $plugin_types; do
    echo "<a href=\"#$p\">$p</a> <br/>"
  done

  # Generate snippets.  TODO: should be use a <div> or something?

  for p in $plugin_types; do
    echo '<hr />'
    echo "<a id=\"$p\"></a><h3>$p</h3>"

    # TODO: alternative text?
    local path=plugins/$p/gallery.md
    if test -f $path; then
      # display on stdout
      markdown $path
    fi

    # snippet inline
    cat $base_dir/$p.html
  done
}

# TODO:
# - how to get the .js to work?
# It goes ../../...
# Maybe it should be a variable, like $WEBPIPE_PLUGIN_BASE_URL.
#
# could publish it to:
# there will be:
# webpipe/plugins/
# webpipe/s/2014-04-04/1.html
# webpipe/doc/gallery/index.html
# png testdata
#   - just make a little R plot

makelink() {
  local src=$1
  local dest=$2
  mkdir -p $(dirname $dest)
  ln -v -s -f $src --no-target-directory $dest
}

# The gallery needs to reference static assets.  list the ones with static.
# TODO: automate this more?

link-static() {
  makelink $PWD/plugins/treemap/static/ _tmp/plugins/treemap/static
  makelink $PWD/plugins/json/static/ _tmp/plugins/json/static
  tree _tmp/doc
}

gallery() {
  local plugin_types="$(plugin-types)"
  local base_dir=$PWD/_tmp/doc/gallery  # absolute path

  gallery-snippets "$plugin_types" $base_dir

  local body=$base_dir/body.html
  local out=$base_dir/index.html
  print-gallery "$plugin_types" $base_dir > $body

  # NOTE: It's interesting that #anchors don't work without <html>?  At least
  # in Chrome.
  make-dict $body | to-html $out

  # The gallery needs to link to static assets.  TODO: Should be _tmp/doc?
  link-static

  ls -al $base_dir
}

check() {
  # TODO: put this in a test?
  tidy -errors  _tmp/gallery/out/index.html
}

# NOTE: gallery has to be 3 levels deep to access ../../../plugins/*/static
deploy() {
  set -o errexit
  # create a file in this dir with the base dir, e.g. user@host.com:mydir
  local base=$(cat ssh-base.txt)
  echo $base
  # Have to get all the generated dirs.  NOTE: Don't need the individual
  # snippets.  Maybe remove.
  scp -r _tmp/doc/* $base/webpipe/doc
  scp -r _tmp/plugins $base/webpipe
}

#
# Screencast
#

# Use the method here.  "Record my desktop", then convert using mplayer then Image Magick.
#
# http://askubuntu.com/questions/107726/how-to-create-animated-gif-images-of-a-screencast

# 57s for a 2.7 M file.
frames() {
  local video_in=$1
  local frames_out=${2:-}
  if test -z "$frames_out"; then
    local out_dir=_tmp/frames
    mkdir -p $out_dir
    frames_out="$out_dir/$(basename $video_in)"
  fi

  # TODO: use png or gif?
  time mplayer -ao null $video_in -vo jpeg:outdir=$frames_out
}

# Took 4m 37s for a 1.4 MB ogv?  Resulted in 50 MB animated gif.
animated-gif() {
  local frames_in=$1
  local gif_out=${2:-_tmp/gif/screencast.gif}
  mkdir -p $(dirname $gif_out)
  time convert $frames_in/* $gif_out
}

# This method reduces gif from 50MB to 1MB.
#
# But on 142MB gif, this doesn't just crash, but hangs the machine!

optimize-gif() {
  local gif_in=$1
  local gif_out=$(echo $gif_in | sed 's/\.gif/_opt.gif/')
  set -x
  export MAGICK_THREAD_LIMIT=1
  time convert $gif_in -fuzz 10% -layers Optimize $gif_out
}

"$@"
