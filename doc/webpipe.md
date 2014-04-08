webpipe
=======

webpipe is server and a set of tools which bridge the Unix shell and the web.
You create files in a terminal (using [R][], bash, etc.), and they will be
rendered immediately in your browser.

It gets rid of the `Alt-Tab F5` dance when creating content.

[R]: http://r-project.org/

<a href="screencast.html">
  <img src="screenshot_small.jpg" alt="webpipe screenshot" />
</a>

Setup
-----

Put `wp` in your `PATH`.  For example:

    $ ln -s /path/to/webpipe/wp.sh ~/bin/wp

Do one-time initialization of your `~/webpipe` dir:

    $ wp init

Create a convenience symlink for the R library:

    $ ln -s /path/to/webpipe/webpipe.R ~/webpipe


R Plots
-------

The initial motivation for webpipe was to show R plots in a browser, avoiding
the remote X11 protocol in favor of HTTP.

First start the renderer and server:

    $ wp run

This creates a new "session", e.g. `2014-04-03`.  Files can be put in the
`~/webpipe/input` directory, and then they are rendered to HTML in the
`~/webpipe/s/2014-02-17` directory.
  
Visit http://localhost:8989/ in your browser.

Then in R, make a plot using the the wrapper functions in `webpipe.R`:
  
    $ R
    ...
    > source('~/webpipe/webpipe.R')
    >
    > web.plot(1:10)
    > web.hist(rnorm(10))
    
Instead of opening up an desktop window, the plot will be pushed to your
browser via AJAX.

ggplot works easily as well:
    
    > library(ggplot2)
    > p = ggplot(mtcars, aes(wt, mpg)) + geom_point()
    > web.plot(p)

Shell Usage
-----------

You can also display files from the shell:

    $ wp show mydata.csv

With no file, `show` reads from stdin.

    $ ls -l | wp show

Use `wp help` to see more actions.


File Types
----------

The renderer process is called `xrender`, which shells out to various plugins.
It understands `.png` files, plain text, HTML, and CSV files.  (TODO: document
the full list)

More Docs
---------

   * [Gallery](gallery/) of plugin types (under construction)

Publishing
----------

You can publish entries to "shared hosting", so you don't have to keep your
server up.

TODO ...


Advanced Usage
--------------

TODO ...


<!--
Advanced usage?

    $ webpipe serve 2013-12-01  # serve an old session
    $ webpipe serve downtime    # create a new named session and serve it
      # inotifywait $dir | (file2html | serve)
  -->

 

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

- There is too much debug spew on the terminal.

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


