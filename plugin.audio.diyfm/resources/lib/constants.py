import os
import sys

import xbmc
import xbmcaddon


ADDON_ID = 'plugin.audio.diyfm'
ADDON = xbmcaddon.Addon(id=ADDON_ID)
PLUGIN_HANDLE = int(sys.argv[1])
PROJECT_ROOT = ADDON.getAddonInfo('path')
DATA_DIR = os.path.join(PROJECT_ROOT, 'resources', 'data')
USER_DATA_DIR = xbmc.translatePath(ADDON.getAddonInfo('profile'))
RADIO_FILE_PATH = os.path.join(DATA_DIR, 'groupRadioStations.xml')
API_KEY = ADDON.getSetting('api_key')
API_URL = "http://diy.fm/rest/v1/media/podcasts.xml?apiKey=%s" % API_KEY
API_USER_URL = "https://diy.fm/rest/v1/user/token.xml?apiKey=%s" % API_KEY
API_PERS_RADIO_URL = 'http://diy.fm/rest/v1/setting/overview.xml?apiKey=%(api_key)s&userToken=%(user_token)s'
DATE_FORMAT = '%d-%m-%Y'
