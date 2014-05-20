Using webpipe with the shell
============================

The original idea behind webpipe was to use it with an R client.  But using it
at the shell opens up a lot of possibilities, e.g. for system administration
and performance analysis.

# run the server that listens on port 8988

$ wp run

# hm I don't want to run another server...

# Run EITHER

$ wp run-recv
# listen on port 8988 for local filenames
# also listen on 8987 for remote

# Run a socat server on 8987, which pipes to recv, then writes the file, then
# sends filename to 9899.


# Now you can send stuff locally to 8987.  "wp-stub show" ?  Or send?

 # copy
$ wp scp-stub example.com

$ wp ssh example.com    # Local 8987 tunnel

example.com$ wp-stub show foo.png

Now foo.png appears in the browser on localhost:8989.


Even further generalization:

You want not just the xrender endpoint, but the raw server endpoint?  Hm.
Allow interposition at any point...

The use case is where you run the render pipelines?  Running render pipelines
remotely, but server locally.  If you want to be secure, and don't want to
expose an HTTP server.


