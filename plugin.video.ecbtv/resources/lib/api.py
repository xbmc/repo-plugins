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
from urlparse import urljoin
from datetime import datetime, date, timedelta
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
TOURNAMENTS_URL = 'https://cricketapi-ecb.pulselive.com/tournaments/'

_Video = namedtuple('Video', 'title url thumbnail date duration')
_Entity = namedtuple('Entity', 'name id reference thumbnail')


def _video_query_params(reference, page, page_size=10):
    '''Returns a dictionary of query params for a list of videos'''
    return dict(
        contentTypes='video',
        references=reference if reference is not None else '',
        page=page - 1,
        pageSize=page_size
    )


def _search_query_params(term, page, page_size=10):
    '''Returns a dictionary of query params for the JSON search api'''
    return dict(
        type='VIDEO',
        fullObjectResponse=True,
        terms=term,
        size=page_size,
        start=(page - 1) * page_size
    )


def _tournaments_query_params(team_ids,
                              match_types,
                              weeks_ago,
                              weeks_ahead):
    '''Returns a dictionary of query params for the list of tournaments'''
    query_params = dict(
        teamIds=','.join(map(str, team_ids)),
        startDate=date.today() - timedelta(weeks=weeks_ago),
        endDate=date.today() + timedelta(weeks=weeks_ahead),
        sort='desc')
    if match_types is not None:
        query_params['matchTypes'] = ','.join(
            str(t).replace(' ', '_').upper() for t in match_types
        )
    return query_params


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
            return _date_from_str(date_str.strip(), fmt=fmt)
        except ValueError as exc:
            continue
    raise exc


def _thumbnail_variant(video):
    '''Returns the url for the "Media Thumbnail - Squared Medium" thumbnail'''
    if video['thumbnail'] is None:
        return
    return (variant['url'] for variant in video['thumbnail']['variants']
            if variant['tag']['id'] == 981).next()


def england():
    '''Returns an Entity for the England Men team'''
    return _Entity(
        name='England',
        id=11,
        reference='cricket_team:11',
        thumbnail=None
    )


def counties():
    '''Generator for an Entity for each county team'''
    for county in _soup('/county-championship/teams')('div', 'partners__item'):
        team_id = int(os.path.basename(county.a['href']))
        yield _Entity(
            name=county.a.text,
            id=team_id,
            reference='cricket_team:{}'.format(team_id),
            thumbnail=county.img['src']
        )


def player_categories():
    '''Generator for an Entity representing each form of the game'''
    for tab in _soup('/england/men/players').find_all(
            'div', attrs={'data-ui-args': re.compile(r'{ "title": "\w+" }')}):
        yield _Entity(
            name=tab['data-ui-tab'],
            id=None,
            reference=None,
            thumbnail=None
        )


def players(category='Test'):
    '''Generator for England players currently playing in the provided form of the game'''
    soup = _soup('/england/men/players').find('div', attrs={'data-ui-tab': category})
    for player in soup('section', 'profile-player-card'):
        player_id = player.img['data-player']
        yield _Entity(
            name=player.img['alt'],
            id=player_id,
            reference='cricket_player:{}'.format(player_id),
            thumbnail=PLAYER_THUMB_URL_FMT.format(category.lower(), player_id)
        )


def _tournaments(team_ids,
                 match_types=None,
                 weeks_ago=26,
                 weeks_ahead=4):
    for tournament in requests.get(
            url=TOURNAMENTS_URL,
            params=_tournaments_query_params(team_ids, match_types, weeks_ago, weeks_ahead)
        ).json()['content']:
        yield _Entity(
            name=tournament['description'],
            id=tournament['id'],
            thumbnail=None,
            reference='cricket_tournament:{}'.format(tournament['id'])
        )


def england_tournaments():
    '''Returns a generator for all tournaments played by the England Men'''
    return _tournaments([england().id], ['Test', 'ODI', 'T20I'])


def county_tournaments():
    '''Generator for all tournaments played by a county, excluding tour matches'''
    for tournament in _tournaments([county.id for county in counties()], weeks_ahead=0):
        if not re.search(' in [A-Z]', tournament.name):
            yield tournament


def _video(video):
    return _Video(
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
    '''Returns a generator for videos matching a reference string,
       and the number of pages'''
    videos_json = requests.get(
        url=VIDEO_LIST_URL,
        params=_video_query_params(reference, page, page_size)
    ).json()
    npages = videos_json['pageInfo']['numPages']
    return _videos(videos_json), npages


def _search_results(search_results_json):
    '''Generator for videos matching a search term'''
    results = search_results_json['hits']['hit']
    for result in results:
        video = result['response']
        yield _video(video)


def search_results(term, page=1, page_size=10):
    '''Returns a generator for search results and the number of pages'''
    search_results_json = requests.get(
        url=SEARCH_URL,
        params=_search_query_params(term, page, page_size)
    ).json()
    total = search_results_json['hits']['found']
    npages = int(math.ceil(float(total) / page_size))
    return _search_results(search_results_json), npages
