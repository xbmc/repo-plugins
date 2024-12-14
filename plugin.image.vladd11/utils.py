import http.client
import sys
from datetime import datetime
from urllib.parse import urlencode, urlparse

import xbmc
import xbmcplugin
from xbmcaddon import Addon
from xbmcvfs import translatePath

HANDLE = int(sys.argv[1])

RAW_SERVER_URL = xbmcplugin.getSetting(HANDLE, "immich_url")
SHARED_ONLY = xbmcplugin.getSetting(HANDLE, "shared_only")
SERVER_URL = urlparse(RAW_SERVER_URL)
API_KEY = xbmcplugin.getSetting(HANDLE, "api_key")
ADDON_PATH = translatePath(Addon().getAddonInfo('path'))
conn = http.client.HTTPSConnection(SERVER_URL.netloc) if SERVER_URL.scheme == 'https' \
    else http.client.HTTPConnection(SERVER_URL.netloc)
datelong = xbmc.getRegion('datelong')
timestamp = xbmc.getRegion('time')


def get_url(**kwargs):
    """
    Create a URL for calling the plugin recursively from the given set of keyword arguments.

    :param kwargs: "argument=value" pairs
    :return: plugin call URL
    :rtype: str
    """
    return '{}?{}'.format(sys.argv[0], urlencode(kwargs))


def getThumbUrl(id):
    return f'{RAW_SERVER_URL}/api/assets/{id}/thumbnail|x-api-key={API_KEY}'
