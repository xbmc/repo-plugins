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

import re
import simplejson as json
from urllib2 import urlopen, Request, HTTPError, URLError


MAIN_URL = 'http://www.netzkino.de/capi/'
MOVIE_URL = ('http://mf.netzkinomobil.c.nmdn.net/netzkino_mobil'
             '/_definst_/mp4:%s/playlist.m3u8')
RTMP_URL = 'rtmp://mf.netzkino.c.nmdn.net/netzkino/_definst_/mp4:%s'

VISIBLE_CATEGORIES = (
    ('81', 'Neu bei Netzkino'),
    ('61', 'HD-Kino'),
    ('39', 'Starkino'),
    ('1', 'Actionkino'),
    ('4', 'Dramakino'),
    ('32', 'Thrillerkino'),
    ('18', 'Liebesfilmkino'),
    ('6', 'Scifikino'),
    ('51', 'Arthousekino'),
    ('31', 'Queerkino'),
    ('3', 'Spasskino'),
    ('10', 'Asiakino'),
    ('5', 'Horrorkino'),
    ('33', 'Klassikerkino'),
    ('34', 'Westernkino'),
    ('71', 'Kino ab 18'),
    #'35: Familienkino',
    #'8: Highlights',
    #'37: IPTV',
    #'36: Kultkino',
    #'38: Ladykino',
    #'91: OV - Kino',
    #'41: Trashkino',
    #'9: Blog',
)


class NetworkError(Exception):
    pass


class NetzkinoApi():

    def get_categories(self, from_net=False):
        if from_net:
            data = self.__get_json(
                url=MAIN_URL,
                path='get_category_index'
            )
            items = [{
                'id': item['id'],
                'title': item.get('title'),
            } for item in data.get('categories', [])]
        else:
            items = [{
                'id': category_id,
                'title': title,
            } for category_id, title in VISIBLE_CATEGORIES]
        return items

    def get_movies(self, category_id, movie_count=500):

        def clean_tags(bad_str):
            bad_str = re.sub(r'<[^>]*?>', '', bad_str)
            return bad_str.replace('&#8211;', '-')

        def get_image(attachments_list):
            for item in attachments_list:
                if item.get('url', '') != '':
                    return item['url']

        path = (
            'get_category_posts'
            '?count=%(movie_count)d'
            '&id=%(category_id)d'
            '&custom_fields=Streaming'
            #'&include=id,title,attachments,content,modified'
        ) % {
            'category_id': int(category_id),
            'movie_count': int(movie_count)
        }
        data = self.__get_json(
            url=MAIN_URL,
            path=path
        )
        movies = []
        for item in data['posts']:
            if not item.get('custom_fields', {}).get('Streaming'):
                continue
            movies.append({
                'id': item['id'],
                'title': clean_tags(item.get('title_plain')),
                'content': clean_tags(item.get('content')),
                'modified': item.get('modified'),
                'image': (
                    item.get('thumbnail') or
                    get_image(item.get('attachments', []))
                ),
                'stream_path': item['custom_fields']['Streaming'][0]
            })
        return movies

    def get_stream_url(self, stream_path):
        return MOVIE_URL % stream_path

    def get_rtmp_url(self, stream_path):
        return RTMP_URL % stream_path

    def __get_json(self, url, path=None):
        if path:
            url += path
        req = Request(url)
        print 'Opening URL: %s' % url
        try:
            response = urlopen(req).read()
        except HTTPError, error:
            raise NetworkError('HTTPError: %s' % error)
        except URLError, error:
            raise NetworkError('URLError: %s' % error)
        print 'got %d bytes result' % len(response)
        json_data = json.loads(response)
        return json_data
