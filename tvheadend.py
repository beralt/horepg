# -*- coding: utf-8 -*-

"""
Fetch a list of channels from TVHeadend
"""

import requests

def tvh_get_channels(host, port=9981, username='', password=''):
  channels = []
  r = requests.get('http://{:s}:{:d}/api/channel/list'.format(host, port), auth=(username, password))
  if r.status_code != 200:
    raise Exception('connection to tvheadend failed with status {:d}'.format(r.status_code))
  data = r.json()
  if 'entries' in data:
    for channel in data['entries']:
      if 'val' in channel:
        channels.append(channel['val'])
  return channels
