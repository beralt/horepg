# -*- coding: utf-8 -*-

"""
Fetch a list of channels from TVHeadend
"""

import requests
import socket

def tvh_get_channels(host, port=9981, username='', password=''):
  channels = []
  #r = requests.get('http://{:s}:{:d}/api/channel/list'.format(host, port), auth=(username, password))
  r = requests.get('http://{:s}:{:d}/api/channel/list'.format(host, port))
  if r.status_code != 200:
    raise Exception('connection to tvheadend failed with status {:d}'.format(r.status_code))
  data = r.json()
  if 'entries' in data:
    for channel in data['entries']:
      if 'val' in channel:
        channels.append(channel['val'])
  return channels

class TVHXMLTVSocket(object):
  def __init__(self, path):
    self.path = path
    self.sock = False
  def __enter__(self):
    return self
  def __exit__(self, type, value, traceback):
    if(self.sock):
      self.sock.close()
  def send(self, data):
    self.sock = socket.socket(socket.AF_UNIX)
    self.sock.connect(self.path)
    self.sock.sendall(data)
    self.sock.close()
