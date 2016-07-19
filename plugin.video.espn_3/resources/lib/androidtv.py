import time
import base64

import xbmcplugin

import util
import adobe_activate_api
from globals import defaultlive, defaultfanart, translation, pluginhandle
from addon_util import *
from menu_listing import *
from register_mode import RegisterMode
import tvos

TAG = 'AndroidTV: '
PLACE = 'androidtv'

HOME = 'HOME'
ANDROID_HOME = 'ANDROID_HOME'
SPORTS = 'SPORTS'
CHANNELS = 'CHANNELS'
BUCKET = 'BUCKET'
URL_MODE = 'URL_MODE'
URL = 'URL'



class AndroidTV(tvos.TVOS):
    @RegisterMode(PLACE)
    def __init__(self):
        MenuListing.__init__(self, PLACE)

    @RegisterMode(ROOT)
    def root_menu(self, args):
        url = base64.b64decode(
            'aHR0cHM6Ly93YXRjaC5wcm9kdWN0LmFwaS5lc3BuLmNvbS9hcGkvcHJvZHVjdC92MS9hbmRyb2lkL3R2L2hvbWU=')
        self.parse_json(args, url)
        xbmcplugin.endOfDirectory(pluginhandle)

    @RegisterMode(URL_MODE)
    def url_mode(self, args):
        url = args.get(URL)[0]
        self.parse_json(args, url)
        xbmcplugin.endOfDirectory(pluginhandle)
