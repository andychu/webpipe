#!/usr/bin/python
#
# Copyright 2014 Google Inc. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found
# in the LICENSE file or at https://developers.google.com/open-source/licenses/bsd

"""
spy.py

Client for usage/error reporting.
"""

import json
import os
import socket
import sys
import time


class Error(Exception):
  pass


class UsageReporter(object):

  def __init__(self, host_port):
    self.host_port = host_port
    # Internet / UDP socket
    self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # These values are constant throughout the life of the process, and can be
    # used to match messages.  We assume we have just one usage reporter per
    # process, and that it is instantiated early in the process.  That way
    # start-ts is reasonably accurate.

    self.id_data = {
        # TODO: would getfqdn() be appropriate?  How does thiat work.
        'hostname': socket.gethostname(),
        'pid': os.getpid(),
        }

  def Send(self, msg):
    """Send a raw UDP packet."""
    #log('msg %r', msg)
    self.sock.sendto(msg, self.host_port)

  def SendDict(self, d):
    """Send a JSON-encoded dictionary of data."""
    # TODO:
    # - accept function objects as values.
    #   - And wrap them in a try/catch, so that bad error reporting can't
    #   affect the program.
    # - also need a "extended" process ID?
    #   - hostname / PID / process start time?  that might be good enough.
    #   - can you encode this efficiently?
    #   - homer/3434/13232
    #     - does time.time have too much resolution?

    msg = json.dumps(d)
    self.Send(msg)

  def SendRecord(self, event, d):
    """Send a JSON-encoded record with some standard data.

    Hostname and PID are send to uniquely identify the process.  local time is
    calculated and sent.
    """
    rec = dict(self.id_data)
    if d:
      rec.update(d)
    rec['ev'] = event  # type of event
    rec['ts'] = time.time()
    self.SendDict(rec)

  # TODO:
  # SendStart() ?  Most programs use this at the beginning.
  # SendSummary() ?
  # maybe there should be a protocol where you can send an accumulator object.


class NullUsageReporter(object):
  def Send(self, msg):
    pass
  def SendDict(self, d):
    pass
  def SendRecord(self, event, d):
    pass


def _GetUsageConfig():
  """Allow the user to turn off usage reporting with an environment variable."""

  # TODO: maybe use a level number?  default level 9?
  # You probably want to distinguish between:
  # - report bugs
  # - report usage
  # maybe name them.
  #
  # SPY_REPORT_LEVEL=     # nothing
  # SPY_REPORT_LEVEL=bugs (only bugs)
  # SPY_REPORT_LEVEL=usage (usage and bugs.  usage normally includes start, and
  #   a summary at the end.  Should involve perf)
  # SPY_REPORT_LEVEL=perf?  Is this a separate one?  I think the app should
  # collect this and send it as usage.

  # SPY_REPORT_LEVEL=usage-details (argv, env, etc. Sutff that could be
  # private)

  # default is 'usage'.

  var = os.getenv('SPY_REPORT_USAGE')
  do_report = True
  if var is not None:
    var = var.strip()
    # set it to 0 or empty to turn off
    if var in ('', '0'):
      do_report = False
      log('Not reporting usage because SPY_REPORT_USAGE was set')
  return do_report


def _ReadAddressFile(address_file=None):
  # TODO: readlink?  or does basis take care of it?

  if not address_file:
    d = os.path.dirname(sys.argv[0])
    address_file = os.path.join(d, 'usage-address.txt')

  try:
    with open(address_file) as f:
      contents = f.read()
    host, port = contents.split(':')
    port = int(port)
    result = (host, port)
  except IOError, e:
    #log('address Not found')
    result = None

  return result


def GetClientFromConfig(address_file=None):
  """
  Get a client, which may be the null client.

  Right now we lookat
  """
  # server can be configured with a usage file
  do_report = _GetUsageConfig()

  address = _ReadAddressFile(address_file=address_file)
  if do_report and address:
    reporter = UsageReporter(address)
  else:
    reporter = NullUsageReporter()
  return reporter

