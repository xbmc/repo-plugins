# -*- coding: utf-8 -*-
"""
    Catch-up TV & More
    Copyright (C) 2017  SylvainCecchetto

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

import re
from resources.lib import utils
from resources.lib import common

# Initialize GNU gettext emulation in addon
# This allows to use UI strings from addon’s English
# strings.po file instead of numeric codes
_ = common.ADDON.initialize_gettext()

URL_ROOT = 'http://www.dw.com'


def channel_entry(params):
    """Entry function of the module"""
    if 'list_shows' in params.next:
        return list_shows(params)
    elif 'list_videos' in params.next:
        return list_videos(params)
    elif 'play' in params.next:
        return get_video_url(params)
    return None


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def list_shows(params):
    return None


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def list_videos(params):
    return None


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def get_live_item(params):
    title = ''
    plot = ''
    duration = 0
    img = ''
    url_live = ''

    desired_language = common.PLUGIN.get_setting(
        params.channel_name + '.language')

    if desired_language == 'EN':
        title = '%s English Live' % (params.channel_label)
    elif desired_language == 'AR':
        title = '%s عربية Live' % (params.channel_label)
    elif desired_language == 'DE':
        title = '%s Deutsch Live' % (params.channel_label)
    elif desired_language == 'ES':
        title = '%s Español Live' % (params.channel_label)

    file_path = utils.get_webcontent(
        URL_ROOT + '/%s' % desired_language.lower())
    url_lives = re.compile(
        r'name="file_name" value="(.*?)"').findall(file_path)

    for urls in url_lives:
        if 'm3u8' in urls:
            url_live = urls

    info = {
        'video': {
            'title': title,
            'plot': plot,
            'duration': duration
        }
    }

    return {
        'label': title,
        'fanart': img,
        'thumb': img,
        'url': common.PLUGIN.get_url(
            module_path=params.module_path,
            module_name=params.module_name,
            action='start_live_tv_stream',
            next='play_l',
            url=url_live,
        ),
        'is_playable': True,
        'info': info
    }


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def get_video_url(params):
    """Get video URL and start video player"""
    if params.next == 'play_l':
        return params.url
