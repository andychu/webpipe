# Simple R functions to use web pipe.
#
# Examples:
#
# > web.plot(1:10)               # alternative to plot(1:10)
# > web.png(hist, rnorm(10))     # alternative to hist(rnorm(10))

# TODO:
# - Can the user configure the dir?  Environment var?

PLOT_DEST <- '~/webpipe/input/Rplot%03d.png'

# Wrap a function that writes to a graphic device so that it writes a .png to
# the webpipe input directory.

web.png <- function(func, ...) {
  png(file=PLOT_DEST)
  func(...)
  dev.off()
}

# Like R plot(), but writes to the webpipe input directory.

web.plot <- function(...) {
  web.png(plot, ...)
}

