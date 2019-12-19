# -*- coding: utf-8 -*-
"""
    Catch-up TV & More
    Copyright (C) 2016  SylvainCecchetto

    This file is part of Catch-up TV & More.

    Catch-up TV & More is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    Catch-up TV & More is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along
    with Catch-up TV & More; if not, write to the Free Software Foundation,
    Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""

# The unicode_literals import only has
# an effect on Python 2.
# It makes string literals as unicode like in Python 3
from __future__ import unicode_literals

import os
import sys
import pickle
import binascii

from kodi_six import xbmcgui
from kodi_six import xbmc
from kodi_six import xbmcvfs

try:
    from urllib.parse import urlunsplit
except ImportError:
    from urlparse import urlunsplit

import urlquick
from codequick import Script
from resources.lib.labels import LABELS


PY3 = sys.version_info[0] >= 3


def build_kodi_url(route_path, raw_params):
    # route_path: /resources/lib/channels/fr/mytf1/get_video_url/
    # raw_params: params dict
    if raw_params:
        pickled = binascii.hexlify(
            pickle.dumps(raw_params, protocol=pickle.HIGHEST_PROTOCOL))
        query = "_pickle_={}".format(
            pickled.decode("ascii") if PY3 else pickled)

    # Build kodi url
    return urlunsplit(
        ("plugin", "plugin.video.catchuptvandmore", route_path, query, ""))


def get_quality_YTDL(download_mode=False):
    # If not download mode get the 'quality' setting
    if not download_mode:
        quality = Script.setting.get_string('quality')
        if quality == 'BEST':
            return 3
        elif quality == 'DEFAULT':
            return 3
        elif quality == 'DIALOG':
            youtubeDL_qualiy = ['SD', '720p', '1080p', 'Highest Available']
            seleted_item = xbmcgui.Dialog().select(
                Script.localize(LABELS['choose_video_quality']),
                youtubeDL_qualiy)
            return seleted_item

        else:
            return 3

    # Else we need to use the 'dl_quality' setting
    elif download_mode:
        dl_quality = Script.setting.get_string('dl_quality')
        if dl_quality == 'SD':
            return 0
        if dl_quality == '720p':
            return 1
        if dl_quality == '1080p':
            return 2
        if dl_quality == 'Highest available':
            return 3
        return 3


def get_kodi_version():
    xbmc_version = xbmc.getInfoLabel("System.BuildVersion")
    return int(xbmc_version.split('-')[0].split('.')[0])


@Script.register
def clear_cache(plugin):
    # Callback function of clear cache setting button

    # Clear urlquick cache
    urlquick.cache_cleanup(-1)
    Script.notify(plugin.localize(30371), '')

    # Remove all tv guides
    dirs, files = xbmcvfs.listdir(Script.get_info('profile'))
    for fn in files:
        if '.xml' in fn and fn != 'settings.xml':
            Script.log('Remove xmltv file: {}'.format(fn))
            xbmcvfs.delete(os.path.join(Script.get_info('profile'), fn))
