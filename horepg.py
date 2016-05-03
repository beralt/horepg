# -*- coding: utf-8 -*-

"""
Download EPG data from Horizon and output XMLTV stuff
"""

import logging
import xml.dom.minidom
import time
import datetime
import calendar
import json
import socket
import http.client

def debug(msg):
  logging.debug(msg)

def debug_json(data):
  debug(json.dumps(data, sort_keys=True, indent=4))

class XMLTVDocument(object):
  # this renames some of the channels
  add_display_name = {}
  category_map = {
    'tv drama': 'movie/drama (general)',
    'actie': 'movie/drama (general)',
    'familie': 'movie/drama (general)',
    'thriller': 'detective/thriller',
    'detective': 'detective/thriller',
    'avontuur': 'detective/thriller',
    'western': 'detective/thriller',
    'horror': 'science fiction/fantasy/horror',
    'sci-fi': 'science fiction/fantasy/horror',
    'komedie': 'comedy',
    'melodrama': 'science fiction/fantasy/horror',
    'romantiek': 'romance',
    'drama': 'serious/classical/religious/historical movie/drama',
    'erotiek': 'adult movie/drama',
    'nieuws': 'news/current affairs (general)',
    'weer': 'news/weather report',
    'nieuws documentaire': 'news magazine',
    'documentaire': 'documentary',
    'historisch': 'documentary',
    'waar gebeurd': 'documentary',
    'discussie': 'discussion/interview/debate',
    'show': 'game show/quiz/contest',
    'variété': 'variety show',
    'talkshow': 'talk show',
    'sport': 'sports (general)',
    'gevechtssport': 'martial sports',
    'wintersport': 'winter Sports',
    'paardensport': 'equestrian',
    'evenementen': 'special event',
    'sportmagazine': 'sports magazine',
    'voetbal': 'football/soccer',
    'tennis/squash': 'tennis/squash',
    'teamsporten': 'Team sports',
    'atletiek': 'athletics',
    'motorsport': 'motor sport',
    'extreme': 'motor sport',
    'watersport': 'water sport',
    'kids/jeugd': 'children\'s/youth program (general)',
    'kids 0 - 6': 'pre-school children\'s program',
    'jeugd 6 - 14': 'entertainment (6-14 year old)',
    'jeugd 10 - 16': 'entertainment (10-16 year old)',
    'poppenspel': 'cartoon/puppets',
    'educatie': 'information/educational/school program',
    'muziek': 'music/ballet/dance',
    'ballet': 'ballet',
    'easy listening': 'music/ballet/dance',
    'musical': 'musical/opera',
    'rock/pop': 'rock/pop',
    'klassiek': 'serious music/classical music',
    'volksmuziek': 'folk/traditional music',
    'jazz': 'jazz',
    'musical': 'musical/opera',
    'lifestyle': 'arts/culture (without music, general)',
    'beeldende kunst': 'performing arts',
    'mode': 'fashion',
    'kunst magazine': 'arts/culture magazines',
    'kunst/cultuur': 'arts/culture magazines',
    'religie': 'religion',
    'popart': 'popular culture/traditional arts',
    'literatuur': 'literature',
    'speelfilm': 'film/cinema',
    'shorts': 'experimental film/video',
    'special': 'broadcasting/press',
    'maatschappelijk': 'social/political issues/economics (general)',
    'actualiteiten': 'magazines/reports/documentary',
    'economie': 'economics/social advisory',
    'beroemdheden': 'remarkable people',
    'educatie': 'education/science/factual topics (general)',
    'natuur': 'nature/animals/environment',
    'technologie': 'technology/natural sciences',
    'geneeskunde': 'medicine/physiology/psychology',
    'expedities': 'foreign countries/expeditions',
    'sociologie': 'social/spiritual sciences',
    'educatie divers': 'further education',
    'talen': 'languages',
    'vrije tijd': 'leisure hobbies (general)',
    'reizen': 'tourism/travel',
    'klussen': 'handicraft',
    'auto en motor': 'motoring',
    'gezondheid': 'fitness & health',
    'koken': 'cooking',
    'shoppen': 'advertisement/shopping',
    'tuinieren': 'gardening'
    }

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
  host = 'web-api-pepper.horizon.tv'
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
  host = 'web-api-pepper.horizon.tv'
  path = '/oesp/api/NL/nld/web/listings'

  """
  Defaults to only few days for given channel
  """
  def __init__(self):
    self.conn = http.client.HTTPSConnection(Listings.host)
  def obtain(self, xmltv, channel_id, start = False, end = False, retry = True):
    if start == False:
      start = int(time.time() * 1000)
    if end == False:
      end = start + (86400 * 2 * 1000)
    self.path = Listings.path + '?byStationId=' + channel_id + '&byStartTime=' + str(start) + '~' + str(end) + '&sort=startTime'
    self.conn.request('GET', self.path)
    response = self.conn.getresponse()
    if response.status != 200:
      if retry:
        # give the server a bit of time to recover
        time.sleep(1)
        return self.obtain(xmltv, channel_id, start, end, False)
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
