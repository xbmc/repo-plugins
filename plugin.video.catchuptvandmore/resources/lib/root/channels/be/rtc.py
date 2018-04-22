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

import ast
import re
from bs4 import BeautifulSoup as bs
from resources.lib import utils
from resources.lib import common


URL_ROOT = 'https://www.rtc.be'

URL_LIVE = URL_ROOT + '/live'

URL_VIDEOS = URL_ROOT + '/videos'

URL_EMISSIONS = URL_ROOT + '/emissions'


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

        category_name = common.GETTEXT('All videos')
        category_url = URL_VIDEOS
        shows.append({
            'label': category_name,
            'url': common.PLUGIN.get_url(
                module_path=params.module_path,
                module_name=params.module_name,
                action='replay_entry',
                category_url=category_url,
                category_name=category_name,
                next='list_videos_1',
                page='0',
                window_title=category_name
            )
        })

        replay_categories_html = utils.get_webcontent(URL_EMISSIONS)
        replay_categories_soup = bs(replay_categories_html, 'html.parser')
        categories = replay_categories_soup.find_all(
            'div', class_='col-sm-4')

        for category in categories:

            category_name = category.find('h3').get_text()
            category_img = URL_ROOT + '/' + category.find(
                'img').get('src')
            category_url = URL_ROOT + '/' + category.find(
                "a").get("href")
            shows.append({
                'label': category_name,
                'thumb': category_img,
                'url': common.PLUGIN.get_url(
                    module_path=params.module_path,
                    module_name=params.module_name,
                    action='replay_entry',
                    category_url=category_url,
                    category_name=category_name,
                    next='list_videos_1',
                    page='0',
                    window_title=category_name
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
    if 'previous_listing' in params:
        videos = ast.literal_eval(params['previous_listing'])

    if params.next == 'list_videos_1':
        list_videos_html = utils.get_webcontent(
            params.category_url + '?lim_un=%s' % params.page)
        list_videos_soup = bs(list_videos_html, 'html.parser')

        videos_data = list_videos_soup.find_all(
            'div', class_='col-sm-4')

        for video in videos_data:

            title = video.find('h3').get_text()
            plot = ''
            duration = 0
            img = video.find('img').get('src')
            video_url = video.find('a').get('href')

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

        # More videos...
        videos.append({
            'label': common.ADDON.get_localized_string(30700),
            'url': common.PLUGIN.get_url(
                module_path=params.module_path,
                module_name=params.module_name,
                action='replay_entry',
                next='list_videos_1',
                category_url = params.category_url,
                page=str(int(params.page) + 12),
                update_listing=True,
                previous_listing=str(videos)
            )
        })

    return common.PLUGIN.create_listing(
        videos,
        sort_methods=(
            common.sp.xbmcplugin.SORT_METHOD_UNSORTED
        ),
        content='tvshows',
        update_listing='update_listing' in params,
        category=common.get_window_title()
    )


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def get_live_item(params):
    plot = ''
    duration = 0
    img = 'https://www.rtc.be/images/direct.png'
    url_live = ''

    live_html = utils.get_webcontent(URL_LIVE)
    live_html_soup = bs(live_html, 'html.parser')
    live_iframe = 'https:' + live_html_soup.find(
        'iframe').get('src')
    live_iframe_html = utils.get_webcontent(live_iframe)
    live_iframe_soup = bs(live_iframe_html, 'html.parser')
    url_live = 'https:' + live_iframe_soup.find(
        'source').get('src')

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
            url=url_live,
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
            r'file: "(.*?)"').findall(video_html)
        stream_url = ''
        for stream in streams_url:
            if 'm3u8' in stream or \
                'mp4' in stream:
                stream_url = stream
        return stream_url
    elif params.next == 'play_l':
        return params.url
