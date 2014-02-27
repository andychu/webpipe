webpipe
=======

webpipe is server and a set of tools which bridge the Unix shell and the web.
You create files in a terminal (using [R][], a shell script, etc.), and they
will be rendered immediately in your browser.

It gets rid of the `Alt-Tab F5` dance when creating content.

[R]: http://r-project.org/

Setup
-----

On a Debian/Ubuntu system, do:

    $ sudo apt-get install inotify-tools

This installs the `inotifywait` tool, which notifies the server when a new file
appears.

(Optionally) put webpipe in your `PATH`:

    $ ln -s /path/to/webpipe/webpipe.sh ~/bin/webpipe

Then do one-time initialization of your `~/webpipe` dir:

    $ webpipe init

Create a convenience symlink for the R library:

    $ ln -s /path/to/webpipe/webpipe.R ~/webpipe


R Plots
-------

The initial motivation for webpipe was to show R plots in a browser, avoiding
the remote X11 protocol in favor of HTTP.

First start the notifier and the server:

    $ webpipe run

This creates a new "session", e.g. `2014-02-17`.  It listens for files in the
`~/webpipe/input` directory, and then renders them to HTML in the
`~/webpipe/s/2014-02-17` directory.
  
Visit http://localhost:8989/ in your browser.

Then in R, make a plot using the the wrapper functions in `webpipe.R`:
  
    $ R
    ...
    > source('~/webpipe/webpipe.R')
    >
    > web.plot(1:10)
    
Instead of opening up an desktop window, the plot will be pushed to your
browser via AJAX.

ggplot works easily as well:
    
    > library(ggplot2)
    > p = ggplot(mtcars, aes(wt, mpg)) + geom_point()
    > web.plot(p)


<!--
Advanced usage?

    $ webpipe serve 2013-12-01  # serve an old session
    $ webpipe serve downtime    # create a new named session and serve it
      # inotifywait $dir | (file2html | serve)
  -->

 
<!-- TODO: animated screenshot -->


File Types
----------

There renderer module is called `file2html`.  Right now it understands .png
files, plain text, HTML, and CSV files.

The goal is to add other file types, e.g. graphviz dot format.

Advanced Usage
--------------

TODO ...

<!--

The tools form a pipeline as follows:

- R (or any other tools): write files into a directory

- inotifywait - every time a new file appears in the directory, print its
  filename to stdout

- file2html - take the file and "render" it to HTML
- write_files - write rendered files to a directory
- wait_server - block on the next file in a sequence, to allow a "hanging GET"
  to push the file to the browser

- webpipe - main program that strings all these parts together.

Usage:
  $ ./run.sh serve

  $ mkfifo pipe
  $ webpipe render >pipe
    # inotifywait $dir | file2html >pipe
  $ webpipe serve-rendered <pipe
    # read from pipe and serve


- TODO: do this all in process?  Or does it matter?  I guess it's nicer for
- usage reporting, etc.  Plumb file2html and webpipe together.

TODO:

For a remote work setup, you will normally have an inotifywait process and a
webpipe process on the remote machine.  The webpipe process is a web server,
and you view it from your local machine.

An alternative configuration is to run the web server on the *local* machine.
If you don't want a public HTTP server on the remote machine, you may prefer
this setup (although it's more complicated).

- on remote machine: inotify process piped to file2html process, which has its
  stdout directed to a named pie
- ssh from local to remote machine, reading from a named pipe
- ssh stdout piped to webpipe process on local machine, which servers the
  snippets.
  
usage:
- On remote machine:   ./remote.sh print-parts
- On local machine:     ssh ... | ./run.sh webpipe

-->

Known Issues
------------

- Error message on a session that is not "live" is a little ugly.

Feedback
--------

Contact `__EMAIL_ADDRESS__`.



<!-- 

Latch Server
------------

Include in the static HTML output.

latch.js

webpipe refresh *.txt
# listen to *.txt
# and then when it hinges, you do ./build.sh  or Make?
#  foo.txt -> make foo.html
# and then it will POST to latch?  or change it to stdin, named pipe?
#
# the HTML waits on the latch
# 


while true;
  inotifywait
  local file=foo.html
  make $file
  curl http://localhost:8989/latch/$FILE?
done

# what if you change the style?  I guess you can just save the style, and then
# save the file


webpipe scroll
webpipe serve

-->

