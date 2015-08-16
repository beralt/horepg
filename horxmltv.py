from horepg import *

# the wanted channels
wanted_channels = ['NPO 1 HD']

if __name__ == '__main__':
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
      
f = open( 'tvguide.xml', 'w', encoding='UTF-8' )
f.write( xmltv.document.toprettyxml() )
f.close()
