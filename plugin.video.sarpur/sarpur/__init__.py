#!/usr/bin/env python
# encoding: UTF-8

import sys
import xbmcaddon

ALWAYS_REFRESH = False
LOGGING_ENABLED = True

BASE_URL = sys.argv[0]
ADDON_HANDLE = int(sys.argv[1])
ADDON = xbmcaddon.Addon(id='plugin.video.sarpur')

LIVE_URLS = {
    "ruv": "http://sip-live.hds.adaptive.level3.net/hls-live/ruv-ruv/_definst_/live.m3u8",
    "ras1": "http://sip-live.hds.adaptive.level3.net/hls-live/ruv-ras1/_definst_/live.m3u8",
    "ras2": "http://sip-live.hds.adaptive.level3.net/hls-live/ruv-ras2/_definst_/live.m3u8",
    'rondo': 'http://sip-live.hds.adaptive.level3.net/hls-live/ruv-ras3/_definst_/live.m3u8'
}

