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
from utils import unescape
from datetime import datetime
from datetime import timedelta
from urllib import urlencode
from random import random


class VgtvApi():

    API_URL = 'http://api.vgtv.no/api/actions'
    CMS_URL = 'http://cmsapi.vgtv.no'
    PER_PAGE = 40
    plugin = None
    categories = None

    def __init__(self, plugin):
        self.plugin = plugin

    def get_api_url(self, url, params={}):
        defaults = {'formats': 'http', 'meta': 1}
        params = dict(defaults.items() + params.items())
        return self.API_URL + url + '?' + urlencode(params)

    def get_default_video_list(self, url, page, raw=False, params={}):
        if raw is False:
            offset = self.calculate_offset(page)
            params.update({'limit': self.PER_PAGE, 'offset': offset})
            url = self.get_api_url(url=url, params=params)

        response = urllib2.urlopen(url)
        return self.parse_video_response(response)

    def get_category_tree(self):
        if self.categories is not None:
            return self.categories

        url = self.CMS_URL + '/categories/drvideo-list'
        response = urllib2.urlopen(url)
        data = simplejson.loads(response.read())
        self.categories = data
        return data

    def get_categories(self, root_id=0):
        categories = self.get_category_tree()

        matches = []
        for id in categories:

            if int(id) < 0:
                continue

            category = categories.get(id)
            if (int(category.get('parentId')) == int(root_id)):
                matches.append({
                    'label': unescape(category.get('name')),
                    'path':  self.plugin.url_for('show_category', id=str(id)),
                    'id':    id
                })

        return matches

    def resolve_video_url(self, video_id):
        #url = self.get_api_url(url='/video/', params={'id': video_id})
        url = 'http://www.vgtv.no/data/actions/videostatus/?id=%s' % video_id
        response = urllib2.urlopen(url)
        data = simplejson.loads(response.read())
        return self.get_video_urls(data, allow_resolve=False)

    def parse_video_response(self, response):
        data = simplejson.loads(response.read())
        items = list()
        count = 0
        for video in data['videos']:
            vid_url, thumb_url, category_id, dur = self.get_video_urls(video)
            count += 1

            if vid_url is None:
                continue

            meta = video.get('meta')
            items.append({
                'label': unescape(meta.get('title')),
                'thumbnail': thumb_url,
                'info': {
                    'plot': unescape(meta.get('preamble') or ''),
                    'originaltitle': unescape(meta.get('title') or '???'),
                    'tagline': unescape(meta.get('preamble') or ''),
                    'aired': self.get_date(meta.get('timePublished')),
                    'duration': self.get_duration(meta.get('duration'))
                },
                'path': vid_url,
                'is_playable': True,
            })

        return items, (count < self.PER_PAGE)

    def get_video_urls(self, video, allow_resolve=True):
        highest_bitrate = 0
        best_thumb = {'width': 10000}
        best_format = None
        category_id = video.get('meta').get('category')
        video_title = video.get('meta').get('title', 'none')
        duration = str(video.get('meta').get('duration'))
        video_title = self.url_friendly(video_title.encode('utf-8'))

        # Some videos do not have a formats array
        if 'formats' not in video and allow_resolve:
            video_url = self.plugin.url_for('play_id',
                id=str(video['id']),
                category=str(category_id),
                title=video_title.encode('utf-8')
            )
            thumb_url = self.build_thumbnail_url({
                'width': 354,
                'height': 199
            }, video['id'])

            return video_url, thumb_url, category_id, duration
        elif 'formats' not in video:
            self.plugin.log.warning('Formats not in video-response')
            return None, None, None, None

        # MP4 or m3u8?
        if (allow_resolve):
            # Use MP4 by default
            format = 'mp4'
            if ('mp4' not in video['formats']['http'] and
                'm3u8' in video['formats']['http']):
                format = 'm3u8'
            elif ('mp4' not in video['formats']['http'] and
                'flv' in video['formats']['http']):
                format = 'flv'
        else:
            # Reverse order for stuff we have to resolve
            # Had some trouble getting mp4 stream to work
            format = 'm3u8'
            if ('m3u8' not in video['formats']['http'] and
                'mp4' in video['formats']['http']):
                format = 'mp4'

        # Loop through the formats to find the best one
        for format in video['formats']['http'][format]:
            # Find the highest bitrate available
            if format['bitrate'] > highest_bitrate:
                highest_bitrate = format['bitrate']
                best_format = format

            # Thumbs seem to be around ~300px in general
            if format['width'] > 310 and format['width'] < best_thumb['width']:
                best_thumb = format

        # Fall back if something failed
        if best_format is None:
            self.plugin.log.error('No format found for video %s' % video['id'])
            return None, None, None, None

        # If we didn't find a fitting thumb, use thumb from the highest bitrate
        if 'height' not in best_thumb:
            best_thumb = best_format

        video_url = self.build_video_url(best_format['paths'][0])
        video_url = self.plugin.url_for('play_url',
            url=video_url,
            category=str(category_id),
            id=str(video['id']),
            title=video_title.encode('utf-8'),
            duration=duration
        )
        thumb_url = self.build_thumbnail_url(best_thumb, video['id'])
        return video_url, thumb_url, category_id, duration

    def build_video_url(self, p):
        # p = parts
        url = 'http://%s/%s/%s' % (p['address'], p['path'], p['filename'])
        return url

    def build_thumbnail_url(self, d, id):
        # d = dimensions
        url = 'http://api.vgtv.no/images/id/' + str(id / 1000) + 'xxx/'
        url += '%s/w%dh%dc.jpg' % (id % 1000, d['width'], d['height'])
        return url

    def calculate_offset(self, page):
        return self.PER_PAGE * (int(page) - 1)

    def get_date(self, timestamp):
        return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')

    def get_duration(self, secs):
        return timedelta(seconds=secs)

    def track_play(self, id, category_id, title, resolution, duration):
        category = self.get_category(category_id)
        self.track_play_drclick(id, category)
        self.track_play_tns(id, category, resolution, title, duration)
        self.track_play_xiti(id, category, resolution, title, duration)

    def track_play_drclick(self, id, category=None):
        url = 'http://drclick.vg.no/drklikkvgtv/register/betalive.php?'
        url += 'event=videoplay&identification=' + str(id) + '&text1=vgtv-xbmc'

        if category is not None:
            url += '&text2=' + str(category)

        try:
            urllib2.urlopen(url)
        except urllib2.URLError:
            # Not being able to track is no fatal error
            pass

    def track_play_tns(self, id, category, resolution, title, duration):
        res = resolution.split('x')
        path = self.get_category_path(category)

        name = 'vgtv/' + path + '/video_' + str(id) + '_' + title

        uid = self.baseN(int(round(random() * 10000000000)), 32)

        url = 'http://vgstream.tns-cs.net/j0=,,,pl=VGTVplayerXBMC+pv=version1'
        url += '+sx=' + res[0] + '+sy=' + res[1] + ';+,name=' + name
        url += '+ct=video+uid=' + uid + '+post=,,0+0,+memlv5;+,1+12+memlv7;;'
        url += '+dur=' + str(duration) + '+vt=217;;;'

        try:
            urllib2.urlopen(url.encode('utf-8'))
        except urllib2.URLError:
            # Not being able to track is no fatal error
            pass

    def track_play_xiti(self, id, category, resolution, title, duration):
        now = datetime.now()
        category_name = category.get('title').encode('utf-8')
        title = title.encode('utf-8')
        params = {
            's': 417204,
            'p': category_name + '::' + str(id) + '_' + title,
            's2': category.get('drVideoId'),
            'type': 'video',
            'plyr': 2,
            'a': 'play',
            'm5': 'int',
            'm6': 'clip',
            'm1': duration,
            'rmp': 0,
            'rmpf': 0,
            'rmbufp': 0,
            'm3': 2,
            'm4': 16,
            'm7': 0,
            'm8': 9,
            'prich': 'VGTV-XBMC',
            's2rich': 1,
            'rfsh': 10,
            'hl': 'x'.join([str(now.hour), str(now.minute), str(now.second)]),
            'r': resolution + 'x24x24'
        }

        url = 'http://logc189.xiti.com/hit.xiti?'
        url += urlencode(params)

        try:
            urllib2.urlopen(url)
        except urllib2.URLError:
            # Not being able to track is no fatal error
            pass

    def url_friendly(self, unfriendly):
        friendly = unfriendly.decode('utf-8')
        friendly = re.sub(r'\s', r'_', friendly)
        friendly = friendly.lower()
        friendly = friendly.replace(u'\xe6', u'ae')
        friendly = friendly.replace(u'\xf8', u'oe')
        friendly = friendly.replace(u'\xe5', u'aa')
        friendly = re.sub(r'[^A-Za-z\/_0-9\-:()]', r'', friendly)
        return friendly

    def get_category(self, category_id):
        url = self.CMS_URL + '/categories/' + str(category_id)

        try:
            response = urllib2.urlopen(url)
            data = simplejson.loads(response.read())
            return data
        except urllib2.HTTPError:
            return {
                'drVideoId': 0,
                'categoryPath': None,
                'title': ''
            }
        return data

    def get_category_path(self, category):
        categoryPath = category.get('categoryPath', None)

        if categoryPath is None:
            return 'front'
        else:
            return '/'.join([p.get('name') for p in categoryPath])

    def baseN(self, num, b, numerals='0123456789abcdefghijklmnopqrstuvwxyz'):
        return ((num == 0) and numerals[0]) or (
            self.baseN(num // b, b, numerals)
            .lstrip(numerals[0]) + numerals[num % b])
