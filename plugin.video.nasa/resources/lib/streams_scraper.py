#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#     Copyright (C) 2012 Tristan Fischer (sphere@dersphere.de)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#

import simplejson as json
from urllib import urlencode
from urllib2 import urlopen
import re

API_KEY = 'C55C5A3302BF1CA923A7B41A04E5C0F4'  # please don't steal my key
API_URL = 'http://api.ustream.tv/json/'


def get_streams(only_live=True):
    log('get_streams started')
    path = ('user', 'NASAtelevision', 'listAllChannels')
    json_data = __ustream_request(path)
    channels = []
    for channel in json_data['results']:
        if only_live and channel['status'] != 'live':
            continue
        else:
            channels.append({
                'title': channel['title'],
                'id': channel['id'],
                'description': channel['description'],
                'thumbnail': channel['imageUrl']['small']
            })
    log('get_streams finished with %d channels' % len(channels))
    return channels


def get_stream(id):
    return __generate_rtmp(id)


def __ustream_request(path):
    params = {
        'key': API_KEY,
        'limit': 50
    }
    url = API_URL + '%s?%s' % ('/'.join(path), urlencode(params))
    log('__ustream_request opening url=%s' % url)
    response = urlopen(url).read()
    log('__ustream_request finished with %d bytes result' % len(response))
    return json.loads(response)


def __generate_rtmp(id):
    log('__generate_rtmp started with id=%s' % id)
    amf_url = 'http://cdngw.ustream.tv/Viewer/getStream/1/%s.amf' % id
    response = urlopen(amf_url).read()
    tc_url = re.search('rtmp://(.+?)\x00', response).group(1)
    page_url = re.search('url\W\W\W(.+?)\x00', response).group(1)
    playpath = re.search('streamName(?:\W+)([^\x00]+)', response).group(1)
    if tc_url.count('/') > 1:
        log('__generate_rtmp guessing rtmp without verification')
        app = tc_url.split('/', 1)[1]
        swf_url = 'http://www.ustream.tv/flash/viewer.swf'
        url = (
            'rtmp://%s playpath=%s swfUrl=%s pageUrl=%s '
            'app=%s live=1' % (tc_url, playpath, swf_url, page_url, app)
        )
    else:
        log('__generate_rtmp guessing rtmp with verification')
        swf_url = urlopen('http://www.ustream.tv/flash/viewer.swf').geturl()
        url = ('rtmp://%s playpath=%s swfUrl=%s pageUrl=%s swfVfy=1 live=1'
               % (tc_url, playpath, swf_url, page_url))
    log('__generate_rtmp finished with url=%s' % url)
    return url


def log(text):
    print 'Nasa streams scraper: %s' % text
