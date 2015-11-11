# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2016 Espen Hovlandsdal

from requests import Session

API_URL = 'http://api.vg.no/podcast';

session = Session()
session.headers['User-Agent'] = 'kodi-vg-podcasts'
session.headers['Accept'] = 'application/json'

class Base(object):
    id = None
    title = None
    subtitle = None
    thumb = None
    logo = None

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

class Show(Base):
    @staticmethod
    def from_response(r):
        return Show(
            id=r['slug'],
            title=r['name'],
            subtitle=r['subtitle'],
            logo=r['logo'],
            thumb=r['logoThumb']
        )

class Episode(Base):
    duration = 0
    media_url = None
    year = 2015

    @staticmethod
    def from_response(r):
        url = None
        for attachment in r['attachments']:
            if attachment['format'] == 'mp3':
                url = attachment['url']
                break

        return Episode(
            id=r['slug'],
            title=r['title'],
            subtitle=r['subtitle'],
            logo=r['logo'],
            thumb=r['logoThumb'],
            year=get_year(r['pubDate']),
            duration=parse_duration(r['duration']),
            media_url=url
        )

def shows():
    return [Show.from_response(item) for item in _get('/shows.json')]

def episodes(slug):
    items = _get('/' + slug + '.json')['episodes']
    return [Episode.from_response(item) for item in items]

def parse_duration(dur):
    parts = dur.split(':')
    multiplier = 1
    seconds = 0

    for part in reversed(parts):
        seconds += int(part) * multiplier
        multiplier *= 60

    return seconds

def get_year(date):
    return int(date[:4])

def _get(path):
    r = session.get(API_URL + path)
    r.raise_for_status()
    return r.json()
