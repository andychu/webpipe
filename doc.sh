#!/bin/bash
#
# Usage:
#   ./doc.sh <function name>

# Add the HTML shell.  A data dictionary should be readable stdin.  Does NOT
# depend on $PWD, so callers can cd.

to-html() {
  local name=$1
  jsont doc/html.jsont > _tmp/$name-full.html
}

make-dict() {
  local name="$1"
  # Add PULP_ variables from the environment, so that 'PULP_latch=1 poly build'
  pin \
    --title-tag=h1 \
    _tmp/$name.html
}

main() {
  local in=$1
  local out=$2

  echo "Building $in -> $out"
  cat >$out <<EOF
<html>
  <head>
    <!-- TODO: load this only if it's not already loaded? -->
    <script type='text/javascript'
            src="https://ajax.googleapis.com/ajax/libs/jquery/1.8.3/jquery.min.js">
    </script>

<!-- INSERT LATCH JS -->
  </head>
  <body>
    <div id="latch-status">Waiting</div>
EOF

  markdown $in >>$out

  cat >>$out <<EOF
  </body>
</html>
EOF

  ls -al $out
}

#main "$@"

"$@"
