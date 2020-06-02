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

# Core imports
import os

# Kodi imports
from kodi_six import xbmcgui
from kodi_six import xbmc
from kodi_six import xbmcvfs
from resources.lib.codequick import Script, utils
from resources.lib import urlquick


# Local imports
from resources.lib.labels import LABELS


def get_item_label(item_id):
    """Get (translated) label of 'item_id'

    Args:
        item_id (str)
    Returns:
        str: (translated) label of 'item_id'
    """
    label = item_id
    if item_id in LABELS:
        label = LABELS[item_id]
        if isinstance(label, int):
            label = Script.localize(label)
    return label


def get_item_media_path(item_media_path):
    """Get full path or URL of an item_media

    Args:
        item_media_path (str or list): Partial media path of the item (e.g. channels/fr/tf1.png)
    Returns:
        str: Full path or URL of the item_pedia
    """
    full_path = ''

    # Local image in ressources/media folder
    if type(item_media_path) is list:
        full_path = os.path.join(Script.get_info("path"), "resources", "media",
                                 *(item_media_path))

    # Remote image with complete URL
    elif 'http' in item_media_path:
        full_path = item_media_path

    # Image in our resource.images add-on
    else:
        full_path = 'resource://resource.images.catchuptvandmore/' + item_media_path

    return utils.ensure_native_str(full_path)


def get_quality_YTDL(download_mode=False):
    """Get YoutTubeDL quality setting

    Args:
        download_mode (bool)
    Returns:
        int: YoutTubeDL quality
    """

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


@Script.register
def clear_cache(plugin):
    """Callback function of clear cache setting button

    Args:
        plugin (codequick.script.Script)
    """

    # Clear urlquick cache
    urlquick.cache_cleanup(-1)
    Script.notify(plugin.localize(30371), '')

    # Remove all tv guides
    dirs, files = xbmcvfs.listdir(Script.get_info('profile'))
    for fn in files:
        if '.xml' in fn and fn != 'settings.xml':
            Script.log('Remove xmltv file: {}'.format(fn))
            xbmcvfs.delete(os.path.join(Script.get_info('profile'), fn))
