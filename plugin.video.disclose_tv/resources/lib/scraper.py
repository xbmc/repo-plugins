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
import sys
import logging

from xbmcswift2 import Plugin
plugin = Plugin()

if sys.version_info >= (2, 7):
    import json
else:
    import simplejson as json

from BeautifulSoup import BeautifulSoup
from urllib2 import urlopen

MAIN_URL = 'http://www.disclose.tv/'


class Scraper:

    def get_video_topics(self):
        log('get_video_topics started')
        path = 'action/videolist/page/1/all/filter/'
        url = MAIN_URL + path
        tree = self.__get_tree(url)
        ul = tree.find('ul', {'id': 'videos-media-box-filter'})
        topics = []
        for li in ul.findAll('li'):
            topics.append({
                'title': li.a.string,
                'id': li.a['href'].split('/')[5]
            })
        return topics

    def get_videos(self, topic_id, page):
        log('get_videos_by_topic_id started with topic_id=%s' % topic_id)
        url = MAIN_URL + 'action/videolist/page/%d/%s/filter/' % (
            int(page), topic_id
        )
        tree = self.__get_tree(url)
        div = tree.find('div', {'id': 'videos-media-box-list'})
        videos = []
        for li in div.findAll('li', {'class': 'clearfix '}):
            a = li.find('a')
            title = li.find('img')['alt']
            video_id = '/'.join((a['href'].split('/')[3:5]))
            span_content = li.find('span', {'class': 'types typeV'}).contents
            duration = span_content[0].strip()

            videos.append({
                'id': video_id,
                'thumbnail': self.__img(li.find('img')['src'] or li.find('img')['data-src']),
                'title': title,
                'duration': self.__secs_from_duration(duration)
            })
        return videos

    def get_video_url(self, video_id):
        url = MAIN_URL + 'action/viewvideo/%s/' % video_id
        data = self.__get_url(url)
        if plugin.get_setting('Disable_HD_Default') == 'false':
            hdcheck = re.search(r"(http://video.*?\.flv)", data)
            if hdcheck:
                match=hdcheck
            else:
                match = re.search(r"(https?://video.*?\.(flv|mp4|webm))", data)
        else:
            match = re.search(r"(https?://video.*?\.(flv|mp4|webm))", data)
        if match:
            return match.group(1).replace('http://', 'https://')

    @staticmethod
    def __secs_from_duration(d):
        seconds = 0
        for part in d.split(':'):
            seconds = seconds * 60 + int(part)
        return seconds

    @staticmethod
    def __img(url):
        return url.replace('135x76', '').split('?')[0]

    def __get_tree(self, url):
        html = self.__get_url(url)
        return BeautifulSoup(html, convertEntities=BeautifulSoup.HTML_ENTITIES)

    def __get_url(self, url):
        log('__get_url opening url: %s' % url)
        response = urlopen(url).read()
        log('__get_url got %d bytes' % len(response))
        return response


def log(text):
    plugin.log.info(u'Scraper: %s' % text)
