#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#     Copyright (C) 2013 Tristan Fischer (sphere@dersphere.de)
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

import sys

from BeautifulSoup import BeautifulSoup
from urllib2 import urlopen

if sys.version_info >= (2, 7):
    import json
else:
    import simplejson as json


MAIN_URL = 'http://www.collegehumor.com/'


def get_categories():
    url = MAIN_URL
    tree = __get_tree(url)
    parent = tree.find('a', {'href': '/originals'}).parent.parent.parent
    categories = [{
        'title': a.contents[2].strip(),
        'link': a['href'][1:]
    } for a in parent.findAll('a')]
    return categories


def get_videos(category, page=1):
    url = MAIN_URL + '%s/page:%s' % (category, page)
    tree = __get_tree(url)
    parent = tree.find('div', {'class': 'primary'})
    videos = [{
        'title': article.a.img['alt'],
        'video_id': _get_video_id(article.a['href']),
        'image': article.a.img['data-src-retina']
    } for article in parent.findAll('article') if article.a]
    has_next_page = tree.find('a', {'class': 'next'})
    return videos, has_next_page


def _get_video_id(link):
    return link.split('/')[2]


def get_video_file(video_id):
    url = MAIN_URL + 'moogaloop/video/%s.json' % video_id
    video = __get_json(url)['video']
    return video['mp4'].get('high_quality') or video['mp4'].get('low_quality')


def __get_tree(url):
    response = urlopen(url).read()
    return BeautifulSoup(response, convertEntities=BeautifulSoup.HTML_ENTITIES)


def __get_json(url):
    response = urlopen(url).read()
    return json.loads(response)
