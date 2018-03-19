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
import re
from bs4 import BeautifulSoup as bs
from resources.lib import utils
from resources.lib import resolver
from resources.lib import common


URL_ROOT = 'http://www.30millionsdamis.fr'


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

    categories_html = utils.get_webcontent(
        URL_ROOT + '/actualites/videos')
    categories_soup = bs(categories_html, 'html.parser')
    categories = categories_soup.find(
            'select', class_='selecttourl').find_all(
            'option')

    for category in categories:
        category_title = category.get_text().strip().encode('utf-8')
        category_url = category.get('value')

        modes.append({
            'label': category_title,
            'url': common.PLUGIN.get_url(
                module_path=params.module_path,
                module_name=params.module_name,
                action='website_entry',
                next='list_videos_1',
                title=category_title,
                category_url=category_url,
                page='0',
                window_title=category_title
            )
        })

    return common.PLUGIN.create_listing(
        modes,
        sort_methods=(
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

        if int(params.page) > 0:
            replay_episodes_html = utils.get_webcontent(
                params.category_url + 'actu-page/%s/' % params.page)
        else:
            replay_episodes_html = utils.get_webcontent(
                params.category_url)
        replay_episodes_soup = bs(replay_episodes_html, 'html.parser')

        episodes = replay_episodes_soup.find_all(
            'div', class_='news-latest')

        for episode in episodes:

            video_title = episode.find(
                'a').get('title')
            video_url = URL_ROOT + episode.find('a').get('href')
            video_img = URL_ROOT + episode.find('img').get('src')
            video_duration = 0
            video_plot = episode.find(
                'p').get_text().strip().encode('utf-8')

            info = {
                'video': {
                    'title': video_title,
                    # 'aired': aired,
                    # 'date': date,
                    'duration': video_duration,
                    'plot': video_plot,
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
                category_url=params.category_url,
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
    video_id = re.compile(
        r'www.youtube.com/embed/(.*?)[\?\"]').findall(video_html)[0]

    if params.next == 'download_video':
        return resolver.get_stream_youtube(video_id, True)
    else:
        return resolver.get_stream_youtube(video_id, False)
