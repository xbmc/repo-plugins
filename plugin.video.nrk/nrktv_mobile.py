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

from requests import Session

session = Session()
session.headers['User-Agent'] = 'xbmc.org'
session.headers['app-version-android'] = '51'


class Model(object):
    id = None
    title = None

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class Category(Model):
    @staticmethod
    def from_response(r):
        return Category(
            title=r['displayValue'],
            id=r['categoryId'],
        )


class Program(Model):
    description = None
    legal_age = None
    image_id = None
    media_url = None
    _image_url = "http://m.nrk.no/m/img?kaleidoId=%s&width=%d"

    @staticmethod
    def from_response(r):
        category = Category.from_response(r['category'])
        return Program(
            id=r['programId'],
            title=r['title'],
            category=category,
            description=r.get('description'),
            duration=r['duration'],
            image_id=r['imageId'],
            legal_age=r.get('legalAge') or r.get('aldersgrense'),
            media_url=r['mediaUrl'],
            thumb=Program._image_url % (r['imageId'], 250),
            fanart=Program._image_url % (r['imageId'], 1920),
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
