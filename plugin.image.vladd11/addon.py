import socket
import sys
from urllib.parse import parse_qsl

import sys
from urllib.parse import parse_qsl

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

from album import list_albums, album
from timeline import timeline, time
from utils import get_url, API_KEY, conn, RAW_SERVER_URL

DEBUG = False
if DEBUG:
    import debug

URL = sys.argv[0]
HANDLE = int(sys.argv[1])
addon = xbmcaddon.Addon()
if __name__ == '__main__':
    params = dict(parse_qsl(sys.argv[2][1:]))

    if not RAW_SERVER_URL:
        addon.openSettings()
        exit(0)

    try:
        conn.request("GET", "/api/users/me", headers={
            'Accept': 'application/json',
            'x-api-key': API_KEY
        })
        response = conn.getresponse()
        response.read()
        if response.code == 401:
            dialog = xbmcgui.Dialog()
            d = dialog.ok(addon.getLocalizedString(30009),
                          addon.getLocalizedString(30010))
            exit(0)
        elif response.code != 200:
            raise Exception('Can\'t connect to Immich')
    except socket.error as e:
        dialog = xbmcgui.Dialog()
        d = dialog.ok(addon.getLocalizedString(30007),
                      addon.getLocalizedString(30008))
        exit(0)

    if not params.get('action'):
        xbmcplugin.addDirectoryItem(HANDLE, get_url(action='timeline'),
                                    xbmcgui.ListItem(addon.getLocalizedString(30002)), True)
        xbmcplugin.addDirectoryItem(HANDLE, get_url(action='albums'),
                                    xbmcgui.ListItem(addon.getLocalizedString(30003)), True)

        xbmcplugin.endOfDirectory(HANDLE)
    elif params['action'] == 'settings':
        addon.openSettings()
    elif params['action'] == 'timeline':
        timeline()
    elif params['action'] == 'albums':
        list_albums()
    elif params['action'] == 'album':
        album(params['id'])
    elif params['action'] == 'time':
        time(params['id'])

if DEBUG:
    import pydevd

    pydevd.stoptrace()
