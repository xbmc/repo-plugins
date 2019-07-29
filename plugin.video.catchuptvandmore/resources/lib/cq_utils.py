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
import importlib
import xbmcgui
import xbmc
import sys

try:
    import urllib.parse as urlparse
except ImportError:
    # noinspection PyUnresolvedReferences
    import urlparse

from codequick import Script
from resources.lib.labels import LABELS
from codequick.utils import parse_qs

import pickle
import binascii

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
    return urlparse.urlunsplit(
        ("plugin", "plugin.video.catchuptvandmore", route_path, query, ""))


def get_params_in_query(query_string):
    params = parse_qs(query_string)

    # Unpickle pickled data
    if "_pickle_" in params:
        unpickled = pickle.loads(binascii.unhexlify(params.pop("_pickle_")))
        params.update(unpickled)

    return params


def get_module_in_url(base_url):
    # e.g. base_url = plugin://plugin.video.catchuptvandmore/resources/lib/websites/culturepub/list_shows
    if 'resources' not in base_url:
        return ''

    # Remove last '/'
    if base_url[-1] == '/':
        base_url = base_url[:-1]

    # Remove plugin_id
    base_url = base_url.replace('plugin://plugin.video.catchuptvandmore/', '')

    base_url_l = base_url.split('/')
    module_l = []
    for word in base_url_l:
        module_l.append(word)

    module_l.pop()  # Pop the function name (e.g. list_shows)
    module = '.'.join(module_l)
    # Returned module: resources.lib.websites.culturepub
    return module


def get_module_in_query(query_string):
    module = ''
    params = get_params_in_query(query_string)
    # '_route': u'/resources/lib/channels/fr/francetv/list_videos_search/'
    if '_route' in params:
        base_url = params['_route']
        # Remove last '/'
        if base_url[-1] == '/':
            base_url = base_url[:-1]

        # Remove first '/'
        if base_url[0] == '/':
            base_url = base_url[1:]

        base_url_l = base_url.split('/')
        module_l = []
        for word in base_url_l:
            module_l.append(word)

        module_l.pop()  # Pop the function name (e.g. list_videos_search)
        module = '.'.join(module_l)
        # Returned module: resources.lib.channels.fr.francetv

    return module


def import_needed_module():
    # Import needed module according to the
    # base URL and query string (Fix for Kodi favorite item and search)
    modules_to_import = [get_module_in_url(sys.argv[0])]
    if 'codequick/search' in sys.argv[0]:
        modules_to_import.append(get_module_in_query(sys.argv[2]))
    for module_to_import in modules_to_import:
        if module_to_import == '':
            # No additionnal module to load
            continue

        # Need to load additional module
        try:
            Script.log('[cq_utils.import_needed_module] Import module {} on the fly'.format(module_to_import), lvl=Script.INFO)
            importlib.import_module(module_to_import)
        except Exception:
            Script.log('[cq_utils.import_needed_module] Failed to import module {} on the fly'.format(module_to_import), lvl=Script.WARNING)

    return


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
