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

Plugins
-------

TODO: define interface.

3 args:

$input $output_html $output_dir
       5.html       5/

5.html has to be at the root, not in 5/index.html, because of the relative
<img> links.

What abut pipe?  Instead of writing to output HTML file.  Can the plugin write
to stdout?  It's going to be on disk anyway, so I guess there's no point.  The
only time that's inefficient is what you are running file2html and server on
different machines.  But then you could use tmpfs if it was really a big deal.

"Style Guide".  Things plugins should do:

- check size of file (whether in bytes, entries, depth, etc.)
  - small: just display it inline (and possibly summary)
  - large: display summary, then click through to full view
  - huge: display summary, and message that says it's too big to preview

- summary:
  - size in bytes
  - entries, etc.

- provide original file for download (in most cases)

- zero copy
  - if you make a symlink, then the plugin can read that stuff, create a summary
  - and then can it output a *capability* for the server to serve files
    anywhere on the file system?
    - or perhaps the symlink is enough?  well it could change.
    - maybe you have to dereference the link.
"""

import cgi
import csv
import errno
import json
import os
import re
import subprocess
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


if sys.stderr.isatty():
  PREFIX = '\033[36m' + 'file2html:' + '\033[0;0m'
else:
  PREFIX = 'file2html:'

def log(msg, *args):
  if args:
    msg = msg % args
  print >>sys.stderr, PREFIX, msg


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
  return TABLE_TEMPLATE.expand(d), None


# TODO: use mime types here?
# The two-level hierarchy of:
# image/png, image/gif, etc. might be useful
#
# Also: aliases like htm, html, etc. are detected

def GuessFileType(filename):
  filename, ext = os.path.splitext(filename)
  if ext == '':
    # The 'script' command defaults to a file called 'typescript'.  We assume
    # the terminal is ansi, so we use the ansi plugin to handle it.
    if filename == 'typescript':
      return 'ansi'
    else:
      return None
  else:
    # .png -> png
    return ext[1:]

  return file_type


def RenderPng(orig_rel_path, unused_filename, contents):
  html = IMG_TAG.expand({'url': orig_rel_path})
  orig = contents
  return html, orig


def RenderHtml(orig_rel_path, filename, contents):
  # This is how users can "extend" webpipe.  They just write a tool
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
  return html, None


def RenderTxt(orig_rel_path, unused_filename, contents):
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
  return html, None


BUILTINS = {
    'png': RenderPng,
    'csv': RenderCsv,
    'html': RenderHtml,
    'txt': RenderTxt,
    }


class Resources(object):
  def __init__(self, base_dir=None):
    self.base_dir = base_dir or os.path.dirname(sys.argv[0])
    b = os.path.join(self.base_dir, '..', 'plugins')
    self.bin_base = os.path.normpath(b)

  def GetPluginBin(self, file_type):
    # plugins dir is parallel to webpipe python dir.
    p = os.path.join(self.bin_base, file_type, 'render')

    # TODO: test if it's executable.  Show clear error if not.
    if os.path.exists(p):
      return p
    else: 
      return None


def main(argv):
  """Returns an exit code."""

  # NOTE: This is the input base path.  We just join them with the filenames on
  # stdin.
  in_dir = argv[1]
  out_dir = argv[2]
  # TODO:
  # - input is a single line for now.  Later it could be a message, if you want
  # people to specify an explicit file type.  I guess that can be done with a
  # file extension too, like typescript.ansi.  The problem is that you can't
  # get any other options with it.
  # - output is pointer to files/dirs written.

  res = Resources()

  entries = os.listdir(out_dir)
  nums = []
  for e in entries:
    m = re.match(r'(\d+)\.html', e)
    if m:
      nums.append(int(m.group(1)))

  if nums:
    maximum = max(nums)
  else:
    maximum = 0

  counter = maximum + 1  # application is 1-indexed
  log('counter initialized to %d', counter)

  # e.g. we are about to write "1"
  header = json.dumps({'stream': 'netstring', 'nextPart': counter})

  # Print it on a single line.  Also allow netstring parsing.  Minimal
  # JSON/netstring header is: 2:{}\n.
  sys.stdout.write(tnet.dump_line(header))

  while True:
    line = sys.stdin.readline()
    if not line:
      break

    filename = line.strip()

    # NOTE: Right now, this allows absolute paths too.
    input_path = os.path.join(in_dir, filename)

    # TODO: Plugins should be passed directories directly.
    if os.path.isdir(input_path):
      log('Skipping directory %s (for now)', input_path)
      continue

    # TODO: handle errors
    with open(input_path) as f:
      contents = f.read()

    orig_rel_path = '%d/%s' % (counter, filename)
    orig = None  # original contents

    file_type = GuessFileType(filename)
    log('file type: %s', file_type)

    if file_type is None:
      log("Couldn't determine file type for %r; ignored", filename)
      continue

    out_html_filename = '%d.html' % counter
    out_html_path = os.path.join(out_dir, out_html_filename)

    # 23/
    part_dir = os.path.join(out_dir, str(counter))

    # Order of resolution:
    #
    # 1. Check user's ~/webpipe dir for plugins
    # 2. Check installation dir for plugins distributed with the webpipe
    #    package
    # 3. Builtins

    plugin_bin = res.GetPluginBin(file_type)
    if plugin_bin:

      # TODO: add action here
      argv = [plugin_bin, input_path, out_html_path, part_dir]
      log('argv: %s', argv)
      exit_code = subprocess.call(argv)
      if exit_code != 0:
        log('ERROR: %s exited with code %d', argv, exit_code)

      # NOTE: the plugin responsible for printing the directory, if any?  And
      # making it.

      # Check that the plugin actually create the file.
      if not os.path.exists(out_html_path):
        log('Plugin error: %r not created' % out_html_path)
        continue
      print out_html_filename

    else:
      # TODO: use a chaining pattern instead of nested if-else

      func = BUILTINS.get(file_type)
      if func:
        html, orig = func(orig_rel_path, filename, contents)
        if orig:
          orig_out_path = os.path.join(out_dir, orig_rel_path)

          try:
            os.makedirs(os.path.dirname(orig_out_path))
          except OSError, e:
            if e.errno != errno.EEXIST:
              raise

          with open(orig_out_path, 'w') as f:
            f.write(orig)
          # Print the directory, because we wrote a file there.
          print '%d/' % counter

        with open(out_html_path, 'w') as f:
          f.write(html)
        # This triggers the server
        print out_html_filename

      else:
        log('No builtin renderer for %r; ignored', filename)
        continue

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
