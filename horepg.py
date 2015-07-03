"""
Download EPG data from Horizon and output XMLTV stuff
"""

import os
import syslog
import pwd
import grp
import xml.dom.minidom
import time
import datetime
import calendar
import sys
import json
import socket
import http.client

def debug(msg):
  syslog.syslog(msg)

def debug_json(data):
  debug(json.dumps(data, sort_keys=True, indent=4))

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

class XMLTVDocument(object):
  # this renames some of the channels
  add_display_name = {}
  category_map = {
    'nieuws': 'News / Current affairs',
    'sport': 'Sports',
    'vrije tijd': 'Leisure hobbies',
    'gezondheid': 'Fitness and health',
    'discussie': 'Discussion / Interview / Debate',
    'tv drama': 'Movie / Drama',
    'komedie': 'Comedy',
    'show': 'Show / Game show',
    'documentaire': 'Documentary'}

  def __init__(self):
    impl = xml.dom.minidom.getDOMImplementation()
    doctype = impl.createDocumentType('tv', None, 'xmltv.dtd')
    self.document = impl.createDocument(None, 'tv', doctype)
    self.document.documentElement.setAttribute('source-info-url', 'https://horizon.tv')
    self.document.documentElement.setAttribute('source-info-name', 'UPC Horizon API')
    self.document.documentElement.setAttribute('generator-info-name', 'HorEPG v1.0')
    self.document.documentElement.setAttribute('generator-info-url', 'beralt.nl/horepg')
  def addChannel(self, channel_id, display_name, icons):
    element = self.document.createElement('channel')
    element.setAttribute('id', channel_id)

    if display_name in XMLTVDocument.add_display_name:
      for name in XMLTVDocument.add_display_name[display_name]:
        dn_element = self.document.createElement('display-name')
        dn_text = self.document.createTextNode(name)
        dn_element.appendChild(dn_text)
        element.appendChild(dn_element)
    else:
      if type(display_name) == list:
        for name in display_name:
          dn_element = self.document.createElement('display-name')
          dn_text = self.document.createTextNode(name)
          dn_element.appendChild(dn_text)
          element.appendChild(dn_element)
      else:
        dn_element = self.document.createElement('display-name')
        dn_text = self.document.createTextNode(display_name)
        dn_element.appendChild(dn_text)
        element.appendChild(dn_element)

    for icon in icons:
      if icon['assetType'] == 'station-logo-large':
        lu_element = self.document.createElement('icon')
        lu_element.setAttribute('src', icon['url'])
        element.appendChild(lu_element)

    self.document.documentElement.appendChild(element)
  def addProgramme(self, programme):
    if 'program' in programme:
      if 'title' in programme['program']:
        element = self.document.createElement('programme')

        element.setAttribute('start', XMLTVDocument.convert_time(int(programme['startTime']) / 1000))
        element.setAttribute('stop',  XMLTVDocument.convert_time(int(programme['endTime']) / 1000))
        element.setAttribute('channel', programme['stationId'])

        # quick tags
        self.quick_tag(element, 'title', programme['program']['title'])
        if 'seriesEpisodeNumber' in programme['program']:
          self.quick_tag(element, 'episode-num', programme['program']['seriesEpisodeNumber'], {'system': 'onscreen'})

        # fallback to shorter descriptions
        if 'longDescription' in programme['program']:
          self.quick_tag(element, 'desc', programme['program']['longDescription'])
        elif 'description' in programme['program']:
          self.quick_tag(element, 'desc', programme['program']['description'])
        elif 'shortDescription' in programme['program']:
          self.quick_tag(element, 'desc', programme['program']['shortDescription'])

        if 'secondaryTitle' in programme['program']:
          self.quick_tag(element, 'sub-title', programme['program']['secondaryTitle'])

        # categories
        if 'categories' in programme['program']:
          for cat in programme['program']['categories']:
            if '/' not in cat['title']:
              cat_title = XMLTVDocument.map_category(cat['title'].lower())
              if cat_title:
                self.quick_tag(element, 'category', cat_title)
              else:
                self.quick_tag(element, 'category', cat['title'])

        self.document.documentElement.appendChild(element)
      else:
        debug('The program had no title')
    else:
      debug('The listing had no program')
  def map_category(cat):
    if cat in XMLTVDocument.category_map:
      return XMLTVDocument.category_map[cat]
    return False
  def quick_tag(self, parent, tag, content, attributes = False):
    element = self.document.createElement(tag)
    text = self.document.createTextNode(content)
    element.appendChild(text)
    if attributes:
      for k, v in attributes.items():
        element.setAttribute(k, v)
    parent.appendChild(element)
  def convert_time(t):
    return time.strftime('%Y%m%d%H%M%S', time.gmtime(t))

class ChannelMap(object):
  host = 'www.horizon.tv'
  path = '/oesp/api/NL/nld/web/channels/'
  
  def __init__(self):
    conn = http.client.HTTPSConnection(ChannelMap.host)
    conn.request('GET', ChannelMap.path)
    response = conn.getresponse()
    if(response.status == 200):
      raw = response.read()
    else:
      raise Exception('Failed to GET channel url')
    # load json
    data = json.loads(raw.decode('utf-8'))
    #setup channel map
    self.channel_map = {}
    for channel in data['channels']:
      for schedule in channel['stationSchedules']:
        station = schedule['station']
        self.channel_map[station['id']] = station
  def dump(self, xmltv):
    for k, v in self.channel_map.items():
      xmltv.addChannel(v['id'], v['title'])
  def lookup(self, channel_id):
    if channel_id in self.channel_map:
      return self.channel_map[channel_id]
    return False
  def lookup_by_title(self, title):
    for channel_id, channel in self.channel_map.items():
      if channel['title'] == title:
        return channel_id
    return False

class Listings(object):
  host = 'www.horizon.tv'
  path = '/oesp/api/NL/nld/web/listings'

  """
  Defaults to only few days for given channel
  """
  def __init__(self):
    self.conn = http.client.HTTPSConnection(Listings.host)
  def obtain(self, xmltv, channel_id, start = False, end = False):
    if start == False:
      start = int(time.time() * 1000)
    if end == False:
      end = start + (86400 * 2 * 1000)
    self.path = Listings.path + '?byStationId=' + channel_id + '&byStartTime=' + str(start) + '~' + str(end) + '&sort=startTime'
    self.conn.request('GET', self.path)
    response = self.conn.getresponse()
    if response.status != 200:
      raise Exception('Failed to GET listings url:', response.status, response.reason)
    return self.parse(response.read(), xmltv)
  def parse(self, raw, xmltv):
    # parse raw data
    data = json.loads(raw.decode('utf-8'))
    for listing in data['listings']:
      xmltv.addProgramme(listing)
    return len(data['listings'])

class TVHXMLTVSocket(object):
  def __init__(self, path):
    self.path = path
  def __enter__(self):
    return self
  def __exit__(self, type, value, traceback):
    self.sock.close()
  def send(self, data):
    self.sock = socket.socket(socket.AF_UNIX)
    self.sock.connect(self.path)
    self.sock.sendall(data)
    self.sock.close()

# the wanted channels
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
  # switch user and do daemonization
  try:
    uid = pwd.getpwnam('hts').pw_uid
    gid = grp.getgrnam('video').gr_gid
  except KeyError as exc:
    debug('Unable to find the user and group id for daemonization')
    sys.exit(1)

  switch_user(uid, gid)
  daemonize()

  while True:
    run_import(wanted_channels)
    time.sleep(60*60*24)
