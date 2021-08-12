# -*- coding: utf-8 -*-
# Copyright: (c) 2016, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals

from codequick import Script
from codequick.utils import ensure_unicode

from resources.lib.addon_utils import get_quality_YTDL
from resources.lib.kodi_utils import get_selected_item_label


def download_video(video_url):
    """Callback function of the 'Download' context menu

    Args:
        video_url (str): URL of the video to download
    """

    #  print('URL Video to download ' + video_url)

    #  Now that we have video URL we can try to download this one

    YDStreamExtractor = __import__('YDStreamExtractor')

    info = {'url': video_url, 'quality': get_quality_YTDL(download_mode=True)}

    path = ensure_unicode(Script.setting.get_string('dl_folder'))
    filename = ''
    if Script.setting.get_boolean('dl_item_filename'):
        filename = get_selected_item_label()
    bg = Script.setting.get_boolean('dl_background')
    YDStreamExtractor.handleDownload(info, bg=bg, path=path, filename=filename)

    return False
