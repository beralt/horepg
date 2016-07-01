# -*- coding: utf-8 -*-

"""
 Parse data from oorboekje.nl
"""

import http.client
import time
import logging

from html.parser import HTMLParser
from .xmltvdoc import *
from .tvheadend import *

def debug(msg):
  logging.debug(msg)

class OorboekjeParser(HTMLParser):
  STATE_INITIAL = 0
  STATE_NEW_CHANNEL = 1
  STATE_NEW_CHANNEL_TITLE = 2
  STATE_NEW_PROGRAMME = 3
  STATE_NEW_PROGRAMME_TIME = 4
  STATE_NEW_PROGRAMME_TITLE = 5
  STATE_NEW_PROGRAMME_WAIT_DESCR = 6
  STATE_NEW_PROGRAMME_DESCR = 7

  day_map = ['maandag', 'dinsdag', 'woensdag', 'donderdag', 'vrijdag', 'zaterdag', 'zondag']

  def __init__(self):
    self.setup()
    self.xmltvdoc = XMLTVDocument()
    super().__init__()

  def setup(self):
    self.state = OorboekjeParser.STATE_INITIAL
    self.current_channel = None
    self.current_programme_time = None
    self.current_programme_title = None
    self.current_programme_descr = None
    now = time.localtime()
    self.previous_programme_time = time.mktime((now.tm_year, now.tm_mon, now.tm_mday, 0, 0, 0, now.tm_wday, now.tm_yday, now.tm_isdst))
    self.previous_programme_title = None
    self.previous_programme_descr = None

    self.oor_add_days = 0
    self.prev_oor_hour = 0

  def get_day(self, for_timestamp = False):
    if(not for_timestamp):
      for_timestamp = time.time()
    else:
      now = time.time()
      if(for_timestamp - now < 0):
        raise Exception('Unable to get data for the past')

    # extract day of week, and map to dutch equivalent
    self.target = time.gmtime(for_timestamp)
    wday = OorboekjeParser.day_map[self.target.tm_wday]
    debug('getting data for {:}'.format(wday))
    # form url
    connection = http.client.HTTPConnection('oorboekje.nl')
    connection.request('GET', '/radiogids/{:}'.format(wday))
    response = connection.getresponse()
    raw = response.read()
    self.feed(raw.decode('iso-8859-1'))
    return self.xmltvdoc.document.toprettyxml(encoding='UTF-8')

  def handle_starttag(self, tag, attrs):
    # always allow the detection of a new channel
    if(tag == 'div'):
      for (name, value) in attrs:
        if(name == 'class' and value == 'pgMenuKop'):
          self.state = OorboekjeParser.STATE_NEW_CHANNEL

    if(self.state == OorboekjeParser.STATE_NEW_CHANNEL):
      if(tag == 'div'):
        # handled in data
        self.state = OorboekjeParser.STATE_NEW_CHANNEL_TITLE
    elif(self.state == OorboekjeParser.STATE_NEW_PROGRAMME):
      if(tag == 'div'):
        for (name, value) in attrs:
          if(name == 'class' and value == 'pgProgOmschr'):
            self.state = OorboekjeParser.STATE_NEW_PROGRAMME_TIME
    elif(self.state == OorboekjeParser.STATE_NEW_PROGRAMME_TIME):
      if(tag == 'b'):
        self.state = OorboekjeParser.STATE_NEW_PROGRAMME_TITLE
    elif(self.state == OorboekjeParser.STATE_NEW_PROGRAMME_WAIT_DESCR):
      if(tag == 'br'):
        self.state = OorboekjeParser.STATE_NEW_PROGRAMME_DESCR
    else:
      pass

  def handle_endtag(self, tag):
    if(self.state == OorboekjeParser.STATE_NEW_PROGRAMME_WAIT_DESCR and tag == 'div'):
      # allow skipping of the description
      self.finish_programme()
  
  def oortime_to_timestamp(self, oor):
    hourmin = oor.split(':', 2)
    cur_oor_hour = int(hourmin[0])
    if(cur_oor_hour < self.prev_oor_hour):
      # this is actually the next day
      self.oor_add_days = 1
    self.prev_oor_hour = cur_oor_hour
    return time.mktime((self.target.tm_year, self.target.tm_mon, self.target.tm_mday + self.oor_add_days, int(hourmin[0]), int(hourmin[1]), 0, self.target.tm_wday, self.target.tm_yday, self.target.tm_isdst))
    
  def handle_data(self, data):
    if(self.state == OorboekjeParser.STATE_NEW_CHANNEL_TITLE):
      self.current_channel = data.strip()
      self.xmltvdoc.addChannel(self.current_channel, self.current_channel)
      self.state = OorboekjeParser.STATE_NEW_PROGRAMME
    elif(self.state == OorboekjeParser.STATE_NEW_PROGRAMME_TIME):
      if('-' in data):
        self.current_programme_time = data.strip()
      elif(':' in data):
        self.current_programme_time = self.oortime_to_timestamp(data.strip())
      else:
        # this is not a very valid programme
        self.state = OorboekjeParser.STATE_NEW_PROGRAMME
    elif(self.state == OorboekjeParser.STATE_NEW_PROGRAMME_TITLE):
      self.current_programme_title = data.strip()
      self.state = OorboekjeParser.STATE_NEW_PROGRAMME_WAIT_DESCR
    elif(self.state == OorboekjeParser.STATE_NEW_PROGRAMME_DESCR):
      self.current_programme_descr = data.strip()
      self.finish_programme()

  def finish_programme(self):
    if(type(self.current_programme_time) == str and '-' in self.current_programme_time):
      # this is the last programme of the day, having the end time attached to it
      times = self.current_programme_time.split('-', 2)
      self.xmltvdoc.addProgramme(self.current_channel, self.current_programme_title, self.oortime_to_timestamp(times[0].strip()), self.oortime_to_timestamp(times[1].strip()), description = self.current_programme_descr)
      # clear out!
      self.setup()
    elif(self.previous_programme_title):
      # push the previous programme
      self.xmltvdoc.addProgramme(self.current_channel, self.previous_programme_title, self.previous_programme_time, self.current_programme_time, description = self.previous_programme_descr)
    self.previous_programme_time = self.current_programme_time
    self.previous_programme_title = self.current_programme_title
    self.previous_programme_descr = self.current_programme_descr
    self.current_programme_time = None
    self.current_programme_title = None
    self.current_programme_descr = None
    self.state = OorboekjeParser.STATE_NEW_PROGRAMME

logging.basicConfig(level=logging.DEBUG)

def run_import():
  parser = OorboekjeParser()
  for i in range(0, 3):
    start = time.time() + i*86400 + 100
    print(parser.get_day(start))

if __name__ == '__main__':
  run_import()
