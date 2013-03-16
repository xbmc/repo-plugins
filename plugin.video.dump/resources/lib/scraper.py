#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#     Copyright (C) 2013 Tristan Fischer
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

from urllib import quote
from urllib2 import urlopen, Request, HTTPError, URLError
import re
from datetime import datetime
from base64 import b64decode
from BeautifulSoup import BeautifulSoup

MAIN_URL = 'http://dump.com/'

MONTHS = {
    'Jan': 1,
    'Feb': 2,
    'Mar': 3,
    'Apr': 4,
    'May': 5,
    'Jun': 6,
    'Jul': 7,
    'Aug': 8,
    'Sep': 9,
    'Oct': 10,
    'Nov': 11,
    'Dec': 12
}


class NetworkError(Exception):
    pass


def get_current_videos():
    return __get_videos(MAIN_URL)


def get_archive_dates():
    url = MAIN_URL + 'archives'
    tree = __get_tree(url)
    archive_dates = []
    for entry in tree.findAll('a', {'class': 'b'}):
        title = entry.string.strip()
        archive_id = entry['href'].replace('/archives/', '').strip()
        archive_dates.append({
            'title': title,
            'archive_id': archive_id
        })
    return reversed(archive_dates)


def get_archived_videos(archive_id):
    return __get_videos(MAIN_URL + 'archives/%s' % archive_id)


def get_search_result(query):
    return __get_videos(MAIN_URL + 'search/%s' % quote(query))


def get_video_url(video_id):
    tree = __get_tree(MAIN_URL + video_id)
    r_js = re.compile('lxUTILsign')
    r_gc = re.compile('var googleCode = \'(.+?)\';')  # funny idea :-)
    r_vurl = re.compile('"file","(.+?)"')
    js_code = tree.find('script', text=r_js).string.strip()
    js_params = b64decode(re.search(r_gc, js_code).group(1))
    video_url = re.search(r_vurl, js_params).group(1)
    return video_url


def __get_videos(url):
    tree = __get_tree(url)
    videos = []
    page_title = tree.head.title.string
    y = None
    if page_title:
        y = filter(lambda s: s.isdigit(), page_title)
    if not y:
        y = datetime.now().year
    for a in tree.findAll('a', {'class': 'b'}):
        m, d = a.find('span', {'class': 'video_date'}).string.split()
        thumb = a.find('img').get('data-original') or a.find('img')['src']
        videos.append({
            'title': a.find('span', {'class': 'video_title'}).string,
            'video_id': a['href'].split('/')[-2],
            'thumb': thumb,
            'date': '%02i.%02i.%s' % (int(d), MONTHS[m], y)
        })
    return videos


def __get_tree(url):
    req = Request(url)
    try:
        response = urlopen(req).read()
    except HTTPError, error:
        raise NetworkError(error)
    except URLError, error:
        raise NetworkError(error)
    tree = BeautifulSoup(response, convertEntities=BeautifulSoup.HTML_ENTITIES)
    return tree
