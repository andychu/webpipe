#!/usr/bin/python
"""
csv_plugin.py

This is in process in xrender.py until we work out packaging issues.
"""

import csv
import os
import shutil
import sys

import jsontemplate

class Error(Exception):
  pass

# See http://datatables.net/usage/
# CDN: http://www.asp.net/ajaxlibrary/CDNjQueryDataTables194.ashx
#
# TODO: We can put this in the /static dir

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
""", default_formatter='html')


PREVIEW_TEMPLATE = jsontemplate.Template("""\
<p>{basename} - {num_rows} rows</p>

<p><a href="{output}/full.html">Browse CSV</a></p>

<p><a href="{output}/{basename}">Download Original CSV</a></p>

""", default_formatter='html')



# TODO: avoid loading the entire thing in memory?
def ParseAndRender(f):
  """
  Turn CSV into an HTML table.

  TODO: maximum number of rows.
  """
  c = csv.reader(f)
  d = {'rows': []}

  num_rows = 0
  for i, row in enumerate(c):
    #print 'R', row
    if i == 0:
      d['thead'] = row
    else:
      d['rows'].append(row)
    num_rows += 1
  return TABLE_TEMPLATE.expand(d), num_rows


def main(argv):
  """Returns an exit code."""

  # Assume we're in the output dir
  input_path, output = argv[1:]

  os.mkdir(output)
  basename = os.path.basename(input_path)
  orig = os.path.join(output, basename)

  # Copy the original
  shutil.copy(input_path, orig)

  full_html = os.path.join(output, 'full.html')
  with open(full_html, 'w') as f:
    with open(input_path) as infile:
      h, num_rows = ParseAndRender(infile)
    f.write(h)

  print output  # finished the dir

  # This

  html = output + '.html'

  with open(html, 'w') as f:
    d = {
        'num_rows': num_rows,
        'output': output,
        'basename': basename,
        }
    # TODO: check how many rows, and write head/tail, or full thing.
    f.write(PREVIEW_TEMPLATE.expand(d))

  print html  # wrote html

  return 0


if __name__ == '__main__':
  try:
    sys.exit(main(sys.argv))
  except Error, e:
    print >> sys.stderr, e.args[0]
    sys.exit(1)
