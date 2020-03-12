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
import numbers
import time
import pickle
import binascii
import importlib
try:
    from urllib.parse import urlunsplit
except ImportError:
    from urlparse import urlunsplit

from codequick.script import Script
from codequick.utils import ensure_native_str, parse_qs

from kodi_six import xbmc

from resources.lib.labels import LABELS

PY3 = sys.version_info[0] >= 3

"""Kodi InfoLabel functions

"""


def get_kodi_version():
    """Get Kodi major version

    Returns:
        int: Kodi major version (e.g. 18)
    """
    xbmc_version = xbmc.getInfoLabel("System.BuildVersion")
    return int(xbmc_version.split('-')[0].split('.')[0])


def get_selected_item_art():
    """Get 'art' dict of the selected item in the current Kodi menu

    Returns:
        dict: Selected item 'art' dict
    """
    art = {}
    for art_type in ['thumb', 'poster', 'banner', 'fanart', 'clearart', 'clearlogo', 'landscape', 'icon']:
        v = xbmc.getInfoLabel('ListItem.Art({})'.format(art_type))
        art[art_type] = v
    return art


def get_selected_item_label():
    """Get label the selected item in the current Kodi menu

    Returns:
        str: Selected item label
    """
    return xbmc.getInfoLabel('ListItem.Label')


def get_selected_item_params():
    """Get 'params' dict of the selected item in the current Kodi menu

    Returns:
        dict: Selected item 'params' dict
    """
    path = xbmc.getInfoLabel('ListItem.FilenameAndPath')
    return get_params_in_query(path)


def get_selected_item_stream():
    """Get 'stream' dict of the selected item in the current Kodi menu

    Returns:
        dict: Selected item 'stream' dict
    """
    stream = {}
    stream['video_codec'] = xbmc.getInfoLabel('ListItem.VideoCodec')
    stream['aspect'] = xbmc.getInfoLabel('ListItem.VideoAspect')
    stream['aspect'] = float(stream['aspect']) if stream['aspect'] != '' else stream['aspect']
    # stream['width'] (TODO)
    # stream['channels'] (TODO)
    stream['audio_codec'] = xbmc.getInfoLabel('ListItem.VideoCodec')
    stream['audio_language'] = xbmc.getInfoLabel('ListItem.AudioLanguage')
    stream['subtitle_language'] = xbmc.getInfoLabel('ListItem.SubtitleLanguage')
    return stream


def get_selected_item_info():
    """Get 'info' dict of the selected item in the current Kodi menu

    Returns:
        dict: Selected item 'info' dict
    """
    info = {}
    info['plot'] = xbmc.getInfoLabel('ListItem.Plot')
    return info


"""Kodi URL/sys.argv utility functions

"""


def build_kodi_url(route_path, raw_params):
    """Build a valid Kodi URL

    Args:
        route_path (str): (e.g. /resources/lib/channels/fr/mytf1/get_video_url/)
        raw_params (dict): Paramters dict
    Returns:
        str: Valid kodi URL (e.g. plugin://plugin.video.catchuptvandmore/resources/lib/channels/fr/mytf1/get_video_url/?foo=bar&baz=quux)
    """
    if raw_params:
        pickled = binascii.hexlify(
            pickle.dumps(raw_params, protocol=pickle.HIGHEST_PROTOCOL))
        query = "_pickle_={}".format(
            pickled.decode("ascii") if PY3 else pickled)

    return urlunsplit(
        ("plugin", "plugin.video.catchuptvandmore", route_path, query, ""))


def get_params_in_query(query_string):
    """Get parameters dict from Kodi query (sys.argv[2])

    Args:
        query_string (str): Query string passed to the addon (e.g. ?foo=bar&baz=quux)
    Returns:
        dict: Paramters found in the query string
    """

    params = parse_qs(query_string)

    # Unpickle pickled data
    if "_pickle_" in params:
        unpickled = pickle.loads(binascii.unhexlify(params.pop("_pickle_")))
        params.update(unpickled)

    return params


def get_module_in_query(query_string):
    """Get module from Kodi query (sys.argv[2]) in CodeQuick special case (Search feature)

    Args:
        query_string (str): Query string passed to the addon (e.g. ?foo=bar&baz=quux)
    Returns:
        str: Module to load after the Search window (e.g. resources.lib.channels.fr.francetv)
    """

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


def get_module_in_url(base_url):
    """Get module from Kodi base URL (sys.argv[0])

    Args:
        base_url (str): Base URL string passed to the addon (e.g. plugin://plugin.video.catchuptvandmore/resources/lib/websites/culturepub/list_shows)
    Returns:
        str: Module found in the base URL (e.g. resources.lib.websites.culturepub)
    """

    if 'resources' not in base_url:
        return 'resources.lib.main'

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

    return module


def import_needed_module():
    """Import needed module according to the Kodi base URL and query string

    TODO: Remove this import 'hack' when CodeQuick 0.9.11 will be released

    """

    modules_to_import = [get_module_in_url(sys.argv[0])]
    if 'codequick/search' in sys.argv[0]:
        modules_to_import.append(get_module_in_query(sys.argv[2]))
    for module_to_import in modules_to_import:
        if module_to_import == '':
            # No additionnal module to load
            continue

        # Need to load additional module
        try:
            Script.log('[import_needed_module] Import module {} on the fly'.format(module_to_import), lvl=Script.INFO)
            importlib.import_module(module_to_import)
        except Exception:
            Script.log('[import_needed_module] Failed to import module {} on the fly'.format(module_to_import), lvl=Script.WARNING)
