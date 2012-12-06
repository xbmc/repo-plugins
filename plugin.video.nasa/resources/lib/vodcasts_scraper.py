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

from urllib2 import urlopen
from BeautifulSoup import BeautifulSoup, BeautifulStoneSoup
import re

MAIN_URL = 'http://www.nasa.gov/rss/'


def get_vodcasts():
    log('get_vodcasts started')
    url = 'http://www.nasa.gov/multimedia/index.html'
    html = urlopen(url).read()
    e = BeautifulStoneSoup.HTML_ENTITIES
    tree = BeautifulSoup(html, convertEntities=e)
    vodcasts = []
    for section in tree.findAll('div', {'class': 'box_230_cap'}):
        if section.find('h2', text='Video Podcasts'):
            for row in section.findAll('tr'):
                cells = row.findAll('td')
                if len(cells) == 2:
                    title = cells[0].b.string
                    link = cells[1].a['href']
                    if '/rss/' in link:
                        vodcasts.append({
                            'title': title[1:],
                            'rss_file': link[5:]
                        })
            break
    log('get_vodcasts finished with %d vodcasts' % len(vodcasts))
    return vodcasts


def show_vodcast_videos(rss_file):
    log('get_vodcasts started with rss_file=%s' % rss_file)
    r_media = re.compile('^media')
    url = MAIN_URL + rss_file
    rss = urlopen(url).read()
    e = BeautifulStoneSoup.XML_ENTITIES
    tree = BeautifulStoneSoup(rss, convertEntities=e)
    videos = []
    for item in tree.findAll('item'):
        if item.find(r_media):
            thumbnail = item.find(r_media)['url']
        else:
            thumbnail = 'DefaultVideo.png'
        videos.append({
            'title': item.title.string,
            'thumbnail': thumbnail,
            'url': item.enclosure['url'],
            'description': item.description.string
        })
    log('show_vodcast_videos finished with %d videos' % len(videos))
    return videos


def log(text):
    print 'Nasa vodcasts scraper: %s' % text
