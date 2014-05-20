# Simple R functions to use web pipe.
#
# Examples:
#
# > web.plot(1:10)               # alternative to plot(1:10)
# > web.hist(rnorm(10))          # hist(1:10)

# Underlying function is web.png.
#
# > web.png(hist, rnorm(10))     # alternative to hist(rnorm(10))
# > web.plot(hist(rnorm(10), plot=F))   # another alternative
#
# The webpipe.png.args option is used to determine additional arguments to the
# png device.
#
# Example:
#   options(webpipe.png.args=list(width=800, height=600))

# TODO:
# - Can the user configure the input dir?  Environment var?

# NOTE: png() accepts ~/webpipe, but CairoPNG doesn't.  (It doesn't expand ~).
web.plot.dest = path.expand('~/webpipe/input')  # expand ~

web.plot.num = 0

# Wrap a function that writes to a graphic device so that it writes a .png to
# the webpipe input directory.

web.png = function(func, ...) {
  # NOTE: giving it the "dual extension" .Rplot.png, so we can possibly do
  # different things with it, vs. a regular png.
  plot.path = file.path(web.plot.dest, sprintf('%03d.Rplot.png', web.plot.num))

  # Let the user pass their own dimensions, etc.  filename can't be overridden.
  png.args = getOption("webpipe.png.args", list())
  png.args$file = plot.path

  # NOTE: in an interactive session, it's possible to do png <- CairoPNG to
  # avoid "x11 is not available" errors.
  do.call(png, png.args)
  func(...)
  dev.off()

  # Debug: assert that the file was created.
  #if (!file.exists(plot.path)) {
  #  print(paste0('ERROR ', plot.path))
  #}

  cat(sprintf('%s\n', plot.path))

  web.plot.num <<- web.plot.num + 1  # increment global

  # Notify webpipe that there is a plot.

  # NOTE: no shQuote necessary because we construct the filename.
  cmd = sprintf('echo %s | nc localhost 8988', plot.path)
  exit.code = system(cmd)
  if (exit.code != 0) {
    cat(sprintf("Command '%s' failed.\n", cmd))
    # Possibly give the hint to install nc
    code2 = system('nc -h')
    if (code2 != 0) {
      cat("Couldn't execute 'nc' (netcat).  Is it installed?\n")
    }
  }

  invisible()  # no return value printed in REPL
}

# Like R plot(), but writes to the webpipe input directory.

web.plot = function(...) {
  web.png(plot, ...)
}

# Like R hist().

web.hist = function(...) {
  web.plot(hist(..., plot=F))
}
