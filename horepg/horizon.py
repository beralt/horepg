# -*- coding: utf-8 -*-

"""
Download EPG data from Horizon and output XMLTV stuff
"""

import logging
import time
import json
import http.client

def debug(msg):
    logging.debug(msg)

def debug_json(data):
    debug(json.dumps(data, sort_keys=True, indent=4))

class HorizonRequest(object):
    hosts = ['web-api-salt.horizon.tv', 'web-api-pepper.horizon.tv']

    def __init__(self):
        self.current = 0
        self.connection = http.client.HTTPSConnection(HorizonRequest.hosts[self.current])

    def request(self, method, path, retry=True):
        self.connection.request(method, path)
        response = self.connection.getresponse()
        if response.status == 500:
            debug('Failed to request data from Horizon API, HTTP status {:0}'.format(response.status))
            debug('Waiting for 5 seconds before trying again !')
            time.sleep(5)
            self.connection = http.client.HTTPSConnection(HorizonRequest.hosts[self.current])
            return self.request(method, path, retry=True)
        if response.status == 200:
            return response
        elif response.status == 403:
            # switch hosts
            debug('Switching hosts')
            if self.current == 0:
                self.current = 1
            else:
                self.current = 0
            self.connection = http.client.HTTPSConnection(HorizonRequest.hosts[self.current])
            if retry:
                return self.request(method, path, retry=False)
        else:
            debug('Failed to request data from Horizon API, HTTP status {:0}'.format(response.status))
        return response

class ChannelMap(object):
    path = '/oesp/api/NL/nld/web/channels/'

    def __init__(self):
        self.horizon_request = HorizonRequest()
        response = self.horizon_request.request('GET', ChannelMap.path)
        if response:
            raw = response.read()
        else:
            raise Exception('Failed to get data from Horizon API, HTTP status {:d}'.format(response.status))
        # load json
        data = json.loads(raw.decode('utf-8'))
        #setup channel map
        self.channel_map = {}
        for channel in data['channels']:
            for schedule in channel['stationSchedules']:
                station = schedule['station']
                self.channel_map[station['id']] = station
    def dump(self, xmltv):
        for key, value in self.channel_map.items():
            xmltv.addChannel(value['id'], value['title'])
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
    path = '/oesp/api/NL/nld/web/listings'

    """
    Defaults to only few days for given channel
    """
    def __init__(self):
        self.horizon_request = HorizonRequest()
    def obtain(self, xmltv, channel_id, start=False, end=False):
        if not start:
            start = int(time.time() * 1000)
        if not end:
            end = start + (86400 * 2 * 1000)
        path = Listings.path + '?byStationId=' + channel_id + '&byStartTime=' + str(start) + '~' + str(end) + '&sort=startTime'
        response = self.horizon_request.request('GET', path)
        if response:
            return parse(response.read(), xmltv)
        else:
            raise Exception('Failed to GET listings url:', response.status, response.reason)

def parse(raw, xmltv):
    # parse raw data
    data = json.loads(raw.decode('utf-8'))
    invalid = 0
    for listing in data['listings']:
        if not 'program' in listing:
            debug('Listing has no programme field')
            continue
        if not 'title' in listing['program']:
            debug('Listing has programme, but programme has no title')
            continue
        if 'geen info beschikbaar' == listing['program']['title'].lower():
            debug('Listing has programme, but programme has invalid title')
            invalid = invalid + 1
            continue

        start = int(listing['startTime']) / 1000
        end = int(listing['endTime']) / 1000
        channel_id = listing['stationId']
        title = listing['program']['title']

        if 'longDescription' in listing['program']:
            description = listing['program']['longDescription']
        elif 'description' in listing['program']:
            description = listing['program']['description']
        elif 'shortDescription' in listing['program']:
            description = listing['program']['shortDescription']
        else:
            description = None

        if 'seriesEpisodeNumber' in listing['program']:
            episode = listing['program']['seriesEpisodeNumber']
        else:
            episode = None

        if 'secondaryTitle' in listing['program']:
            episode_title = listing['program']['secondaryTitle']
        else:
            episode_title = None

        categories = []
        if 'categories' in listing['program']:
            for cat in listing['program']['categories']:
                categories.append(cat['title'])

        xmltv.addProgramme(channel_id, title, start, end, episode, episode_title, description, categories)
    return len(data['listings']) - invalid
