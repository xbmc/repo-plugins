# -*- coding: utf-8 -*-
# Copyright: (c) 2016, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import binascii
import pickle
import sys
try:
    from urllib.parse import urlunsplit
except ImportError:
    from urlparse import urlunsplit

from codequick.utils import parse_qs

from kodi_six import xbmc


PY3 = sys.version_info[0] >= 3


# Handler functions of Kodi versions

def get_kodi_version():
    """Get Kodi major version

    Returns:
        int: Kodi major version (e.g. 18)
    """
    xbmc_version = xbmc.getInfoLabel("System.BuildVersion")
    return int(xbmc_version.split('-')[0].split('.')[0])


INPUTSTREAM_PROP = 'inputstream' if get_kodi_version() >= 19 else 'inputstreamaddon'


# Kodi InfoLabel functions

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


# Kodi URL/sys.argv utility functions

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
