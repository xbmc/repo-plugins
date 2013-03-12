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

import urllib2
import re
from BeautifulSoup import BeautifulSoup
from urllib import urlencode


MOBILE_URL = 'http://m.collegehumor.com/'
MAIN_URL = 'http://www.collegehumor.com/'

IPAD_USERAGENT = (
    'Mozilla/5.0 (iPad; U; CPU OS 3_2 like Mac OS X; en-us) '
    'AppleWebKit/531.21.10 (KHTML, like Gecko) '
    'Version/4.0.4 Mobile/7B334b Safari/531.21.10'
)


def get_categories():
    url = MOBILE_URL + 'videos/browse'
    tree = __get_tree(url, mobile=True)
    categories = []
    for a in tree.find('ul', {'data-role': 'listview'}).findAll('a'):
        if 'playlist' in a['href']:
            print 'Skipping Playlist'
            continue
        elif 'video' in a['href']:
            print 'Skipping'
            continue
        categories.append({
            'title': a.string,
            'link': a['href'][1:]
        })
    return categories


def get_videos(category, page=1):
    post = {'render_mode': 'ajax'}
    url = MOBILE_URL + '%s/page:%s' % (category, page)
    tree = __get_tree(url, post, mobile=True)
    videos = []
    elements = tree.find('ul', {'data-role': 'listview'}).findAll('a')
    for a in elements:
        if 'playlist' in a['href']:
            print 'Skipping Playlist'
            continue
        videos.append({
            'title': a.h3.string,
            'link': a['href'][1:],
            'image': a.img['src']
        })
    has_next_page = len(elements) == 24
    return videos, has_next_page


def get_video_file(link):
    url = MAIN_URL + link
    tree = __get_tree(url)

    video_object = tree.find('video')
    if video_object and video_object.get('src'):
        return video_object['src']

    re_flv = re.compile("flvSourceUrl: '([^']+)',")
    js_code = tree.find('script', {'type': 'text/javascript'},
                        text=re_flv)
    if js_code:
        flv_url = re.search(re_flv, js_code).group(1)
        return flv_url


def __get_tree(url, data_dict=None, mobile=True):
    print 'Opening url: %s' % url
    if data_dict:
        post_data = urlencode(data_dict)
    else:
        post_data = ' '
    req = urllib2.Request(url, post_data)
    if mobile:
        req.add_header('Cookie', 'force_mobile=1')
        req.add_header('User-Agent', IPAD_USERAGENT)
    req.add_header('X-Requested-With', 'XMLHttpRequest')
    response = urllib2.urlopen(req).read()
    tree = BeautifulSoup(response, convertEntities=BeautifulSoup.HTML_ENTITIES)
    return tree
