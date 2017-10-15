###############################################################################
#
# MIT License
#
# Copyright (c) 2017 Lee Smith
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
###############################################################################

'''
Module for extracting video links from the England and Wales Cricket Board website
'''

import json
import os
from urlparse import urljoin, urlparse, urlunparse
from urllib import urlencode
from datetime import datetime
import time
from collections import namedtuple

import requests
from bs4 import BeautifulSoup

HOST = 'http://www.ecb.co.uk'
BASE_URL = urljoin(HOST, 'tv/')

HLS_HOST = 'https://secure.brightcove.com/'
HLS_URL_FMT = urljoin(HLS_HOST, 'services/mobile/streaming/index/master.m3u8?videoId={}')

SEARCH_URL = 'https://content-ecb.pulselive.com/search/ecb/'


Video = namedtuple('Video', 'title url thumbnail date duration')


def _search_url(term, start, size):
    '''Returns a URL for the JSON search api'''
    url_parts = list(urlparse(SEARCH_URL))
    query_params = dict(
        type='VIDEO',
        fullObjectResponse=True,
        terms=term,
        size=size,
        start=start
    )
    url_parts[4] = urlencode(query_params)
    return urlunparse(url_parts)


def _soup(path=''):
    '''Returns a BeautifulSoup tree for the specified path'''
    url = urljoin(BASE_URL, path)
    response = requests.get(url)
    return BeautifulSoup(response.text, 'html.parser')


def _date_from_str(date_str, fmt='%d %B %Y'):
    '''Returns a data object from a string.
       datetime.strptime is avoided due to a Python issue in Kodi'''
    return datetime(*(time.strptime(date_str, fmt)[0:6])).date()


def _date(media_item):
    '''Returns a date object from the HTML media item.'''
    date_str = media_item.find('time', 'media__sub-meta').string
    return _date_from_str(date_str)


def _date_json(json_item):
    '''Returns a date object from the JSON item.
       The date can be one of two formats'''
    date_str = json_item['date']
    for fmt in ['%Y-%m-%dT%H:%M', '%d/%m/%Y %H:%M']:
        try:
            date = _date_from_str(date_str.strip(), fmt=fmt)
        except ValueError as exc:
            continue
        else:
            return date
    raise exc


def categories():
    '''Generator for category names and links, excluding all that appear before Home'''
    start = False
    for submenu_link in _soup()('a', 'submenu__link'):
        title = submenu_link.string.strip()
        if start and title != 'All Categories':
            yield title, os.path.basename(submenu_link['href'])
        if title == 'Home':
            start = True


def videos(path):
    '''Generator for all videos from a particular page'''
    for media_item in _soup(path)('a', 'media__item'):
        video = json.loads(media_item['data-ui-args'])
        yield Video(
            title=media_item.find('span', 'media__title').string,
            url=HLS_URL_FMT.format(video['mediaId']),
            thumbnail=media_item.picture.img['data-highres-img'],
            date=_date(media_item),
            duration=int(video['duration'].replace(',', ''))
        )


def search_results(term, start=0, size=10):
    '''Generator for videos matching a search term'''
    results = requests.get(_search_url(term, start, size)).json()['hits']['hit']
    for result in results:
        video = result['response']
        yield Video(
            title=video['title'],
            url=HLS_URL_FMT.format(video['mediaId']),
            thumbnail=video['imageUrl'],
            date=_date_json(video),
            duration=video['duration']
        )


def _print_all_videos():
    '''Test function to print all categories and videos'''
    for title, path in categories():
        print '{} ({})'.format(title, path)
        for video in videos(path):
            print '\t', video.title


def _print_search_results(term):
    '''Test function to print search results'''
    print 'Search: {}'.format(term)
    for video in search_results(term):
        print '\t', video.title


if __name__ == '__main__':
    _print_all_videos()
    print
    _print_search_results('test cricket')
