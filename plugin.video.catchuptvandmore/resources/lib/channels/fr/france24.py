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

import time
import re
import json
from bs4 import BeautifulSoup as bs
from resources.lib import utils
from resources.lib import common

# TO DO
# Replay (emission) | (just 5 first episodes) Add More Button (with api) to download just some part ? (More Work TO DO)
# Add info LIVE TV (picture, plot)
# Add Video, Last JT, Last ECO, Last Meteo
# Select Language settings not show

# Initialize GNU gettext emulation in addon
# This allows to use UI strings from addon’s English
# strings.po file instead of numeric codes
_ = common.ADDON.initialize_gettext()

URL_LIVE_SITE = 'http://www.france24.com/%s/'
# Language

URL_INFO_LIVE = 'http://www.france24.com/%s/_fragment/player/nowplaying/'
# Language

URL_API_VOD = 'http://api.france24.com/%s/services/json-rpc/emission_list?databases=f24%s&key=XXX' \
              '&start=0&limit=50&edition_start=0&edition_limit=5'
# language

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

@common.PLUGIN.cached(common.CACHE_TIME)
def root(params):
    """Add Replay and Live in the listing"""
    modes = []

    # Add Replay
    modes.append({
        'label' : 'Replay',
        'url': common.PLUGIN.get_url(
            action='channel_entry',
            next='list_shows_1',
            category='%s Replay' % params.channel_name.upper(),
            window_title='%s Replay' % params.channel_name.upper()
        ),
    })

    # Add Live
    modes.append({
        'label' : 'Live TV',
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

@common.PLUGIN.cached(common.CACHE_TIME)
def list_shows(params):
    """Build shows listing"""
    shows = []

    desired_language = common.PLUGIN.get_setting(
        params.channel_id + '.language')

    if params.next == 'list_shows_1':
        file_path = utils.download_catalog(
            URL_API_VOD % (desired_language.lower(),desired_language.lower()),
            '%s_%s_vod.json' % (params.channel_name,desired_language.lower())
        )
        json_vod = open(file_path).read()
        json_parser = json.loads(json_vod)

        list_caterories = json_parser["result"]["f24%s" % desired_language.lower()]["list"]
        for category in list_caterories:

            category_name = category["title"].encode('utf-8')
            img = category["image"][0]["original"].encode('utf-8')
            nid = category["nid"]
            url = category["url"].encode('utf-8')

            shows.append({
                'label': category_name,
                'fanart': img,
                'thumb': img,
                'url': common.PLUGIN.get_url(
                    action='channel_entry',
                    next='list_videos_cat',
                    nid=nid,
                    url=url,
                    window_title=category_name,
                    category_name=category_name,
                )
            })

    return common.PLUGIN.create_listing(
        shows,
        sort_methods=(
            common.sp.xbmcplugin.SORT_METHOD_UNSORTED,
            common.sp.xbmcplugin.SORT_METHOD_LABEL
        ),
    )

@common.PLUGIN.cached(common.CACHE_TIME)
def list_videos(params):
    """Build videos listing"""
    videos = []

    desired_language = common.PLUGIN.get_setting(
        params.channel_id + '.language')

    file_path = utils.download_catalog(
        URL_API_VOD % (desired_language.lower(), desired_language.lower()),
        '%s_%s_vod.json' % (params.channel_name, desired_language.lower())
    )
    json_vod = open(file_path).read()
    json_parser = json.loads(json_vod)

    list_caterories = json_parser["result"]["f24%s" % desired_language.lower()]["list"]
    for category in list_caterories:
        if str(params.nid) == str(category["nid"]):
            for video in category["editions"]["list"]:

                title = video["title"].encode('utf-8')
                plot = video["intro"].encode('utf-8')
                img = video["image"][0]["original"].encode('utf-8')
                url = video["video"][0]["mp4-mbr"].encode('utf-8')

                value_date = time.strftime('%d %m %Y', time.localtime(int(video["created"])))
                date = str(value_date).split(' ')
                day = date[0]
                mounth = date[1]
                year = date[2]
                date = '.'.join((day, mounth, year))
                aired = '-'.join((year, mounth, day))

                info = {
                    'video': {
                        'title': title,
                        'aired': aired,
                        'date': date,
                        #'duration': video_duration,
                        'year': year,
                        'plot' : plot,
                        'mediatype': 'tvshow'
                    }
                }

                context_menu = []
                download_video = (
                    _('Download'),
                    'XBMC.RunPlugin(' + common.PLUGIN.get_url(
                        action='download_video',
                        url=url) + ')'
                )
                context_menu.append(download_video)

                videos.append({
                    'label': title,
                    'thumb': img,
                    'fanart': img,
                    'url': common.PLUGIN.get_url(
                        action='channel_entry',
                        next='play_r',
                        url=url
                    ),
                    'is_playable': True,
                    'info': info,
                    'context_menu': context_menu
                })


    # TO DO add More button Video

    return common.PLUGIN.create_listing(
        videos,
        sort_methods=(
            common.sp.xbmcplugin.SORT_METHOD_UNSORTED,
            common.sp.xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE
        ),
        content='tvshows')

@common.PLUGIN.cached(common.CACHE_TIME)
def list_live(params):
    """Build live listing"""
    lives = []

    title = ''
    plot = ''
    duration = 0
    img = ''
    url_live = ''

    desired_language = common.PLUGIN.get_setting(
        params.channel_id + '.language')

    url_live = URL_LIVE_SITE % desired_language.lower()

    file_path = utils.download_catalog(
        url_live,
        '%s_%s_live.html' % (params.channel_name, desired_language.lower())
    )
    html_live = open(file_path).read()
    root_soup = bs(html_live, 'html.parser')

    json_parser = json.loads(root_soup.select_one("script[type=application/json]").text)
    media_datas_list = json_parser['medias']['media']['media_sources']['media_source']
    for datas in media_datas_list:
        if datas['source']:
            url_live = datas['source']

    live_info = utils.get_webcontent(URL_INFO_LIVE % (desired_language.lower()))
    title = re.compile('id="main-player-playing-value">(.+?)<').findall(live_info)[0]

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
        'url' : common.PLUGIN.get_url(
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

@common.PLUGIN.cached(common.CACHE_TIME)
def get_video_url(params):
    """Get video URL and start video player"""
    if params.next == 'play_l':
        return params.url
    elif params.next == 'play_r' or params.next == 'download_video':
        return params.url

