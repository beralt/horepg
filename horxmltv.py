#!/usr/bin/env python
# -*- coding: utf-8 -*-

from horepg.horizon import *
import logging

# the wanted channels
wanted_channels = ['TV Oost', 'ARD HD', '13TH Street HD', 'ZDF HD']

logging.basicConfig(level=logging.DEBUG)

if __name__ == '__main__':
  with open('tvguide.xml', 'w', encoding='UTF-8') as fd:
    print('Running horepg')
    chmap = ChannelMap()
    listings = Listings()
    xmltv = XMLTVDocument()
    # add listings for each of the channels
    for channel_id, channel in chmap.channel_map.items():
      if channel['title'] in wanted_channels:
        nr = 0
        now = datetime.date.today().timetuple()
        xmltv.addChannel(channel_id, channel['title'], channel['images'])
        for i in range(0, 5):
          start = int((calendar.timegm(now) + 86400 * i) * 1000) # milis
          end = start + (86400 * 1000)
          nr = nr + listings.obtain(xmltv, channel_id, start, end)
        debug('Added {:d} programmes for channel {:s}'.format(nr, channel['title']))
    fd.write(xmltv.document.toprettyxml())
