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

import simplejson as json
from urllib import urlencode, quote_plus
from urllib2 import urlopen, Request, HTTPError, URLError

import feedparser

CONTENT_TYPES = ('video', 'audio')
GENRE_ID_PODCAST = 26
MAX_PODCAST_SEARCH_LIST = 200
MAX_PODCAST_LIST = 300
PODCAST_URL = 'http://itunes.apple.com/lookup?id=%(id)d'
GENRE_LIST_URL = ('http://itunes.apple.com/WebObjects/'
                  'MZStoreServices.woa/ws/genres?id=%(genre_id)d')
PODCAST_LIST_URL = ('http://itunes.apple.com/%(country)s/rss/'
                    'top%(content_type)spodcasts/genre=%(genre_id)d/'
                    'limit=%(limit)d/json')
PODCAST_SEARCH_URL = ('http://itunes.apple.com/search?term=%(search_term)s'
                      '&country=%(country)s&media=podcast&limit=%(limit)d')


# I guess these should be enough :)
STOREFRONT_IDS = {
    'AU': 143460,  # Australia
    'BE': 143446,  # Belgium
    'BR': 143503,  # Brazil
    'BG': 143526,  # Bulgaria
    'CA': 143455,  # Canada
    'CL': 143483,  # Chile
    'CN': 143465,  # China
    'FI': 143447,  # Finland
    'FR': 143442,  # France
    'DE': 143443,  # Germany
    'DK': 143458,  # Denmark
    'GR': 143448,  # Greece
    'IT': 143450,  # Italy
    'JP': 143462,  # Japan
    'KR': 143466,  # Korea
    'LU': 143451,  # Luxembourg
    'MX': 143468,  # Mexico
    'NL': 143452,  # Netherlands
    'NO': 143457,  # Norway
    'PL': 143478,  # Poland
    'PT': 143453,  # Portugal
    'RO': 143487,  # Romania
    'RU': 143469,  # Russia
    'ES': 143454,  # Spain
    'SE': 143456,  # Sweden
    'CH': 143459,  # Switzerland
    'TR': 143480,  # Turkey
    'GB': 143444,  # UK
    'US': 143441,  # USA
}


class NetworkError(Exception):
    pass


class NoEnclosureException(Exception):
    pass


class ItunesPodcastApi():

    USER_AGENT = 'XBMC ItunesPodcastApi'

    def __init__(self, country='US'):
        self.set_country(country)

    def set_country(self, country):
        self.country = country.lower()
        self.storefront_id = STOREFRONT_IDS.get(country.upper(), 143441)

    def get_genres(self, flat=True):
        url = GENRE_LIST_URL % {
            'genre_id': GENRE_ID_PODCAST
        }
        data = self.__get_json(url)
        genres = self._parse_genre(data, flat=flat)
        return genres

    def _parse_genre(self, node, flat, parent=None):
        genres = []
        for item in node.itervalues():
            # Don't add "Podcasts - " to all items
            if parent and parent != 'Podcasts':
                name = '%s - %s' % (parent, item['name'])
            else:
                name = item['name']
            genre = {
                'id': item['id'],
                'name': name,
                'has_video': 'topVideoPodcasts' in item.get('rssUrls', {}),
                'has_audio': 'topAudioPodcasts' in item.get('rssUrls', {}),
                'has_subgenre': 'subgenres' in item
            }
            genres.append(genre)
            # do recursive if flat is enabled or we have no parent
            if (flat or not parent) and item.get('subgenres'):
                genres.extend(self._parse_genre(
                    node=item.get('subgenres'),
                    flat=flat,
                    parent=name
                ))
        return genres

    def get_podcasts(self, genre_id, limit=50, content_type=None):
        if not content_type in CONTENT_TYPES:
            content_type = 'video'
        url = PODCAST_LIST_URL % ({
            'country': self.country,
            'content_type': content_type,
            'genre_id': int(genre_id),
            'limit': min(int(limit), MAX_PODCAST_LIST)
        })
        data = self.__get_json(url)
        podcasts = self._parse_podcasts(data['feed']['entry'])
        return podcasts

    def _parse_podcasts(self, node):

        def __get_best_thumb(node):
            thumbs = sorted(
                node,
                key=lambda p: int(p.get('attributes', {}).get('height', 0)),
                reverse=True
            )
            return thumbs[0].get('label')

        def __get_date(parent_node):
            date_str = parent_node.get('label')
            if not date_str:
                return ''
            y, m, d = date_str.split('T')[0].split('-')
            return '%s.%s.%s' % (d, m, y)

        return [{
            'id': item['id']['attributes']['im:id'],
            'title': item.get('title', {}).get('label'),
            'name': item.get('im:name', {}).get('label'),
            'author': item.get('im:artist', {}).get('label'),
            'summary': item.get('summary', {}).get('label'),
            'thumb': __get_best_thumb(item.get('im:image', [])),
            'genre': item['category'].get('attributes', {}).get('label'),
            'rights': item.get('rights', {}).get('label'),
            'release_date': __get_date(item.get('im:releaseDate', {}))
        } for item in node]

    def get_podcast_items(self, podcast_id):

        def __format_date(time_struct):
            date_f = '%02i.%02i.%04i'
            if time_struct:
                return date_f % (
                    time_struct[2], time_struct[1], time_struct[0]
                )
            else:
                return ''

        def __format_size(size_str):
            if size_str and str(size_str).isdigit():
                return int(size_str)
            else:
                return 0

        def __get_enclosure_link(node):
            if isinstance(node, (list, tuple)):
                for item in node:
                    if item.get('href') and item.get('rel') == 'enclosure':
                        return item
            elif isinstance(node, dict):
                if node.get('href') and node.get('rel') == 'enclosure':
                    return node
            raise NoEnclosureException

        url = PODCAST_URL % {'id': int(podcast_id)}
        data = self.__get_json(url)
        podcast_url = data['results'][0]['feedUrl']
        raw_content = self.__urlopen(podcast_url)
        content = feedparser.parse(raw_content)
        fallback_thumb = content['feed'].get('image', {}).get('href')
        items = []
        for item in content.entries:
            try:
                link = __get_enclosure_link(item.get('links'))
            except NoEnclosureException:
                continue
            items.append({
                'title': item.get('title'),
                'summary': item.get('summary'),
                'author': item.get('author'),
                'item_url': link['url'],
                'size': __format_size(link.get('length', '')),
                'thumb': item.get('image', {}).get('href') or fallback_thumb,
                'duration': link.get('duration', '0:00'),
                'pub_date': __format_date(item.get('published_parsed')),
                'rights': content['feed'].get('copyright')
            })
        if not items:
            raise NoEnclosureException
        return items

    def search_podcast(self, search_term, limit=50):
        url = PODCAST_SEARCH_URL % ({
            'country': self.country,
            'limit': min(int(limit), MAX_PODCAST_SEARCH_LIST),
            'search_term': quote_plus(search_term)
        })
        data = self.__get_json(url)
        podcasts = self._parse_podcast_search_result(data['results'])
        return podcasts

    def get_single_podcast(self, podcast_id):
        url = PODCAST_URL % {'id': int(podcast_id)}
        data = self.__get_json(url)
        podcasts = self._parse_podcast_search_result(data['results'])
        return podcasts[0]

    def _parse_podcast_search_result(self, node):
        return [{
            'id': item['collectionId'],
            'title': item.get('collectionName'),
            'name': item.get('collectionName'),
            'author': item.get('artistName'),
            'summary': '',
            'thumb': item.get('artworkUrl100'),
            'genre': ','.join(item.get('genres', [])),
            'rights': '',
            'release_date': ''
        } for item in node]

    def __get_json(self, url, path=None, params=None):
        response = self.__urlopen(url, path, params)
        json_data = json.loads(response)
        return json_data

    def __urlopen(self, url, path=None, params=None):
        if path:
            url += path
        if params:
            url += '?%s' % urlencode(params)
        req = Request(url)
        req.add_header('X-Apple-Store-Front', self.storefront_id)
        try:
            response = urlopen(req).read()
        except HTTPError, error:
            raise NetworkError('HTTPError: %s' % error)
        except URLError, error:
            raise NetworkError('URLError: %s' % error)
        return response


def test():
    api = ItunesPodcastApi(country='de')
    genres = api.get_genres(flat=True)
    assert genres
    for genre in genres[0:4]:
        print genre['name']
        for content_type in CONTENT_TYPES:
            podcasts = api.get_podcasts(genre['id'], content_type=content_type)
            assert podcasts
            for p in podcasts[0:4]:
                pid = p['id']
                print pid
                items = api.get_podcast_items(pid)
                assert items
                for i in items[0:4]:
                    print i['item_url']
            assert api.get_single_podcast(pid)
            assert api.search_podcast('test')


if __name__ == '__main__':
    test()
