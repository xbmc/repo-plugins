# -*- coding: utf-8 -*-
"""
    Catch-up TV & More
    Original work (C) JUL1EN094, SPM, SylvainCecchetto
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

import json
from resources.lib import utils
from resources.lib import common

# TO DO
# Replay add emissions
# Add info LIVE TV

# Initialize GNU gettext emulation in addon
# This allows to use UI strings from addon’s English
# strings.po file instead of numeric codes
_ = common.ADDON.initialize_gettext()

URL_LIVE_API = 'http://%s.euronews.com/api/watchlive.json'
# Language


def channel_entry(params):
    """Entry function of the module"""
    if 'root' in params.next:
        return root(params)
    elif 'list_shows' in params.next:
        return list_shows(params)
    elif 'list_videos' in params.next:
        return list_videos(params)
    elif 'live' in params.next:
        return list_live(params)
    elif 'play' in params.next:
        return get_video_url(params)
    return None


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def root(params):
    modes = []

    """
    # Add Replay Desactiver
    if params.channel_name != 'euronews':
        modes.append({
            'label': 'Replay',
            'url': common.PLUGIN.get_url(
                action='channel_entry',
                next='list_shows_1',
                category='%s Replay' % params.channel_name.upper(),
                window_title='%s Replay' % params.channel_name.upper()
            ),
        })

    # Add Live
    modes.append({
        'label': 'Live TV',
        'url': common.PLUGIN.get_url(
            action='channel_entry',
            next='live_cat',
            category='%s Live TV' % params.channel_name.upper(),
            window_title='%s Live TV' % params.channel_name.upper()
        ),
    })

    return common.PLUGIN.create_listing(
        modes,
        sort_methods=(
            common.sp.xbmcplugin.SORT_METHOD_UNSORTED,
            common.sp.xbmcplugin.SORT_METHOD_LABEL
        ),
    )
    """

    params.next = "list_live"
    return channel_entry(params)


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def list_shows(params):
    return None


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def list_videos(params):

    return None


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def list_live(params):

    lives = []

    title = ''
    plot = ''
    duration = 0
    img = ''
    url_live = ''

    desired_language = common.PLUGIN.get_setting(
        params.channel_id + '.language')

    if desired_language == 'FR':
        title = '%s Français Live' % (params.channel_name.upper())
    elif desired_language == 'EN':
        title = '%s English Live' % (params.channel_name.upper())
    elif desired_language == 'AR':
        title = '%s عربية Live' % (params.channel_name.upper())
    elif desired_language == 'DE':
        title = '%s Deutsch Live' % (params.channel_name.upper())
    elif desired_language == 'IT':
        title = '%s Italiano Live' % (params.channel_name.upper())
    elif desired_language == 'ES':
        title = '%s Español Live' % (params.channel_name.upper())
    elif desired_language == 'PT':
        title = '%s Português Live' % (params.channel_name.upper())
    elif desired_language == 'RU':
        title = '%s Русский Live' % (params.channel_name.upper())
    elif desired_language == 'TR':
        title = '%s Türkçe Live' % (params.channel_name.upper())
    elif desired_language == 'FA':
        title = '%s فارسی Live' % (params.channel_name.upper())
    elif desired_language == 'GR':
        title = '%s Ελληνικά Live' % (params.channel_name.upper())
    elif desired_language == 'HU':
        title = '%s Magyar Nyelv Live' % (params.channel_name.upper())

    if desired_language == 'EN':
        url_live_json = URL_LIVE_API % 'www'
    elif desired_language == 'AR':
        url_live_json = URL_LIVE_API % 'arabic'
    else:
        url_live_json = URL_LIVE_API % desired_language.lower()

    file_path = utils.download_catalog(
        url_live_json,
        '%s_%s_live.json' % (
            params.channel_name, desired_language.lower())
    )
    json_live = open(file_path).read()
    json_parser = json.loads(json_live)
    url_2nd_json = json_parser["url"]

    file_path_2 = utils.download_catalog(
        url_2nd_json,
        '%s_%s_live_2.json' % (
            params.channel_name, desired_language.lower())
    )
    json_live_2 = open(file_path_2).read()
    json_parser_2 = json.loads(json_live_2)

    url_live = json_parser_2["primary"]

    info = {
        'video': {
            'title': title,
            'plot': plot,
            'duration': duration
        }
    }

    lives.append({
        'label': title,
        'fanart': img,
        'thumb': img,
        'url': common.PLUGIN.get_url(
            action='channel_entry',
            next='play_l',
            url=url_live,
        ),
        'is_playable': True,
        'info': info
    })

    return common.PLUGIN.create_listing(
        lives,
        sort_methods=(
            common.sp.xbmcplugin.SORT_METHOD_UNSORTED,
            common.sp.xbmcplugin.SORT_METHOD_LABEL
        )
    )


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def get_video_url(params):

    if params.next == 'play_l':
        return params.url
