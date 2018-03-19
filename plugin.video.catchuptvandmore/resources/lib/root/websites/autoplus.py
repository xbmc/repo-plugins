# -*- coding: utf-8 -*-
'''
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
'''

import ast
import json
import re
from bs4 import BeautifulSoup as bs
from resources.lib import utils
from resources.lib import resolver
from resources.lib import common


URL_ROOT = 'https://video.autoplus.fr'


def website_entry(params):
    """Entry function of the module"""
    if 'root' in params.next:
        return root(params)
    elif 'list_shows' in params.next:
        return list_shows(params)
    elif 'list_videos' in params.next:
        return list_videos(params)
    elif 'play' in params.next:
        return get_video_url(params)
    return None


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def root(params):
    """Add modes in the listing"""
    modes = []

    category_title = common.GETTEXT('All videos')

    modes.append({
        'label': category_title,
        'url': common.PLUGIN.get_url(
            module_path=params.module_path,
            module_name=params.module_name,
            action='website_entry',
            next='list_videos_1',
            title=category_title,
            page='1',
            window_title=category_title
        )
    })

    return common.PLUGIN.create_listing(
        modes,
        sort_methods=(
            common.sp.xbmcplugin.SORT_METHOD_LABEL,
            common.sp.xbmcplugin.SORT_METHOD_UNSORTED
        ),
        category=common.get_window_title()
    )


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def list_shows(params):
    return None


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def list_videos(params):
    """Build videos listing"""
    videos = []
    if 'previous_listing' in params:
        videos = ast.literal_eval(params['previous_listing'])

    if params.next == 'list_videos_1':

        replay_episodes_html = utils.get_webcontent(
            URL_ROOT + '/?page=%s' % params.page)
        replay_episodes_soup = bs(replay_episodes_html, 'html.parser')

        # Get Video First Page
        if replay_episodes_soup.find('iframe'):
            url_first_video = replay_episodes_soup.find(
                'iframe').get('src')
            info_first_video = utils.get_webcontent(url_first_video)
            info_first_video_json = re.compile(
                'config = (.*?)};').findall(info_first_video)[0]
            info_first_video_jsonparser = json.loads(
                info_first_video_json + '}')

            video_title = info_first_video_jsonparser["metadata"]["title"]
            video_url = info_first_video_jsonparser["metadata"]["url"] + '?'
            video_img = info_first_video_jsonparser["metadata"]["poster_url"]
            video_duration = 0

            info = {
                'video': {
                    'title': video_title,
                    # 'aired': aired,
                    # 'date': date,
                    'duration': video_duration,
                    # 'plot': video_plot,
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
                'label': video_title,
                'thumb': video_img,
                'url': common.PLUGIN.get_url(
                    module_path=params.module_path,
                    module_name=params.module_name,
                    action='website_entry',
                    next='play_r',
                    video_url=video_url
                ),
                'is_playable': True,
                'info': info,
                'context_menu': context_menu
            })

        episodes = replay_episodes_soup.find_all(
            'div', class_='col-xs-6 col-sm-12')

        for episode in episodes:
            video_title = episode.find('img').get('alt')
            video_url = episode.find('a').get('href')
            video_img = episode.find(
                'img').get('src').replace('|','%7C')
            video_duration = 0

            info = {
                'video': {
                    'title': video_title,
                    # 'aired': aired,
                    # 'date': date,
                    'duration': video_duration,
                    # 'plot': video_plot,
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
                'label': video_title,
                'thumb': video_img,
                'url': common.PLUGIN.get_url(
                    module_path=params.module_path,
                    module_name=params.module_name,
                    action='website_entry',
                    next='play_r',
                    video_url=video_url
                ),
                'is_playable': True,
                'info': info,
                'context_menu': context_menu
            })

        # More videos...
        videos.append({
            'label': '# ' + common.ADDON.get_localized_string(30700),
            'url': common.PLUGIN.get_url(
                module_path=params.module_path,
                module_name=params.module_name,
                action='website_entry',
                next='list_videos_1',
                page=str(int(params.page) + 1),
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
def get_video_url(params):
    """Get video URL and start video player"""

    video_html = utils.get_webcontent(params.video_url)
    # Get DailyMotion Id Video
    video_id = re.compile(
        r'embed/video/(.*?)[\"\?]').findall(
        video_html)[0]
    if params.next == 'play_r':
        return resolver.get_stream_dailymotion(video_id, False)
    elif params.next == 'download_video':
        return resolver.get_stream_dailymotion(video_id, True)
