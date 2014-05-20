Using webpipe with the shell
============================

Or "Bringing back graphical computing for headless servers"

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

# TODO: Also need to test two tunnels.  Can we use the same port?  What about
# with big files?

example.com$ wp-stub show foo.png

Now foo.png appears in the browser on localhost:8989.

Even further generalization:

You want not just the xrender endpoint, but the raw server endpoint?  Hm.
Allow interposition at any point...

The use case is where you run the render pipelines?  Running render pipelines
remotely, but server locally.  If you want to be secure, and don't want to
expose an HTTP server.


Pipeline implementation options:

- threads and Queue()
- coroutines
  - it's synchronous dataflow, so you don't need queues really.
  - BUT: if each stage has input from a real socket, and the previous stage,
    can you do that with Python coroutines?  can you do fan in?
    I think so.  Call stage.send() from two places.
    Multiple network ports need a select() loop.

Add --listen for every stage?  So you can listen on recv input, xrender input,
or server input port (and listen on HTTP serving port too)

What's the command line syntax?  You can run:

- serve
- xrender and serve
- recv xrender and serve

And you can run other parts on the remote machine.

- send
- xrender then send

So pipelines look like this, where == is a TCP socket separating machines.  |
is a pipe, or possibly in-process Queue/channel.

xrender | serve (local machine only)

send == recv | xrender | serve

xrender | send == recv | serve

NOTE: send does not currently handle directories, or the combo of file +
directory that webpipe uses.  I guess we write the file last for this reason.


What does the client look like?  Difference between show and send?  I think you
want to use show everywhere.  Both local and remote.  Ports are the same.
"show" goes to port 8988?  "send" goes to port 8987.

Ports:
- 8987 for recv input
- 8988 for xrender input
- TODO: change is to it's 8980 8981 8982?  Three consecutive ports
  WEBPIPE_RECV_PORT
  WEBPIPE_XRENDER_PORT
  WEBPIPE_HTML_PORT
  Need this because those ports might be used on the machine.

- 8989 is webpipe HTTP server
- 8900 is for latch HTTP


More advanced idea
------------------

Along the lines of "bringing back graphical computing".

- What if you want a "live top" or something.  Or a "live pstree".  A visualization.

Then you aren't just sending files back.  You want a client program that prints
a textual protocol to stdout for updates.  Like it will print CPU usage lines
or something.

And then you want to pipe that directly to JS and visualize it?

The easiest demo is some kind of time series.  You scp a little shell/Python
script to a server.  And then it will output a time series.



