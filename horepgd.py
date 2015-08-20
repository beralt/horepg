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

from horepg import *

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

def run_import(wanted_channels):
  with TVHXMLTVSocket('/home/hts/.hts/tvheadend/epggrab/xmltv.sock') as tvh_client:
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
  logging.basicConfig(level=logging.DEBUG)
  # switch user and do daemonization
  try:
    uid = pwd.getpwnam('hts').pw_uid
    gid = grp.getgrnam('video').gr_gid
  except KeyError as exc:
    debug('Unable to find the user and group id for daemonization')
    sys.exit(1)

  switch_user(uid, gid)
  # switch to syslog
  logging.basicConfig(stream=logging.handlers.SysLogHandler())
  daemonize()

  while True:
    run_import(wanted_channels)
    time.sleep(60*60*24)
