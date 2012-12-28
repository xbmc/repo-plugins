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

import urllib2
from BeautifulSoup import BeautifulSoup

MAIN_URL = 'http://www.hd-trailers.net/'
NEXT_IMG = 'http://static.hd-trailers.net/images/mobile/next.png'
PREV_IMG = 'http://static.hd-trailers.net/images/mobile/prev.png'
USER_AGENT = 'XBMC Add-on HD-Trailers.net v0.1.0'

SOURCES = (
    'apple.com',
    'yahoo.com',
    'youtube.com',
    'moviefone.com',
    'ign.com',
    'hd-trailers.net',
    'aol.com'
)


class NetworkError(Exception):
    pass


def get_latest(page=1):
    url = MAIN_URL + 'page/%d/' % int(page)
    return _get_movies(url)


def get_most_watched():
    url = MAIN_URL + 'most-watched/'
    return _get_movies(url)


def get_top_ten():
    url = MAIN_URL + 'top-movies'
    return _get_movies(url)


def get_opening_this_week():
    url = MAIN_URL + 'opening-this-week'
    return _get_movies(url)


def get_coming_soon():
    url = MAIN_URL + 'coming-soon'
    return _get_movies(url)


def get_by_initial(initial='0'):
    url = MAIN_URL + 'poster-library/%s/' % initial
    return _get_movies(url)


def get_initials():
    return list('0ABCDEFGHIJKLMNOPQRSTUVWXYZ')


def get_videos(movie_id):
    url = MAIN_URL + 'movie/%s' % movie_id
    tree = __get_tree(url)

    trailers = []
    clips = []
    section = trailers

    span = tree.find('span', {'class': 'topTableImage'})
    movie = {
        'title': span.img['title'],
        'thumb': span.img['src']
    }

    table = tree.find('table', {'class': 'bottomTable'})
    for tr in table.findAll('tr'):
        if tr.find('td', text='Trailers'):
            section = trailers
            continue
        elif tr.find('td', text='Clips'):
            section = clips
            continue
        elif tr.get('itemprop'):
            res_tds = tr.findAll('td', {'class': 'bottomTableResolution'})
            resolutions = {}
            for td in res_tds:
                if td.a:
                    resolutions[td.a.string] = td.a['href']
            if not resolutions:
                log('No resolutions found: %s' % movie_id)
                continue
            try:
                source = __detect_source(resolutions.values()[0])
            except NotImplementedError, video_url:
                log('Skipping: %s - %s' % (movie_id, video_url))
                continue
            section.append({
                'title': tr.contents[3].span.string,
                'date': __format_date(tr.contents[1].string),
                'source': source,
                'resolutions': resolutions
            })
    return movie, trailers, clips


def _get_movies(url):
    tree = __get_tree(url)
    movies = [{
        'id': td.a['href'].split('/')[2],
        'title': td.a.img['alt'],
        'thumb': td.a.img['src']
    } for td in tree.findAll('td', {'class': 'indexTableTrailerImage'})]
    has_next_page = tree.find(
        'a',
        attrs={'class': 'startLink'},
        text=lambda text: 'Next' in text
    ) is not None
    return movies, has_next_page


def __detect_source(url):
    for source in SOURCES:
        if source in url:
            return source
    raise NotImplementedError(url)


def __format_date(date_str):
    y, m, d = date_str.split('-')
    return '%s.%s.%s' % (d, m, y)


def __get_tree(url):
    log('__get_tree opening url: %s' % url)
    headers = {'User-Agent': USER_AGENT}
    req = urllib2.Request(url, None, headers)
    try:
        html = urllib2.urlopen(req).read()
    except urllib2.HTTPError, error:
        raise NetworkError('HTTPError: %s' % error)
    log('__get_tree got %d bytes' % len(html))
    tree = BeautifulSoup(html, convertEntities=BeautifulSoup.HTML_ENTITIES)
    return tree


def log(msg):
    print(u'%s scraper: %s' % (USER_AGENT, msg))
