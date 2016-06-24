import json
import re
import time

import xbmcplugin

import util
import player_config
import adobe_activate_api
from globals import selfAddon, defaultlive, defaultreplay, defaultupcoming, defaultimage, defaultfanart, translation, pluginhandle, LOG_LEVEL
from addon_util import *
from register_mode import RegisterMode

ROOT = ''

class MenuListing:
    def __init__(self, place):
        self.place = place

    def make_mode(self, destination):
        return '/' + self.place + '/' + destination
