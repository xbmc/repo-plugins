# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Thomas Amland
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# adattato a kodi 20.0 da ^zZz^


import datetime
import re
from requests import Session

session = Session()
session.headers['User-Agent'] = 'kodi.tv'


class ImageMixin(object):
    images = None

    @property
    def thumb(self):
        return self.images[0]['url']

    @property
    def fanart(self):
        return self.images[-1]['url']


class Base(object):
    id = None
    title = None
    is_series = False

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class Category(Base):
    @staticmethod
    def from_response(r):
        return Category(
            title=r.get('displayValue', r.get('title', None)),
            id=r.get('id', None),
        )


class Channel(ImageMixin, Base):
    manifest = None

    @staticmethod
    def from_response(r):
        return Channel(
            title=r['_embedded']['playback']['title'],
            id=r['id'],
            manifest=r['_links']['manifest']['href'],
            images=r['_embedded']['playback']['posters'][0]['image']['items'],
        )


class Series(ImageMixin, Base):
    is_series = True
    description = None
    legal_age = None
    available = True
    category = None
    ''':class:`Category`'''

    @staticmethod
    def from_response(r):
        category = Category.from_response(r['category']) if 'category' in r else None
        images = _image_url_key_standardize(r.get('image', {}).get('webImages', None))
        return Series(
            id=r['id'],
            title=r['title'].strip(),
            category=category,
            description=r.get('description'),
            legal_age=r.get('legalAge', {}).get('displayValue', '') or r.get('aldersgrense'),
            images=images,
            available=r.get('hasOndemandrights', True)
        )

class Season(Base):
    is_season = True
    ''':class:`Season`'''

    @staticmethod
    def from_response(r):
        return Season(
            id=r['name'],
            title=r.get('title', '').strip(),
        )


class Program(Series):
    is_series = False

    episode = None
    '''Episode number, name or date as string.'''

    series_id = None

    aired = None
    '''Date and time aired as :class:`datetime.datetime`'''

    duration = None
    '''In seconds'''

    media_urls = None

    @staticmethod
    def from_response(r):
        category = Category.from_response(r['category']) if 'category' in r else None
        aired = None
        try:
            if 'usageRights' in r:
                usageRights = r.get('usageRights', None)
                availableFrom = usageRights.get('availableFrom') if usageRights else ''
                availableFrom = re.findall(r'\d+', availableFrom)[0] if availableFrom else 0
                aired = datetime.datetime.fromtimestamp(int(availableFrom)/1000)
        except (ValueError, OverflowError, OSError):
            pass

        title = r.get('title', '')
        if not title:
            seriesTitle = r.get('seriesTitle', '')
            episodeTitle = r.get('episodeTitle', '')
            title = '{} {}'.format(seriesTitle, episodeTitle)

        media_urls = []

        manifest = _get('/playback/manifest/{}'.format(r.get('id')))
        # adattato a kodi 20.0 da ^zZz^
        try:
            if manifest.json()['playability'] == 'playable':
                media_urls = list( map(lambda x: x['url'], manifest.json()['playable']['assets']) )
                media_urls
        except:  # il manifest della nuova api apparentemente e' gia' un dict
            if manifest['playability'] == 'playable':
                media_urls = list( map(lambda x: x['url'], manifest['playable']['assets']) )
                media_urls            
        ########## fine modifica ##########
        images = _image_url_key_standardize(r.get('image', {}).get('webImages', None))
        duration = _duration_to_seconds(r.get('duration', 0))
        legal_age = r.get('legalAge', None)
        if legal_age:
            legal_age = legal_age.get('displayValue', legal_age)
        elif 'aldersgrense' in r:
            legal_age = r.get('aldersgrense')

        return Program(
            id=r['id'],
            title=title,
            category=category,
            description=r.get('shortDescription'),
            duration=duration,
            images=images,
            legal_age=legal_age,
            media_urls=media_urls,
            episode=r.get('episodeNumberOrDate', 0),
            aired=aired,
            available=( (r.get('availability', {}).get('status', 'unavailable') == 'available') or (r.get('availability', {}).get('status', 'unavailable') == 'expires') )
        )

def _duration_to_seconds(duration):
    if isinstance(duration, float) or isinstance(duration, int):
        return duration * 60
    else:
        hours = re.findall(r'\d+H', duration)
        hours = float(hours[0][:-1]) if len(hours) else 0
        minutes = re.findall(r'\d+M', duration)
        minutes = float(minutes[0][:-1]) if len(minutes) else 0
        seconds = re.findall(r'\d+S', duration)
        seconds = float(seconds[0][:-1]) if len(seconds) else 0
        return hours * 60**2 + minutes * 60 + seconds

def _image_url_key_standardize(images):
    xs = images
    for image in xs:
        image['url'] = image['imageUrl']
        del image['imageUrl']
    return xs

def _get(path, params=''):
    api_key = 'd1381d92278a47c09066460f2522a67d'
    r = session.get('https://psapi.nrk.no{}?apiKey={}{}'.format(path, api_key, params))
    r.raise_for_status()
    return r.json()


def get_playback_url(manifest_url):
    playable = _get(manifest_url)['playable']
    if playable:
        return playable['assets'][0]['url']
    else:
        return None


def recommended_programs(medium='tv', category_id=None):
    if category_id:
        return [program(item['id']) for item in
                _get('/medium/%s/categories/%s/recommendedprograms' % (medium, category_id),
                     '&maxnumber=15')]
    else:
        return [program(item['id']) for item in
                _get('/medium/%s/recommendedprograms' % medium,
                     '&maxnumber=15')]

def popular_programs(medium='tv', category_id=None, list_type='week'):
    if category_id:
        return [program(item['id']) for item in
                _get('/medium/%s/categories/%s/popularprograms' % (medium, category_id),
                     '&maxnumber=15')]
    else:
        return [program(item['id']) for item in
                _get('/medium/%s/popularprograms/%s' % (medium, list_type),
                     '&maxnumber=15')]


def recent_programs(medium='tv', category_id=None):
    if category_id:
        return [program(item['id']) for item in
                _get('/medium/%s/categories/%s/recentlysentprograms' % (medium, category_id),
                     '&maxnumber=15')]
    else:
        return [program(item['id']) for item in
                _get('/medium/%s/recentlysentprograms' % medium,
                     '&maxnumber=15')]


def episodes(series_id, season_id):
    season = _get('/tv/catalog/series/%s/seasons/%s' % (series_id, season_id))
    embedded = season['_embedded']
    instalments = []
    if 'instalments' in embedded:
        instalments = embedded['instalments']
    else:
        instalments = embedded['episodes']
    return [program(item['prfId']) for item in instalments]


def seasons(series_id):
    return [Season.from_response(item) for item in
            _get('/tv/catalog/series/%s' % series_id,
                 '&embeddedInstalmentsPageSize=1')['_links']['seasons']]


def program(program_id):
    return Program.from_response(_get('/programs/%s' % program_id))


def channels():
    chs = [Channel.from_response(item) for item in _get('/tv/live')]
    return [ch for ch in chs if ch.manifest]

def radios():
    rds = [Channel.from_response(item) for item in _get('/radio/live')]
    return [rd for rd in rds if rd.manifest]


def categories():
    return [Category.from_response(item) for item in _get('/medium/tv/categories/')]


def _to_series_or_program(item):
    if item.get('type', '') == 'series':
        return Series.from_response(item)
    return Program.from_response(item)


def programs(category_id):
    items = _get('/medium/tv/categories/%s/indexelements' % category_id)
    items = [item for item in items if item.get('title', '').strip() != ''
             and item['hasOndemandRights']]
    return list(map(_to_series_or_program, items))


def _hit_to_series_or_program(item):
    hit_type = item.get('type', None)
    if hit_type == 'serie':
        return Series.from_response(item['hit'])
    elif hit_type == 'episode' or hit_type == 'program':
        return Program.from_response(item['hit'])
    return None


def search(query):
    response = _get('/search', '&q=' + query)
    if response['hits'] is None:
        return []
    return [_f for _f in map(_hit_to_series_or_program, response['hits']) if _f]
