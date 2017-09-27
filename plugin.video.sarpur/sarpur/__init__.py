#!/usr/bin/env python
# encoding: UTF-8

import sys
import xbmcaddon


ALWAYS_REFRESH = False  # True
LOGGING_ENABLED = True

BASE_URL = sys.argv[0]
ADDON_HANDLE = int(sys.argv[1])
ADDON = xbmcaddon.Addon(id='plugin.video.sarpur')

PODCAST_URL = 'http://www.ruv.is/hladvarp'