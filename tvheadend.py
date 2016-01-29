# -*- coding: utf-8 -*-

"""
Fetch a list of channels from TVHeadend
"""

import http.client
import json

def tvh_get_channels(host, port=9981):
  channels = []
  conn = http.client.HTTPConnection(host, port)
  conn.request('GET', '/api/channel/list')
  response = conn.getresponse()
  if response.status != 200:
    raise Exception('connection to tvheadend failed with status {:d}'.format(response.status))
  raw = response.read()
  data = json.loads(raw.decode('utf-8'))
  if 'entries' in data:
    for channel in data['entries']:
      if 'val' in channel:
        channels.append(channel['val'])
  return channels
