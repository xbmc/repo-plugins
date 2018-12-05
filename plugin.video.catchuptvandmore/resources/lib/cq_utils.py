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

from codequick import Script
from resources.lib.labels import LABELS


def item2dict(item):
    item_dict = {}
    item_dict['art'] = dict(item.art)
    item_dict['info'] = dict(item.info)
    item_dict['stream'] = dict(item.stream)
    item_dict['context'] = dict(item.context)
    item_dict['property'] = item.property
    item_dict['params'] = item.params
    item_dict['label'] = item.label
    return item_dict


def find_module_in_url(base_url):
    # e.g. base_url = plugin://plugin.video.catchuptvandmore/resources/lib/websites/culturepub/list_shows
    base_url_l = base_url.split('/')
    module_l = []
    addon_name_triggered = False
    for name in base_url_l:
        if addon_name_triggered:
            module_l.append(name)
            continue
        if name == 'plugin.video.catchuptvandmore':
            addon_name_triggered = True
    module_l.pop()  # Pop the function name (e.g. list_shows)
    module = '.'.join(module_l)
    # Returned module: resources.lib.websites.culturepub
    return module


def import_needed_module():
    # Import needed module according to the
    # base URL (Fix for Kodi favorite item)
    module_to_import = find_module_in_url(sys.argv[0])
    try:
        importlib.import_module(module_to_import)
    except Exception:
        pass

    module_to_load_2 = Script.setting['module_to_load']
    if module_to_load_2 != '':
        try:
            importlib.import_module(module_to_load_2)
        except Exception:
            pass
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
