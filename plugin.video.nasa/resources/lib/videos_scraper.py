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

import json
import datetime
from urllib import urlencode
from urllib2 import urlopen, Request
import re

USER_AGENT = (
    'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/535.7 '
    '(KHTML, like Gecko) Chrome/16.0.912.77 Safari/535.7'
)

REFERER = 'http://www.nasa.gov/multimedia/videogallery/index.html'

API_URL = 'http://cdn-api.vmixcore.com/apis/media.php'

VIDEO_LANDING_URL = (
    'http://www.nasa.gov/multimedia/'
    'videogallery/vmixVideoLanding2.js'
)


class Scraper(object):

    def __init__(self, force_refresh=False):
        self.force_refresh = force_refresh
        self.requests = {}
        self.atoken = self.__get_atoken()

    def get_video_topics(self):
        log('get_video_topics started')
        url = VIDEO_LANDING_URL
        r_genre_names = re.compile('var genreNames=\[(.+?)\];')
        r_genre_ids = re.compile('var genreIds=\[(.+?)\];')
        html = self.__get_url(url)
        genre_names = re.search(r_genre_names, html).group(1).split(',')
        genre_ids = re.search(r_genre_ids, html).group(1).split(',')
        video_topics = []
        for genre_id, genre_name in zip(genre_ids, genre_names):
            video_topics.append({
                'id': genre_id,
                'name': genre_name.strip("'")
            })
        log('get_video_topics got %d topics' % len(video_topics))
        return video_topics

    def get_videos_by_topic_id(self, topic_id, start=0, limit=15,
                               order_method=None, order=None):
        log('get_videos_by_topic_id started with topic_id=%s' % topic_id)
        if order_method is None or order_method not in ('DESC', 'ASC'):
            order_method = 'DESC'
        if order is None:
            order = 'date_published_start'
        if start < 0:
            start = 0
        if limit < 0 or limit > 250:
            limit = 15
        params = {
            'action': 'getMediaList',
            'class_id': 1,
            'alltime': 1,
            'order_method': order_method,
            'order': order,
            'get_count': 1,
            'export': 'JSONP',
            'start': start,
            'limit': limit,
            'metadata': 1,
            'atoken': self.atoken
        }
        if int(topic_id) < 1000:  # just a guess...
            params['external_genre_ids'] = topic_id
        else:
            params['genre_ids'] = topic_id
        videos = self.__get_videos(params)
        log('get_videos_by_topic_id finished with %d videos' % len(videos))
        return videos

    def search_videos(self, query, fields=None, start=0, limit=15):
        log('search_videos started with query=%s' % query)
        if start < 0:
            start = 0
        if limit < 0 or limit > 250:
            limit = 15
        if fields is None:
            fields = ['title', ]
        params = {
            'action': 'searchMedia',
            'class_id': 1,
            'get_count': 1,
            'export': 'JSONP',
            'start': start,
            'limit': limit,
            'metadata': 1,
            'atoken': self.atoken,
            'fields': ','.join(fields),
            'query': query
        }
        videos = self.__get_videos(params)
        log('search_videos finished with %d videos' % len(videos))
        return videos

    def __get_videos(self, params):
        url = API_URL
        html = self.__get_url(url, get_dict=params)
        json = self.__get_json(html)
        items = json.get('media') or json.get('medias', {}).get('media', [])
        videos = [{
            'title': item['title'],
            'duration': self.__format_duration(item['duration']),
            'thumbnail': item['thumbnail'][0]['url'],
            'description': item['description'],
            'date': self.__format_date(item['date_published_start']),
            'filesize': int(item['formats']['format'][-1]['filesize']),
            'author': item['author'],
            'genres': [g['name'] for g in item.get('genres', [])],
            'id': item['id'],
        } for item in items]
        total_count = json['total_count']
        return videos, total_count

    def get_video(self, id):
        log('get_video started with id=%s' % id)
        params = {
            'action': 'getMedia',
            'media_id': id,
            'atoken': self.atoken
        }
        url = API_URL
        html = self.__get_url(url, get_dict=params)
        media = self.__get_json(html)
        token = media['formats']['format'][-1]['token']
        signature = self.__get_nasa_signature(token)
        timestamp = self.__get_timestamp()
        p = 'token=%s&expires=%s&signature=%s' % (token, timestamp, signature)
        download_url = 'http://media.vmixcore.com/vmixcore/download?%s' % p
        video = {
            'title': media['title'],
            'thumbnail': media['thumbnail'][0]['url'],
            'url': download_url
        }
        log('get_video finished')
        return video

    def __get_nasa_signature(self, token):
        sig_url = (
            'http://hscripts.vmixcore.com/clients/nasa/'
            'generate_signature.php?token=%s' % token
        )
        t = self.__get_url(sig_url)
        r_sig = re.compile('"signature":"(.+?)"')
        signature = re.search(r_sig, t).group(1)
        return signature

    def __get_atoken(self):
        if self.force_refresh:
            url = VIDEO_LANDING_URL
            r_atoken = re.compile('var atoken = \'(.+?)\';')
            html = self.__get_url(url)
            atoken = re.search(r_atoken, html).group(1)
            log('retrieved atoken: %s' % atoken)
        else:
            atoken = 'cf15596810c05b64c422e071473549f4'
        return atoken

    def __get_timestamp(self):
        if self.force_refresh:
            url = VIDEO_LANDING_URL
            r_timestamp = re.compile('var timestamp = \'(.+?)\';')
            html = self.__get_url(url)
            timestamp = re.search(r_timestamp, html).group(1)
            log('retrieved timestamp: %s' % timestamp)
        else:
            timestamp = '1325444582134'
        return timestamp

    def __get_url(self, url, get_dict='', post_dict=''):
        log('__get_url started with url=%s, get_dict=%s, post_dict=%s'
            % (url, get_dict, post_dict))
        uid = '%s-%s-%s' % (url, urlencode(get_dict), urlencode(post_dict))
        if uid in self.requests.keys():
            log('__get_url using cache for url=%s' % url)
            response = self.requests[uid]
        else:
            if get_dict:
                full_url = '%s?%s' % (url, urlencode(get_dict))
            else:
                full_url = url
            req = Request(full_url)
            req.add_header('User-Agent', USER_AGENT)
            req.add_header('Referer', REFERER)
            log('__get_url opening url=%s' % full_url)
            if post_dict:
                response = urlopen(req, urlencode(post_dict)).read()
            else:
                response = urlopen(req).read()
            self.requests[uid] = response
            log('__get_url finished with %d bytes result' % len(response))
        return response

    def __get_json(self, html):
        return json.loads(html)

    def __format_duration(self, seconds_str):
        '''returns 'HH:MM:SS' '''
        return str(datetime.timedelta(seconds=int(seconds_str)))

    def __format_date(self, date_str):
        '''returns 'DD.MM.YYY' '''
        # there is a python/xbmc bug which prevents using datetime twice
        # so doing it ugly :(
        year, month, day = date_str[0:10].split('-')
        return '%s.%s.%s' % (day, month, year)


def log(text):
    print 'Nasa videos scraper: %s' % text
