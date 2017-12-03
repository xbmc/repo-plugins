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
Module for extracting video links from the BT Sport website
'''

from urlparse import urljoin
from datetime import datetime
import time
from collections import namedtuple
import math

import requests
from bs4 import BeautifulSoup


CATEGORIES_URL = 'http://sport.bt.com/all-videos/videos-01364228997406'
API_URL = 'http://api-search.sport.bt.com/search/sport/select'

_Video = namedtuple('Video', 'title url thumbnail date duration')


def _video_params(page, page_size):
    '''Returns the common params for the BT Sport API'''
    return dict(
        fq='AssetType:BTVideo',
        sort='publicationdate desc',
        wt='json',
        start=(page - 1) * page_size,
        rows=page_size,
    )


def _soup(path=''):
    '''Returns a BeautifulSoup tree for the specified path'''
    url = urljoin(CATEGORIES_URL, path)
    response = requests.get(url)
    return BeautifulSoup(response.text, 'html.parser')


def _date_from_str(date_str):
    '''Returns a data object from a string.
       datetime.strptime is avoided due to an issue with Python in Kodi.
       Ignores possible milliseconds part by including only 19 characters.'''
    return datetime(*(time.strptime(date_str[:19], '%Y-%m-%dT%H:%M:%S')[0:6])).date()


def categories():
    '''Generator for all sport categories on the website'''
    for category in _soup().find('div', 'video-hub-nav')('a'):
        if not category.text.startswith('All '):
            yield category.text


def _videos(videos_response):
    for video in videos_response['docs']:
        yield _Video(
            title=video['h1title'],
            url=video.get('hlsurl') or video.get('streamingurl'),
            thumbnail=video.get('imageurl') or video.get('thumbnailURL'),
            date=_date_from_str(video['publicationdate']),
            duration=int(video['duration'])
        )


def _video_results(page=1, page_size=10, **params):
    params.update(_video_params(page, page_size))
    videos_response = requests.get(API_URL, params=params).json()['response']
    num_pages = int(math.ceil(float(videos_response['numFound']) / page_size))
    return _videos(videos_response), num_pages


def videos(category=None, page=1, page_size=10):
    '''Returns a generator for videos in a category and the number of pages'''
    category = None if category.lower() == 'all' else category
    query = 'tags:("{}")'.format(category) if category else 'Publist:btsport'
    return _video_results(page, page_size, q=query)


def search_results(term, page=1, page_size=10):
    '''Returns a generator for video search results and the number of pages'''
    return _video_results(page, page_size, q='text:{}'.format(term))
