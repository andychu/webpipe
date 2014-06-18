#!/bin/sh
#
# Copyright 2014 Google Inc. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found
# in the LICENSE file or at https://developers.google.com/open-source/licenses/bsd


readonly THIS_DIR=$(dirname $0)
. $THIS_DIR/../webpipe-lib.sh

checkDeps() {
  local msg="tar not found.  Run 'sudo apt-get install tar'"
  which tar >/dev/null || die "$msg"
}

showFile() {
  local eInput=$1
  local tarFlag=$2

  # TODO:
  # - factor into WP_GetFileSize?
  # - would be nice to sum the column, show compression ratio, etc.

  local size=$(stat --printf '%s' $eInput)
  echo "<p>$eInput, $size bytes</p>"

  echo '<pre>'

  # notes:
  # - assumes GNU tar
  # - verbose shows file perms, etc.
  tar --verbose --list $tarFlag < $eInput | WP_HtmlEscape 

  echo '</pre>'
}

main() {
  local eInput=$1
  local eOutput=$2
  local tarFlag=$3  # -z, -j, etc.

  checkDeps

  set -o errexit

  local html=$eOutput.html

  showFile $eInput $tarFlag >$html

  echo $html
}

main "$@"

