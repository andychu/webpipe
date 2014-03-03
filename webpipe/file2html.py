#!/usr/bin/python
"""
file2html.py

A filter that reads filenames from stdin, and prints HTML directories on
stdout.

File types:

- .png -> inline HTML images (data URIs) 
- .csv -> table

Next:

- .script -- type script for Shell session
  - a configurable prefix, like "hostname; whoami;" etc. would be useful.
- .grep -- grep results
  - But then do we have to copy a ton of files over?
  - file2html needs have access to the original directory.
  - and the command

Ideas:

- .url file -> previews of URLs?
- .foo-url -> previews of a certain page?

Should this call a shell script then?  Or it could be a shell script?  The
function will use the tnet tool?

TODO: Make this usable as a library too?  So in the common case you can have a
single process.
"""

import cgi
import csv
import os
import sys

import jsontemplate
import tnet


class Error(Exception):
  pass


PRE_TEMPLATE = """\
<center>
<pre>
%s
</pre>
</center>
"""

IMG_TAG = jsontemplate.Template("""\
<center>
<img src="{url|htmltag}" />
</center>
""", default_formatter='html')

# See http://datatables.net/usage/
# CDN: http://www.asp.net/ajaxlibrary/CDNjQueryDataTables194.ashx

# TODO:
# - generate a different table ID for each one, and then style only that?
#   - I think you can generate the ID in the web roll.  That makes a lot more
#   sense, since it's dynamic.
#   - <div class="roll-part" id="part1"> 
# - don't want every plugin to hard code jquery.getScript
#   - would be nicer to present <elem js="http://" css="http://">

TABLE_TEMPLATE = jsontemplate.Template("""\

<link rel="stylesheet" type="text/css"
      href="http://ajax.aspnetcdn.com/ajax/jquery.dataTables/1.9.4/css/jquery.dataTables.css" />

<script type="text/javascript">
var dtjs="http://ajax.aspnetcdn.com/ajax/jquery.dataTables/1.9.4/jquery.dataTables.min.js";

//$.getScript(dtjs, function() {
//  // NOTE: Is this inefficient?  When you have a lot of tables, it's doing
//  // everything.  Another approach is to generate a unique ID.  But user
//  // scripts might not have that benefit?
//
//  $('.data-table').dataTable();
//});

// Using Chrome dev tools, we can that the JS becomes a cache hit, while
// $.getScript() explicitly breaks caches.

$.ajax({
  url: dtjs,
  dataType: "script",
  cache: true,  // avoid loading every time
  success: function() {
    $('.data-table').dataTable();
  }
});

</script>

<table class="data-table" align="center">
  <thead>
    <tr> {.repeated section thead} <th>{@}</th> {.end} </tr>
  </thead>
  <tbody>
    {.repeated section rows}
      <tr> {.repeated section @} <td>{@}</td> {.end} </tr>
    {.end}
  </tbody>
</table>

<p>
  <a href="{orig_url|htmltag}">{orig_anchor}</a>
</p>
""", default_formatter='html')


def log(msg, *args):
  if args:
    msg = msg % args
  print >>sys.stderr, 'file2html:', msg


def RenderCsv(orig_rel_path, filename, contents):
  """
  Turn CSV into an HTML table.

  TODO: maximum number of rows.
  """
  lines = contents.splitlines()
  c = csv.reader(lines)
  d = {'rows': [], 'orig_url': orig_rel_path, 'orig_anchor': filename}

  for i, row in enumerate(c):
    #print 'R', row
    if i == 0:
      d['thead'] = row
    else:
      d['rows'].append(row)
  #print d
  return TABLE_TEMPLATE.expand(d)


def main(argv):
  """Returns an exit code."""

  # NOTE: This is the base path.  We just join them with the filenames on
  # stdin.  It might be better to just get absolute paths on stdin.
  dir = argv[1]

  # Write out the index
  d = os.path.dirname(sys.argv[0])
  index_path = os.path.join(d, 'index.html')

  with open(index_path) as f:
    index_html = f.read()

  out = {'files': [
      {'path': 'index.html', 'contents': index_html},
      ]}

  sys.stdout.write(tnet.dumps(out))

  counter = 1  # application is 1-indexed
  while True:
    line = sys.stdin.readline()
    if not line:
      break

    filename = line.strip()

    path = os.path.join(dir, filename)

    # TODO: handle errors
    with open(path) as f:
      contents = f.read()

    _, ext = os.path.splitext(filename)

    log('ext: %s', ext)

    orig_rel_path = '%d/%s' % (counter, filename)
    orig = None  # original contents

    if ext == '.png':
      html = IMG_TAG.expand({'url': orig_rel_path})
      orig = contents
      # For now, put it all on one line

    elif ext == '.csv':
      html = RenderCsv(orig_rel_path, filename, contents)
      orig = contents

    elif ext == '.html':
      # This is how users can "extend" the web roll.  They just write a tool
      # that outputs HTML.
      # But can they have separate files and hyperlinks to them?
      #
      # You probably need a JavaScript plugin.  Say you want to experiment with
      # d3.js.

      # TODO: have option for sanitizing?
      # By default, the web roll server trusts all input.  It performs no
      # validation whatsoever.  Security is the responsibility of the file2html
      # process.
      html = contents

    elif ext == '.txt':
      # TODO: need a tool that converts this
      b = cgi.escape(contents).strip()

      # TODO: add raw link, with the filename.
      # we don't really know the number though.
      # <a href="filename.txt">filename.txt<a>
      # <a href="i/filename.txt">filename.txt<a>
      #
      # if there is a "files", then the server can write it to "1/index.html".
      # otherwise 1.html?
      # then serve 1/

      html = PRE_TEMPLATE % b

    else:
      # Default: ignore?  Render text?  Or show error?
      log('ignored: %s', filename)

    # TODO: Add filenames.
    # Only if it's too big do we omit it... and we can append HTML that says
    # "too big"
    #out = {'html': html}

    path = '%d.html' % counter
    files = [
        {'path': path, 'contents': html},
        ]
    if orig:
      o = {'path': orig_rel_path, 'contents': contents}
      files.append(o)

    out = {'files': files}
    sys.stdout.write(tnet.dumps(out))

    counter += 1

  return 0


if __name__ == '__main__':
  try:
    sys.exit(main(sys.argv))
  except KeyboardInterrupt:
    print >>sys.stderr, 'file2html: Stopped'
    sys.exit(0)
  except Error, e:
    print >> sys.stderr, e.args[0]
    sys.exit(1)
