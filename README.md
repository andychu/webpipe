webpipe
=======

webpipe is server and a set of tools which bridge the Unix shell and the web.
You create files in a terminal (using [R][], a shell script, etc.), and they
will be rendered immediately in your browser.

It gets rid of the `Alt-Tab F5` dance when creating content.

[R]: http://r-project.org/

End Users
---------

See [doc/webpipe.html]() for instructions on how to use it.


Developing
----------

Use the `wp-dev.sh` wrapper for `wp.sh`:

    $ ./wp-dev.sh run

This script relies on a couple dependencies existing in hard-coded paths.
Fetch them as follows:

Make a `~/hg` dir.

    $ hg clone https://code.google.com/p/json-template/ 

    $ hg clone https://code.google.com/p/tnet/

[JSON Template](https://code.google.com/p/json-template/) is the template
language used, and [TNET](https://code.google.com/p/tnet/) is the serialization
format.

Portability
-----------

There are multiple components to `webpipe`, each with different portability
constraints.

It's somewhat confusing because the webpipe client often runs on servers, and
the webpipe server may run on your client (i.e. "localhost").

From roughly least to most portable:

- R client: this generally runs on a Linux box.  It currently depends on "nc",
  which should be on most Linux boxes.  netcat is very un-portable, but we are
  just using the simple invocation `nc localhost $port`, which is hopefully
  portable.

- server and renderer: should run on Linux/Mac

- shell client: this is the MOST portable one.  Probably won't run on Mac.  But
  right now it runs on machines without Python or bash!  It just uses plain
  shell.  And "nc" client only.

TODO: Get rid of nc servers.  Not portable.  socat servers also won't run well
on Mac, and are not installed by default on Linux.  So do it in Python.

