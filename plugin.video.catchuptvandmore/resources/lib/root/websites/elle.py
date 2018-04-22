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


URL_ROOT_VIDEOS = 'http://videos.elle.fr'

URL_ROOT_ELLE_GIRL_TV = 'http://www.elle.fr/'

URL_JSON_ELLE_GIRL_TV = URL_ROOT_ELLE_GIRL_TV + 'ajax/last_articles/' \
                                                'Elle-Girl?page=%s'


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


CATEGORIES = {
    'Mode': URL_ROOT_VIDEOS + '/les_videos/archive/Mode/%s',
    'Beaute': URL_ROOT_VIDEOS + '/les_videos/archive/Beaute/%s',
    'Minceur': URL_ROOT_VIDEOS + '/les_videos/archive/Minceur/%s',
    'People': URL_ROOT_VIDEOS + '/les_videos/archive/People/%s',
    'Cuisine': URL_ROOT_VIDEOS + '/les_videos/archive/Cuisine/%s',
    'Deco': URL_ROOT_VIDEOS + '/les_videos/archive/Deco/%s',
    'Musique': URL_ROOT_VIDEOS + '/les_videos/archive/Musique/%s',
    'Cinema': URL_ROOT_VIDEOS + '/les_videos/archive/Cinema/%s',
    'Societe': URL_ROOT_VIDEOS + '/les_videos/archive/Societe/%s',
    'Love & Sexe': URL_ROOT_VIDEOS + '/les_videos/archive/Love&Sexe/%s'
}


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def root(params):
    """Add modes in the listing"""
    modes = []

    category_name = 'ELLE Girl TV'

    modes.append({
        'label': category_name,
        'url': common.PLUGIN.get_url(
            module_path=params.module_path,
            module_name=params.module_name,
            action='website_entry',
            category_name=category_name,
            page='0',
            next='list_videos_2',
            window_title=category_name
        )
    })

    for category_name, category_url in CATEGORIES.iteritems():
        modes.append({
            'label': category_name,
            'url': common.PLUGIN.get_url(
                module_path=params.module_path,
                module_name=params.module_name,
                action='website_entry',
                category_url=category_url,
                category_name=category_name,
                page='1',
                next='list_videos_1',
                window_title=category_name
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

        replay_episodes_html = utils.get_webcontent(
            params.category_url % params.page)
        replay_episodes_soup = bs(replay_episodes_html, 'html.parser')
        episodes = replay_episodes_soup.find(
            'div', class_='video-list').find_all(
                'div', class_='video')

        for episode in episodes:
            video_title = episode.find(
                'a', class_='title').get_text().strip()
            video_url = episode.find('a').get('href')
            video_img = episode.find(
                'img').get('src')
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
                category_url=params.category_url,
                page=str(int(params.page) + 1),
                update_listing=True,
                previous_listing=str(videos)
            )
        })

    elif params.next == 'list_videos_2':

        replay_episodes_html = utils.get_webcontent(
            URL_JSON_ELLE_GIRL_TV % params.page)
        episodes_jsonparser = json.loads(replay_episodes_html)

        for episode in episodes_jsonparser:
            video_title = episode["titre"]
            video_url = URL_ROOT_ELLE_GIRL_TV + \
                episode["url"].encode('utf-8')
            video_img = URL_ROOT_ELLE_GIRL_TV + \
                episode["imagePaysage"].encode('utf-8')
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
                    next='play_r_elle_girl_tv',
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
                next='list_videos_2',
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

    if params.next == 'play_r':
        # Get DailyMotion Id Video
        video_urls = re.compile(
            'file: \"(.*?)\"').findall(video_html)
        stream_url = ''
        for video_url in video_urls:
            if 'm3u8' in video_url:
                stream_url = video_url
        return stream_url
    elif params.next == 'play_r_elle_girl_tv':
        # Get DailyMotion Id Video
        video_id = re.compile(
            r'embed/video/(.*?)[\"\?\']').findall(
                video_html)[0]
        return resolver.get_stream_dailymotion(video_id, False)
    elif params.next == 'download_video':
        if 'dailymotion.com/embed' in video_html:
            video_id = re.compile(
                r'embed/video/(.*?)[\"\?\']').findall(
                    video_html)[0]
            return resolver.get_stream_dailymotion(video_id, True)
        else:
            video_urls = re.compile(
                'file: \"(.*?)\"').findall(video_html)
            stream_url = ''
            for video_url in video_urls:
                if 'm3u8' in video_url:
                    stream_url = video_url
            return stream_url
