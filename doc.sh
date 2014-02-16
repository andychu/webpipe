#!/bin/bash
#
# Usage:
#   ./doc.sh <function name>

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

main "$@"
