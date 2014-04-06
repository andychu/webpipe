#!/bin/bash
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

make-dict() {
  local body_filename=$1
  pin --title-tag=h1 $body_filename
}

# Build main docs.  Called by ./run.sh latch-demo, which calls './latch.sh
# rebuild'.
main() {
  local in=$1
  local out=$2

  local base_in=$(basename $in)  # For now, get rid of subdirs
  local body=_tmp/$base_in-body.html

  echo "Building $in -> $body -> $out"

  markdown $in >$body

  ls -al $body

  make-dict $body | to-html $out

  ls -al $out
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
  local base=$2

  rm -rf $base/out  # so it's numbered from 1
  mkdir -p $base/in $base/out

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
    pushd $base/out
    $plugin $input $output
    popd >/dev/null
  done
}

print-gallery() {
  local plugin_types="$1"
  local base=$2

  cat <<EOF
<h1>webpipe Gallery</h1>

<p>Here is a list of file types and example documents.  Click through.</p>

EOF

  # Generate TOC.
  for p in $plugin_types; do
    echo "<a href=\"#$p\">$p</a> <br/>"
  done

  # Generate snippets.  TODO: should be use a <div> or something?

  for p in $plugin_types; do
    echo '<hr />'
    echo "<a id=\"$p\"></a><h3>$p</h3>"
    # snippet inline
    cat $base/out/$p.html
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


gallery() {
  local plugin_types="$(plugin-types)"
  local base_dir=$PWD/_tmp/gallery  # absolute path

  gallery-snippets "$plugin_types" $base_dir

  local body=$base_dir/out/body.html
  local out=$base_dir/out/index.html
  print-gallery "$plugin_types" $base_dir > $body

  # NOTE: It's interesting that #anchors don't work without <html>?  At least
  # in Chrome.
  make-dict $body | to-html $out

  ls -al $base_dir/out
}

check() {
  # TODO: put this in a test?
  tidy -errors  _tmp/gallery/out/index.html
}

# NOTE: it has to be 3 levels deep
# TODO: deploy other docs
deploy-gallery() {
  set -o errexit
  # create a file in this dir with the base dir, e.g. user@host.com:mydir
  local base=$(cat ssh-base.txt)
  echo $base
  # Have to get all the generated dirs.  NOTE: Don't need the individual
  # snippets.  Maybe remove.
  scp -r _tmp/gallery/out/* $base/webpipe/doc/gallery
}

"$@"
