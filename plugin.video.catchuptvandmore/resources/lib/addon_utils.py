# -*- coding: utf-8 -*-
# Copyright: (c) 2016, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import os

# noinspection PyUnresolvedReferences
from codequick import Script, utils
import urlquick
# noinspection PyUnresolvedReferences
from kodi_six import xbmcgui, xbmcvfs


Quality = {
    "BEST": "0",
    "DEFAULT": "1",
    "DIALOG": "2",
    "WORST": "3"
}


def get_item_label(item_id, item_infos={}, append_selected_lang=True):
    """Get (translated) label of 'item_id'

    Args:
        item_id (str)
        item_infos (dict): Information from the skeleton 'menu' dict
        append_selected_lang (bool, optional): Append selected language by the user in the label
    Returns:
        str: (translated) label of 'item_id'
    """
    if 'label' in item_infos:
        label = item_infos['label']
    else:
        label = item_id

    if isinstance(label, int):
        label = Script.localize(label)

    if append_selected_lang and 'available_languages' in item_infos:
        label = '{} ({})'.format(label, utils.ensure_unicode(Script.setting['{}.language'.format(item_id)]))
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
        if quality == Quality['BEST']:
            return 3

        if quality == Quality['DEFAULT']:
            return 3

        if quality == Quality['DIALOG']:
            youtube_dl_quality = ['SD', '720p', '1080p', 'Highest Available']
            selected_item = xbmcgui.Dialog().select(
                Script.localize(30709),
                youtube_dl_quality)
            return selected_item

        if quality == Quality['WORST']:
            return 0

        return 3

    # Else we need to use the 'dl_quality' setting
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
