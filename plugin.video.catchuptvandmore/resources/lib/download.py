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
from kodi_six import xbmcvfs
from codequick import Script
from resources.lib.addon_utils import get_quality_YTDL
from resources.lib.kodi_utils import get_selected_item_label


def download_video(video_url):
    """Callback function of the 'Download' context menu

    Args:
        video_url (str): URL of the video to download
    """

    #  print('URL Video to download ' + video_url)

    #  Now that we have video URL we can try to download this one
    YDStreamUtils = __import__('YDStreamUtils')
    YDStreamExtractor = __import__('YDStreamExtractor')

    vid = YDStreamExtractor.getVideoInfo(
        video_url,
        quality=get_quality_YTDL(download_mode=True),
        resolve_redirects=True)

    path = Script.setting.get_string('dl_folder')
    download_ok = False
    with YDStreamUtils.DownloadProgress() as prog:
        try:
            YDStreamExtractor.setOutputCallback(prog)
            result = YDStreamExtractor.handleDownload(
                vid, bg=Script.setting.get_boolean('dl_background'), path=path)
            if result:
                if result.status == 'canceled':
                    error_message = result.message
                    Script.log('Download failed: %s' % error_message)
                else:
                    full_path_to_file = result.filepath
                    Script.log('Download success: %s' % full_path_to_file)
                    download_ok = True

        finally:
            YDStreamExtractor.setOutputCallback(None)

    if path != '' and \
            Script.setting.get_boolean('dl_item_filename') and \
            download_ok:

        try:
            filename = os.path.basename(full_path_to_file)
            _, file_extension = os.path.splitext(full_path_to_file)
            current_filepath = os.path.join(path, filename)
            video_name = get_selected_item_label()
            final_filepath = os.path.join(path, video_name + file_extension)
            xbmcvfs.rename(current_filepath, final_filepath)
        except Exception:
            Script.log('Failed to rename video file')

    return False
