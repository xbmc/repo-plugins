#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2012-2013 Espen Hovlandsdal
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


# This module contains helper functions that interact with the VGTV.no JSON API

import simplejson
import urllib2
import re
import math
from utils import unescape
from datetime import datetime
from urllib import urlencode
from urllib import quote
from random import random
from xbmcswift2 import xbmc

class VgtvApi():

    API_URL = 'http://svp.vg.no/svp/api/v1/vgtv'
    PER_PAGE = 40
    plugin = None
    categories = None

    def __init__(self, plugin):
        self.plugin = plugin

    def do_request(self, url):
        req = urllib2.Request(url)
        req.add_header('Accept', 'application/json')
        return urllib2.urlopen(req)

    def get_api_url(self, url, params={}):
        defaults = {'appName': 'vgtv-kodi'}
        params = dict(defaults.items() + params.items())
        return self.API_URL + url + '?' + urlencode(params)

    def get_default_video_list(self, url, page, raw=False, params={}):
        if raw is False:
            offset = self.calculate_offset(page)
            params.update({'limit': self.PER_PAGE, 'offset': offset})
            url = self.get_api_url(url=url, params=params)

        response = self.do_request(url)
        return self.parse_video_response(response)

    def get_category_tree(self):
        if self.categories is not None:
            return self.categories

        url = self.get_api_url(url='/categories', params={'additional': 'true'})
        
        response = self.do_request(url)
        
        self.categories = self.parse_categories(response)
        return self.categories

    def get_categories(self, root_id=0, only_series=False):
        categories = self.get_category_tree()
        root = int(root_id)

        matches = []
        for category in categories:
            id = category.get('id')
            
            if category.get('showCategory') is False:
                continue

            if only_series is True and category.get('isSeries') is not True:
                continue

            if only_series is False and category.get('parentId') != root:
                continue
            
            matches.append({
                'label': unescape(category.get('title')),
                'path':  self.plugin.url_for(
                    'show_category',
                    id=str(id),
                    mode='all'
                ),
                'id':    id
            })

        return matches

    def get_category(self, category_id):
        categories = self.get_category_tree()
        
        for category in categories:
            if str(category.get('id')) == str(category_id):
                return category

    def get_series(self):
        return self.get_categories(only_series=True)

    def parse_categories(self, response):
        data = simplejson.loads(response.read())
        categories = list()

        for category in data['_embedded']['categories']:
            meta = category.get('additional')
            categories.append({
                'id': category.get('id'),
                'parentId': category.get('parentId'),
                'title': category.get('title'),
                'isSeries': category.get('isSeries'),
                'showCategory': category.get('showCategory'),
                'description': meta.get('description'),
                'stats': category.get('stats', '0'),
                'image': self.build_thumbnail_url(meta)
            })

        return categories

    def parse_video_response(self, response):
        data = simplejson.loads(response.read())
        items = list()
        count = 0

        if 'assets' in data:
            assets = data['assets']
        elif '_embedded' in data and 'assets' in data['_embedded']:
            assets = data['_embedded']['assets']
        else:
            return items, True

        for video in assets:
            vid_url, thumb_url, category_id, dur = self.get_video_urls(video)
            count += 1

            if vid_url is None:
                continue

            #tag = self.get_episode_tag(video.get('series'))
            tag = ''
            duration = video.get('duration', 0)
            
            if duration > 1000:
                duration = math.ceil(duration / 1000)

            items.append({
                'label': tag + video.get('title'),
                'thumbnail': thumb_url,
                'info': {
                    'plot': video.get('description') or '',
                    'originaltitle': video.get('title') or '???',
                    'tagline': video.get('descriptionFront') or '',
                    'aired': self.get_date(video.get('published')),
                    'duration': self.get_duration(duration)
                },
                'stream_info': {
                    'video': {
                        'duration': duration
                    }
                },
                'path': vid_url,
                'is_playable': True,
            })

        return items, (count < self.PER_PAGE)

    def get_episode_tag(self, series_info):
        if series_info is None:
            return ''
        
        episodeTag  = 'S' + str(series_info['seasonNumber'])
        episodeTag += 'E' + str(series_info['episodeNumber'])
        
        return '[' + episodeTag + '] '

    def get_video_urls(self, video, allow_resolve=True):
        category_id = video.get('category').get('id')
        video_title = video.get('title', 'none')
        duration = str(video.get('duration'))
        video_title = video_title

        # Some videos do not have a formats array
        if 'streamUrls' not in video:
            # Can't find any http URL, probably protected
            return None, None, None, None

        if video['streamUrls']['hls'] is not None:
            format = 'hls'
        elif video['streamUrls']['mp4'] is not None:
            format = 'mp4'
        else:
            return None, None, None, None

        video_url = video['streamUrls'].get(format)

        # Unfortunately, some videos are secure and cant be played with XBMC
        if 'secure' in video_url:
            return None, None, None, None

        video_url = self.plugin.url_for('play_url',
            url=video_url,
            category=str(category_id),
            id=str(video['id']),
            title=quote(video_title.encode('utf-8')),
            duration=duration
        )
        thumb_url = self.build_thumbnail_url(video)
        return video_url, thumb_url, category_id, duration

    def build_thumbnail_url(self, video):
        qs = '?t[]=640x360q80'
        
        if 'image' in video and video['image'] is not None:
            return video['image'] + qs
        elif 'images' in video and 'main' in video['images']:
            return video['images']['main'] + qs
        
        return None

    def calculate_offset(self, page):
        return self.PER_PAGE * (int(page) - 1)

    def get_date(self, timestamp):
        return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')

    def get_duration(self, secs):
        return str(secs / 60)

    def track_play(self, id, category_id, title, resolution, duration, uid):
        category = self.get_category(category_id)
        self.track_play_click(id, category)
        self.track_site_tns(id, resolution, title, uid)
        self.track_play_tns(id, category, resolution, title, duration, uid)
        self.track_play_xiti(id, category, resolution, title, duration, uid)

    def track_play_click(self, id, category=None):
        url = 'http://click.vgnett.no/svp.gif?s=vgtv&d=desktop'
        url += '&v=' + str(id) + '&p=-1&cb=' + str((random() * 10000))

        try:
            response = self.do_request(url)
        except urllib2.URLError:
            # Not being able to track is no fatal error
            pass

    def track_site_tns(self, id, resolution, title, uid):
        title = title.replace(u':', u'')
        title = self.url_friendly(title)

        url = 'http://vg.tns-cs.net/j0=,,,;+,cp=vgnett%2Fvgtv+url='
        url += 'http%3A%2F%2Fwww.vgtv.no%2F%23!%2Fvideo%2F' + str(id) + '%2F'
        url += title + ';;;?lt=igqdo00o&x=' + resolution + 'x24&c=' + uid

        try:
            response = self.do_request(url)
        except urllib2.URLError:
            # Not being able to track is no fatal error
            pass

    def track_play_tns(self, id, category, resolution, title, duration, uid):
        res = resolution.split('x')
        title = self.url_friendly(title)

        name = category.get('stats') + '/'
        name += self.url_friendly(category.get('title'))
        name += '/video_' + str(id) + '_' + quote(title)

        vid = self.baseN(int(round(random() * 10000000000)), 32)

        url = 'http://vgstream.tns-cs.net/j0=,,,pl=VGTVplayer+pv=version1'
        url += '+sx=' + res[0] + '+sy=' + res[1] + ';+,name=' + name
        url += '+ct=video+uid=' + vid + '+pst=,,0+1+nxhrtl;;'
        url += '+dur=' + str(duration) + '+vt=2;;;?lt=igqdovem&c=' + uid

        try:
            response = self.do_request(url)
        except urllib2.URLError:
            # Not being able to track is no fatal error
            pass

    def track_play_xiti(self, id, category, resolution, title, duration, uid):
        now = datetime.now()
        title = re.sub(r'\s+', r'_', title)
        category_name = re.sub(r'\s+', r'_', category.get('title'))
        portal = 'Portal::' + str(id) + '|' + title
        page = category_name + '::' + str(id) + '|' + title + '::' + portal

        params = {
            's': 550781,
            'idclient': str(int(uid, 16) / 100000)[:18],
            's2': str(category.get('stats')),
            'p': page,
            'lng': 'en-US',
            'idp': self.get_xiti_idp(),
            'jv': '1',
            're': resolution,
            'vtag': '4.5.8',
            'hl': 'x'.join([str(now.hour), str(now.minute), str(now.second)]),
            'r': resolution + 'x24x24',
            'ref': ''
        }

        url = 'http://logc189.xiti.com/hit.xiti?'
        url += urlencode(params)

        try:
            response = self.do_request(url)
        except urllib2.URLError:
            # Not being able to track is no fatal error
            pass

    def url_friendly(self, unfriendly):
        friendly = unfriendly.decode('utf-8')
        friendly = friendly.lower()
        friendly = friendly.replace(u'\xe6', u'ae')
        friendly = friendly.replace(u'\xf8', u'oe')
        friendly = friendly.replace(u'\xe5', u'aa')
        friendly = re.sub(r'[^A-Za-z\/_0-9\-:()]+', r'-', friendly)
        friendly = re.sub(r'\-+', r'-', friendly)
        return friendly

    def baseN(self, num, b, numerals='0123456789abcdefghijklmnopqrstuvwxyz'):
        return ((num == 0) and numerals[0]) or (
            self.baseN(num // b, b, numerals)
            .lstrip(numerals[0]) + numerals[num % b])

    def pad(self, a):
        if (a < 10):
            return '0' + str(a)
        else:
            return str(a)

    def get_xiti_idp(self):
        now = datetime.now()
        idp = ''.join(map(self.pad, [now.hour, now.minute, now.second]))
        return idp + str(int(math.floor(random() * 10000000)))
