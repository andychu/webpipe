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




