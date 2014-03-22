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
# TODO:
# - consider putting row numbers next to each row, in grey.  It will make it
# clearer.
# - refactor template to remove duplication
# - could you use R to show histograms of the rows?
# - We can put this in the /static/ dir

# TODO:
# - generate a different table ID for each one, and then style only that?
#   - I think you can generate the ID in the web roll.  That makes a lot more
#   sense, since it's dynamic.
#   - <div class="roll-part" id="part1"> 
# - don't want every plugin to hard code jquery.getScript
#   - would be nicer to present <elem js="http://" css="http://">

def Commas(n):
  return '{:,}'.format(n)


FORMATTERS = {'commas': Commas}

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

<p><code>{basename}</code> - {num_rows|commas} rows, {num_bytes|commas}
bytes</p>

<table class="data-table" align="center" style="text-align: right;" width="50%">
  <thead>
    <tr> {.repeated section thead} <th>{@}</th> {.end} </tr>
  </thead>
  <tbody>
    {.repeated section rows}
      <tr> {.repeated section @} <td>{@}</td> {.end} </tr>
    {.end}
  </tbody>
</table>
""", default_formatter='html', more_formatters=FORMATTERS)


PREVIEW_TEMPLATE = jsontemplate.Template("""\
<p><code>{basename}</code> - {num_rows|commas} rows, {num_bytes|commas}
bytes</p>

<table align="center" style="text-align: right;" width="50%">
  <thead>
    <tr> {.repeated section thead} <th>{@}</th> {.end} </tr>
  </thead>
  <tbody>
    {# show either a preview, or full rows}

    {.if test head}
      {.repeated section head}
        <tr> {.repeated section @} <td>{@}</td> {.end} </tr>
      {.end}

      <tr>
        <td colspan="{num_cols}" style="text-align: center; font-style: italic;">
          ... <a href="{output}/full.html">{num_omitted|commas} rows omitted</a>
        </td>
      </tr>

      {.repeated section tail}
        <tr> {.repeated section @} <td>{@}</td> {.end} </tr>
      {.end}

    {.or}
      {.repeated section rows}
        <tr> {.repeated section @} <td>{@}</td> {.end} </tr>
      {.end}

    {.end}

  </tbody>
</table>

<p><a href="{output}/{basename}">Download Original CSV</a></p>

""", default_formatter='html', more_formatters=FORMATTERS)


# User setting for how many lines of head/tail they want to see.
wp_num_lines = os.getenv('WP_NUM_LINES', 5)

# TODO: avoid loading the entire thing in memory?
def ParseAndRender(f):
  """
  Turn CSV into an HTML table.

  TODO: maximum number of rows.
  """
  c = csv.reader(f)
  rows = []
  d = {'rows': rows}

  num_rows = 0
  for i, row in enumerate(c):
    #print 'R', row
    if i == 0:
      d['thead'] = row
    else:
      rows.append(row)
    num_rows += 1

  # wp_num_lines is 5, then we should show in full anything less than 15 rows
  if len(rows) >= wp_num_lines * 3:
    d['num_omitted'] = num_rows - (wp_num_lines * 2)
    d['head'] = head = rows[ : wp_num_lines]
    d['tail'] = rows[-wp_num_lines : ]

  d['num_rows'] = num_rows

  return d


def main(argv):
  """Returns an exit code."""

  # Assume we're in the output dir
  input_path, output = argv[1:]

  os.mkdir(output)
  basename = os.path.basename(input_path)
  orig = os.path.join(output, basename)
  
  num_bytes = os.path.getsize(input_path)

  # Copy the original
  shutil.copy(input_path, orig)

  full_html = os.path.join(output, 'full.html')
  with open(full_html, 'w') as outfile:
    with open(input_path) as infile:
      data_dict = ParseAndRender(infile)
      data_dict['num_bytes'] = num_bytes
      data_dict['output'] = output
      data_dict['basename'] = basename
      # So we can have a colspan
      data_dict['num_cols'] = len(data_dict['thead'])

    outfile.write(TABLE_TEMPLATE.expand(data_dict))

  print output  # finished the dir

  html = output + '.html'
  with open(html, 'w') as f:
    # TODO: check how many rows, and write head/tail, or full thing.
    f.write(PREVIEW_TEMPLATE.expand(data_dict))

  print html  # wrote html

  return 0


if __name__ == '__main__':
  try:
    sys.exit(main(sys.argv))
  except Error, e:
    print >> sys.stderr, e.args[0]
    sys.exit(1)
