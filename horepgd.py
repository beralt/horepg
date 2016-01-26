#!/usr/bin/env python
# -*- coding: utf-8 -*-

# horepgd.py
#
# This script provides a daemon which runs daily

import os
import sys
import pwd
import grp
import logging
import logging.handlers
import argparse

from horepg import *

# configuration
wanted_channels = ['NPO 1 HD',
           'NPO 2 HD',
           'NPO 3 HD',
           'RTL 4 HD',
           'RTL 5 HD',
           'SBS6 HD',
           'RTL 7 HD',
           'Veronica HD / Disney XD',
           'Net5 HD',
           'RTL 8 HD',
           'FOX HD',
           'Ziggo TV',
           'Zender van de Maand',
           'Comedy Central HD',
           'Nickelodeon HD',
           'Disney Channel',
           'Discovery HD',
           'National Geographic Channel HD',
           'SBS9 HD',
           'Eurosport HD',
           'TLC HD',
           '13TH Street HD',
           'MTV HD',
           '24Kitchen HD',
           'één HD',
           'Canvas HD',
           'Ketnet',
           'BBC One HD',
           'BBC Two HD']

def switch_user(uid = None, gid = None):
  # set gid first
  if gid is not None:
    os.setgid(gid)
  if uid is not None:
    os.setuid(uid)

def daemonize():
  def fork_exit_parent():
    try:
      pid = os.fork()
      if pid > 0:
        # parent, so exit
        sys.exit(0)
    except OSError as exc:
      sys.stderr.write('failed to fork parent process {:0}\n'.format(exc))
      sys.exit(1)
  def redirect_stream(source, target = None):
    if target is None:
      target_fd = os.open(os.devnull, os.O_RDWR)
    else:
      target_fd = target.fileno()
    os.dup2(target_fd, source.fileno())

  os.umask(0)
  os.chdir('/')

  fork_exit_parent()
  os.setsid()
  fork_exit_parent()

  # redirect streams
  sys.stdout.flush()
  sys.stderr.flush()
  redirect_stream(sys.stdin)
  redirect_stream(sys.stdout)
  redirect_stream(sys.stderr)

def run_import(wanted_channels, tvhsocket):
  with TVHXMLTVSocket(tvhsocket) as tvh_client:
    chmap = ChannelMap()
    listings = Listings()
    # add listings for each of the channels
    for channel_id, channel in chmap.channel_map.items():
      if channel['title'] in wanted_channels:
        now = datetime.date.today().timetuple()
        nr = 0
        xmltv = XMLTVDocument()
        xmltv.addChannel(channel_id, channel['title'], channel['images'])
        for i in range(0, 5):
          start = int((calendar.timegm(now) + 86400 * i) * 1000) # milis
          end = start + (86400 * 1000)
          nr = nr + listings.obtain(xmltv, channel_id, start, end)
        debug('Adding {:d} programmes for channel {:s}'.format(nr, channel['title']))
        # send this channel to tvh for processing
        tvh_client.send(xmltv.document.toprettyxml(encoding='UTF-8'))

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Fetches EPG data from the Horizon service and passes it to TVHeadend.')
  parser.add_argument('-s', nargs='?', metavar='PATH', dest='tvhsocket', default='/home/hts/.hts/tvheadend/epggrab/xmltv.sock', type=str, help='path to TVHeadend XMLTV socket')
  parser.add_argument('-p', nargs='?', metavar='PATH', dest='pid_filename', default='/var/run/horepgd.pid', type=str, help='path to PID file')
  parser.add_argument('-u', nargs='?', metavar='USER', dest='as_user', default='hts', type=str, help='run as USER')
  parser.add_argument('-g', nargs='?', metavar='GROUP', dest='as_group', default='video', type=str, help='run as GROUP')
  parser.add_argument('-d', dest='daemonize', action='store_const', const=True, default=False, help='daemonize')
  args = parser.parse_args()
  
  logging.basicConfig(level=logging.DEBUG)
  if(args.daemonize):
    # switch user and do daemonization
    try:
      uid = pwd.getpwnam(args.as_user).pw_uid
      gid = grp.getgrnam(args.as_group).gr_gid
    except KeyError as exc:
      debug('Unable to find the user {0} and group {1} for daemonization'.format(args.as_user, args.as_group))
      sys.exit(1)

    pid_fd = open(args.pid_filename, 'w')

    switch_user(uid, gid)
    # switch to syslog
    logging.basicConfig(stream=logging.handlers.SysLogHandler())
    daemonize()
  else:
    pid_fd = open(args.pid_filename, 'w')

  pid = str(os.getpid())
  pid_fd.write(pid + '\n')
  pid_fd.close()

  while True:
    run_import(wanted_channels, args.tvhsocket)
    time.sleep(60*60*24)
