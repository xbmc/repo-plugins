import requests

import xbmcgui

from .stream import Streams

BASE_URL = 'https://api.media.ccc.de/public/'
LIVE_URL = 'https://streaming.media.ccc.de/streams/v1.json'

#BASE_URL = 'http://127.0.0.1:3000/public/'
#LIVE_URL = 'http://127.0.0.1:3000/v1.json'

class FetchError(Exception):
    pass

def fetch_data(what):
    try:
        req = requests.get(BASE_URL + what)
        return req.json()
    except requests.RequestException as e:
        xbmcgui.Dialog().notification('CCC-TV', 'Can\'t fetch %s: %s' % (what, e), xbmcgui.NOTIFICATION_ERROR, 15000)
        raise FetchError(e)

def count_view(event, src):
    try:
        requests.post(BASE_URL + 'recordings/count', data = {'event_id': event, 'src': src})
    except requests.RequestException as e:
        xbmcgui.Dialog().notification('CCC-TV', 'Can\'t count view: %s' % e, xbmcgui.NOTIFICATION_INFO, 15000)

def fetch_live():
    try:
        req = requests.get(LIVE_URL)
        return Streams(req.json())
    except requests.exceptions.RequestException as e:
        xbmcgui.Dialog().notification('CCC-TV', 'Can\'t fetch streams: %s' % e, xbmcgui.NOTIFICATION_ERROR, 15000)
        raise FetchError(e)

