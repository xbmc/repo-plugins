# coding: utf-8
from __future__ import print_function, division, absolute_import

import requests

from .stream import Streams
from .recording import Recordings
from .relive import Relives, ReliveRecordings
from . import gui

BASE_URL = 'https://media.ccc.de/public/'
LIVE_URL = 'https://streaming.media.ccc.de/streams/v2.json'
RELIVE_URL = 'https://cdn.c3voc.de/relive/index.json'

# BASE_URL = 'http://127.0.0.1:3000/public/'
# LIVE_URL = 'http://127.0.0.1:3000/stream_v2.json'


class FetchError(Exception):
    pass


def fetch_data(what):
    try:
        req = requests.get(BASE_URL + what)
        return req.json()
    except requests.RequestException as e:
        gui.err('Can\'t fetch %s: %s' % (what, e))
        raise FetchError(e)


def count_view(event, src):
    try:
        data = {'event_id': event, 'src': src}
        requests.post(BASE_URL + 'recordings/count', data=data)
    except requests.RequestException as e:
        gui.info('Can\'t count view: %s' % e)


def fetch_recordings(event):
    req = fetch_data('events/' + event)
    return Recordings(req)


def fetch_live():
    try:
        req = requests.get(LIVE_URL)
        return Streams(req.json())
    except requests.exceptions.RequestException as e:
        gui.err('Can\'t fetch streams: %s' % e)
        raise FetchError(e)


def fetch_relive_index():
    try:
        req = requests.get(RELIVE_URL)
        return Relives(req.json())
    except requests.exceptions.RequestException as e:
        gui.err('Can\'t fetch relive index: %s' % e)
        raise FetchError(e)


def fetch_relive_recordings(url):
    try:
        req = requests.get(url)
        return ReliveRecordings(req.json())
    except requests.exceptions.RequestException as e:
        gui.err('Can\'t fetch relive recordings: %s' % e)
        raise FetchError(e)
