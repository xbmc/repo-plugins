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
from bs4 import BeautifulSoup as bs
from resources.lib import utils
from resources.lib import common


URL_ROOT = 'http://www.arirang.com/mobile/'

URL_EMISSION = URL_ROOT + 'tv_main.asp'
# URL STREAM below present in this URL in mobile phone

URL_STREAM = 'http://amdlive.ctnd.com.edgesuite.net/' \
             'arirang_1ch/smil:arirang_1ch.smil/playlist.m3u8'


def channel_entry(params):
    """Entry function of the module"""
    if 'replay_entry' == params.next:
        params.next = "list_shows_1"
        return list_shows(params)
    elif 'list_shows' in params.next:
        return list_shows(params)
    elif 'list_videos' in params.next:
        return list_videos(params)
    elif 'play' in params.next:
        return get_video_url(params)
    return None


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def list_shows(params):
    """Build categories listing"""
    shows = []

    if params.next == 'list_shows_1':

        replay_categories_html = utils.get_webcontent(URL_EMISSION)
        replay_categories_soup = bs(replay_categories_html, 'html.parser')
        categories = replay_categories_soup.find(
            'ul', class_='amenu_tab amenu_tab_3 amenu_tab_sub').find_all(
                'li')

        for category in categories:

            category_name = category.find('a').get_text()
            category_url = URL_ROOT + category.find(
                "a").get("href")
            shows.append({
                'label': category_name,
                'url': common.PLUGIN.get_url(
                    module_path=params.module_path,
                    module_name=params.module_name,
                    action='replay_entry',
                    category_url=category_url,
                    category_name=category_name,
                    next='list_shows_2',
                    window_title=category_name
                )
            })

    elif params.next == 'list_shows_2':

        replay_shows_html = utils.get_webcontent(params.category_url)
        replay_shows_soup = bs(replay_shows_html, 'html.parser')
        show_lists = replay_shows_soup.find_all(
            'dl', class_='alist amain_tv')

        for show in show_lists:

            show_name = show.find('img').get('alt')
            show_img = show.find('img').get('src')
            show_url = URL_ROOT + show.find(
                "a").get("href")
            shows.append({
                'label': show_name,
                'thumb': show_img,
                'url': common.PLUGIN.get_url(
                    module_path=params.module_path,
                    module_name=params.module_name,
                    action='replay_entry',
                    show_url=show_url,
                    show_name=show_name,
                    next='list_videos_1',
                    window_title=show_name
                )
            })

    return common.PLUGIN.create_listing(
        shows,
        sort_methods=(
            common.sp.xbmcplugin.SORT_METHOD_UNSORTED,
            common.sp.xbmcplugin.SORT_METHOD_LABEL
        ),
        category=common.get_window_title()
    )


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def list_videos(params):
    """Build videos listing"""
    videos = []

    if params.next == 'list_videos_1':
        list_videos_html = utils.get_webcontent(
            params.show_url)
        list_videos_soup = bs(list_videos_html, 'html.parser')

        videos_data = list_videos_soup.find_all(
            'dl', class_='alist')

        for video in videos_data:

            title = video.find('img').get('alt')
            plot = ''
            duration = 0
            img = video.find('img').get('src')
            video_url = video.find('a').get('href')
            video_url = re.compile(
                r'\(\'(.*?)\'\)').findall(
                    video_url)[0]

            info = {
                'video': {
                    'title': title,
                    'plot': plot,
                    # 'aired': aired,
                    # 'date': date,
                    'duration': duration,
                    # 'year': year,
                    'mediatype': 'tvshow'
                }
            }

            download_video = (
                common.GETTEXT('Download'),
                'XBMC.RunPlugin(' + common.PLUGIN.get_url(
                    action='download_video',
                    module_path=params.module_path,
                    module_name=params.module_name,
                    video_url=video_url) + ')'
            )
            context_menu = []
            context_menu.append(download_video)

            videos.append({
                'label': title,
                'thumb': img,
                'url': common.PLUGIN.get_url(
                    module_path=params.module_path,
                    module_name=params.module_name,
                    action='replay_entry',
                    next='play_r',
                    video_url=video_url,
                ),
                'is_playable': True,
                'info': info,
                'context_menu': context_menu
            })

    return common.PLUGIN.create_listing(
        videos,
        sort_methods=(
            common.sp.xbmcplugin.SORT_METHOD_UNSORTED
        ),
        content='tvshows',
        category=common.get_window_title()
    )


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def get_live_item(params):
    plot = ''
    duration = 0
    img = ''
    live_url = ''

    live_url = URL_STREAM

    info = {
        'video': {
            'title': params.channel_label,
            'plot': plot,
            'duration': duration
        }
    }

    return {
        'label': params.channel_label,
        'fanart': img,
        'thumb': img,
        'url': common.PLUGIN.get_url(
            module_path=params.module_path,
            module_name=params.module_name,
            action='start_live_tv_stream',
            next='play_l',
            live_url=live_url
        ),
        'is_playable': True,
        'info': info
    }


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def get_video_url(params):
    """Get video URL and start video player"""
    if params.next == 'play_r' or params.next == 'download_video':
        video_html = utils.get_webcontent(params.video_url)
        streams_url = re.compile(
            r'mediaurl: \'(.*?)\'').findall(video_html)
        stream_url = ''
        for stream in streams_url:
            if 'm3u8' in stream:
                stream_url = stream
        return stream_url
    elif params.next == 'play_l':
        return params.live_url
