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

import os
import re
from urlparse import urljoin, urlparse, urlunparse
from urllib import urlencode
from datetime import datetime
import time
from collections import namedtuple
import math

import requests
from bs4 import BeautifulSoup


BASE_URL = 'http://www.ecb.co.uk/'

HLS_HOST = 'https://secure.brightcove.com/'
HLS_URL_FMT = urljoin(HLS_HOST, 'services/mobile/streaming/index/master.m3u8?videoId={}')

PLAYER_THUMB_URL_FMT = 'https://ecb-resources.s3.amazonaws.com/player-photos/{}/480x480/{}.png'

SEARCH_URL = 'https://content-ecb.pulselive.com/search/ecb/'
VIDEO_LIST_URL = 'https://content-ecb.pulselive.com/content/ecb/EN/'

Video = namedtuple('Video', 'title url thumbnail date duration')
Entity = namedtuple('Entity', 'name reference thumbnail')


def _video_list_url(reference, page, page_size=10):
    '''Returns a URL for a list of videos'''
    url_parts = list(urlparse(VIDEO_LIST_URL))
    query_params = dict(
        contentTypes='video',
        references=reference if reference is not None else '',
        page=page - 1,
        pageSize=page_size
    )
    url_parts[4] = urlencode(query_params)
    return urlunparse(url_parts)


def _search_url(term, page, page_size=10):
    '''Returns a URL for the JSON search api'''
    url_parts = list(urlparse(SEARCH_URL))
    query_params = dict(
        type='VIDEO',
        fullObjectResponse=True,
        terms=term,
        size=page_size,
        start=(page - 1) * page_size
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


def _thumbnail_variant(video):
    if video['thumbnail'] is None:
        return
    return (variant['url'] for variant in video['thumbnail']['variants']
            if variant['tag']['id'] == 981).next()


def england():
    return Entity(
        name='England',
        reference='cricket_team:11',
        thumbnail=None
    )


def counties():
    for county in _soup('/county-championship/teams')('div', 'partners__item'):
        team_id = int(os.path.basename(county.a['href']))
        yield Entity(
            name=county.a.text,
            reference='cricket_team:{}'.format(team_id),
            thumbnail=county.img['src']
        )


def player_categories():
    for tab in _soup('/england/men/players').find_all(
            'div', attrs={'data-ui-args': re.compile(r'{ "title": "\w+" }')}):
        yield Entity(
            name=tab['data-ui-tab'],
            reference=None,
            thumbnail=None
        )


def players(category='Test'):
    soup = _soup('/england/men/players').find('div', attrs={'data-ui-tab': category})
    for player in soup('section', 'profile-player-card'):
        player_id = player.img['data-player']
        yield Entity(
            name=player.img['alt'],
            reference='cricket_player:{}'.format(player_id),
            thumbnail=PLAYER_THUMB_URL_FMT.format(category.lower(), player_id)
        )


def _video(video):
    return Video(
        title=video['title'],
        url=HLS_URL_FMT.format(video['mediaId']),
        thumbnail=_thumbnail_variant(video),
        date=_date_json(video),
        duration=video['duration']
    )


def _videos(videos_json):
    '''Generator for all videos from a particular page'''
    for video in videos_json['content']:
        yield _video(video)


def videos(reference=None, page=1, page_size=10):
    videos_json = requests.get(_video_list_url(reference, page, page_size)).json()
    npages = videos_json['pageInfo']['numPages']
    return _videos(videos_json), npages


def _search_results(search_results_json):
    '''Generator for videos matching a search term'''
    results = search_results_json['hits']['hit']
    for result in results:
        video = result['response']
        yield _video(video)


def search_results(term, page=1, page_size=10):
    search_results_json = requests.get(_search_url(term, page, page_size)).json()
    total = search_results_json['hits']['found']
    npages = int(math.ceil(float(total) / page_size))
    return _search_results(search_results_json), npages


def _print_team_videos():
    '''Test function to print all categories and videos'''
    for team in [england()] + list(counties()):
        print '{} ({})'.format(team.name, team.reference)
        videos_page, _num_pages = videos(team.reference)
        for video in videos_page:
            print '\t', video.title


def _print_search_results(term):
    '''Test function to print search results'''
    print 'Search: {}'.format(term)
    videos_page, _num_pages = search_results(term)
    for video in videos_page:
        print '\t', video.title


if __name__ == '__main__':
    _print_team_videos()
    print
    _print_search_results('test cricket')
