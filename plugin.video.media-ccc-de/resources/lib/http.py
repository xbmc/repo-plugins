import requests

import xbmcgui

from .stream import Streams
from .recording import Recordings

BASE_URL = 'https://api.media.ccc.de/public/'
LIVE_URL = 'https://streaming.media.ccc.de/streams/v1.json'

# BASE_URL = 'http://127.0.0.1:3000/public/'
# LIVE_URL = 'http://127.0.0.1:3000/v1.json'


class FetchError(Exception):
    pass


def fetch_data(what):
    try:
        req = requests.get(BASE_URL + what)
        return req.json()
    except requests.RequestException as e:
        err = 'CCC-TV', 'Can\'t fetch %s: %s' % (what, e)
        xbmcgui.Dialog().notification(err, xbmcgui.NOTIFICATION_ERROR, 15000)
        raise FetchError(e)


def count_view(event, src):
    try:
        data = {'event_id': event, 'src': src}
        requests.post(BASE_URL + 'recordings/count', data=data)
    except requests.RequestException as e:
        err = 'CCC-TV', 'Can\'t count view: %s' % e
        xbmcgui.Dialog().notification(err, xbmcgui.NOTIFICATION_INFO, 15000)


def fetch_recordings(event):
    req = fetch_data('events/' + event)
    return Recordings(req)


def fetch_live():
    try:
        req = requests.get(LIVE_URL)
        return Streams(req.json())
    except requests.exceptions.RequestException as e:
        err = 'CCC-TV', 'Can\'t fetch streams: %s' % e
        xbmcgui.Dialog().notification(err, xbmcgui.NOTIFICATION_ERROR, 15000)
        raise FetchError(e)
