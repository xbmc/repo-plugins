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

from __future__ import unicode_literals

import datetime
from requests import Session

session = Session()
session.headers['User-Agent'] = 'xbmc.org'
session.headers['app-version-android'] = '51'


class ImageMixin(object):
    image_id = None
    _image_url = "http://m.nrk.no/m/img?kaleidoId=%s&width=%d"

    @property
    def thumb(self):
        return self._image_url % (self.image_id, 500) if self.image_id else None

    @property
    def fanart(self):
        return self._image_url % (self.image_id, 1920) if self.image_id else None


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
            title=r.get('displayValue', None) or r['title'],
            id=r['categoryId'],
        )


class Channel(ImageMixin, Base):
    media_url = None

    # override images. some resolutions are corrupt server side
    @property
    def thumb(self):
        return self._image_url % (self.image_id, 490)

    @property
    def fanart(self):
        return self._image_url % (self.image_id, 1910)

    @staticmethod
    def from_response(r):
        return Channel(
            title=r['title'],
            id=r['channelId'],
            media_url=r['mediaUrl'],
            image_id=r['imageId'],
        )


class Series(ImageMixin, Base):
    is_series = True
    description = None
    legal_age = None
    available = True
    category = None
    """:class:`Category`"""

    @staticmethod
    def from_response(r):
        category = Category.from_response(r['category']) if 'category' in r else None
        return Series(
            id=r['seriesId'],
            title=r['title'].strip(),
            category=category,
            description=r.get('description'),
            legal_age=r.get('legalAge') or r.get('aldersgrense'),
            image_id=r.get('seriesImageId', r.get('imageId', None)),
            available=r.get('isAvailable', True)
        )


class Program(Series):
    is_series = False

    episode = None
    """Episode number, name or date as string."""

    aired = None
    """Date and time aired as :class:`datetime.datetime`"""

    duration = None
    """In seconds"""

    media_urls = None

    @staticmethod
    def from_response(r):
        category = Category.from_response(r['category']) if 'category' in r else None
        aired = None
        try:
            aired = datetime.datetime.fromtimestamp(
                int(r.get('usageRights', {}).get('availableFrom', 0)/1000))
        except (ValueError, OverflowError, OSError):
            pass

        media_urls = []
        if 'parts' in r:
            parts = sorted(r['parts'], key=lambda x: x['part'])
            media_urls = [part['mediaUrl'] for part in parts]
        elif 'mediaUrl' in r:
            media_urls = [r['mediaUrl']]

        return Program(
            id=r['programId'],
            title=r['title'].strip(),
            category=category,
            description=r.get('description'),
            duration=int(r.get('duration', 0)/1000),
            image_id=r['imageId'],
            legal_age=r.get('legalAge') or r.get('aldersgrense'),
            media_urls=media_urls,
            episode=r.get('episodeNumberOrDate'),
            aired=aired,
            available=r.get('isAvailable', True)
        )


def _get(path):
    r = session.get("http://m.nrk.no/tvapi/v1" + path)
    r.raise_for_status()
    return r.json()


def recommended_programs(category_id='all-programs'):
    return [Program.from_response(item) for item in
            _get('/categories/%s/recommendedprograms' % category_id)]


def popular_programs(category_id='all-programs'):
    return [Program.from_response(item) for item in
            _get('/categories/%s/popularprograms' % category_id)]


def recent_programs(category_id='all-programs'):
    return [Program.from_response(item) for item in
            _get('/categories/%s/recentlysentprograms' % category_id)]


def episodes(series_id):
    return [Program.from_response(item) for item in
            _get('/series/%s' % series_id)['programs']]


def program(program_id):
    return Program.from_response(_get('/programs/%s' % program_id))


def channels():
    return [Channel.from_response(item) for item in _get('/channels')]


def categories():
    return [Category.from_response(item) for item in _get('/categories/')]


def _to_series_or_program(item):
    if item.get('seriesId', '').strip():
        return Series.from_response(item)
    return Program.from_response(item)


def programs(category_id):
    items = _get('/categories/%s/programs' % category_id)
    items = [item for item in items if item.get('title', '').strip() != ''
             and item['programId'] != 'notransmission']
    return map(_to_series_or_program, items)


def _hit_to_series_or_program(item):
    hit_type = item.get('type', None)
    if hit_type == 'serie':
        return Series.from_response(item['hit'])
    elif hit_type == 'episode' or hit_type == 'program':
        return Program.from_response(item['hit'])
    return None


def search(query):
    response = _get('/search/' + query)
    if response['hits'] is None:
        return []
    return filter(None, map(_hit_to_series_or_program, response['hits']))
