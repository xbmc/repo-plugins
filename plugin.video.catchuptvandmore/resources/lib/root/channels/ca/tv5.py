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
import json
import re
from bs4 import BeautifulSoup as bs
from resources.lib import utils
from resources.lib import common

URL_ROOT = 'https://%s.ca'
# Channel Name

URL_VIDEOS = 'https://%s.ca/videos?params[%s]=%s'\
             '&options[sort]=publish_start&options[page]=%s'
# Channel Name, theme|serie, Value, page

URL_STREAM = 'https://production-ps.lvp.llnw.net/r/PlaylistService' \
             '/media/%s/getMobilePlaylistByMediaId'
# StreamId


def channel_entry(params):
    """Entry function of the module"""
    if 'replay_entry' == params.next:
        params.next = "list_shows_1"
        return list_shows(params)
    elif 'list_shows' in params.next:
        return list_shows(params)
    elif 'list_videos' in params.next:
        return list_videos(params)
    elif 'live' in params.next:
        return list_live(params)
    elif 'play' in params.next:
        return get_video_url(params)
    else:
        return None


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def list_shows(params):
    """Build categories listing"""
    shows = []

    if params.next == 'list_shows_1':

        category_name = 'Emissions'

        shows.append({
            'label': category_name,
            'url': common.PLUGIN.get_url(
                module_path=params.module_path,
                module_name=params.module_name,
                action='replay_entry',
                category_name=category_name,
                next='list_shows_2',
                window_title=category_name
            )
        })

        # Get categories :
        root_html = utils.get_webcontent(
            URL_ROOT % params.channel_name + '/videos')
        root_soup = bs(root_html, 'html.parser')
        menu_soup = root_soup.find(
            'select', class_="js-form-data js-select_filter_video js-select_filter_video-theme")
        categories_soup = menu_soup.find_all('option')

        for category in categories_soup:

            category_name = category.get_text().encode('utf-8')
            value_id = category.get('value')

            if 'theme_' in value_id:
                shows.append({
                    'label': category_name,
                    'url': common.PLUGIN.get_url(
                        module_path=params.module_path,
                        module_name=params.module_name,
                        action='replay_entry',
                        value_id=value_id,
                        page='1',
                        category_name=category_name,
                        next='list_videos_theme',
                        window_title=category_name
                    )
                })

    elif params.next == 'list_shows_2':

        # Get series :
        root_html = utils.get_webcontent(
            URL_ROOT % params.channel_name + '/videos')
        root_soup = bs(root_html, 'html.parser')
        menu_soup = root_soup.find(
            'select', class_="js-form-data js-select_filter_video js-select_filter_video-serie")
        series_soup = menu_soup.find_all('option')

        for serie in series_soup:

            serie_name = serie.get_text().encode('utf-8')
            value_id = serie.get('value')

            if value_id != '':
                shows.append({
                    'label': serie_name,
                    'url': common.PLUGIN.get_url(
                        module_path=params.module_path,
                        module_name=params.module_name,
                        action='replay_entry',
                        value_id=value_id,
                        page='1',
                        serie_name=serie_name,
                        next='list_videos_series_id',
                        window_title=serie_name
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

    category_video = ''
    if params.next == 'list_videos_theme':
        category_video = 'theme'
    elif params.next == 'list_videos_series_id':
        category_video = 'serie'

    url_videos = URL_VIDEOS % (
        params.channel_name,
        category_video,
        params.value_id,
        params.page)

    root_html = utils.get_webcontent(url_videos)
    part_page = re.split(
        '<div class="listing-carousel-container">', root_html)
    part_page = re.split(
        '<div class="pagination-block js-pagination-block">', part_page[1])
    root_soup = bs(part_page[0], 'html.parser')
    episodes = root_soup.find_all(
        'div', class_='media-thumb ')

    for episode in episodes:

        video_title = episode.find('img').get('alt')
        if episode.find('a'):
            video_url = (URL_ROOT % params.channel_name) + \
                episode.find('a').get('href')
        else:
            video_url = 'NO_URL'
        video_img = episode.find('img').get('data-src')
        video_duration = 0
        video_plot = ''

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
                action='replay_entry',
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
            action='replay_entry',
            next=params.next,
            page=str(int(params.page) + 1),
            value_id=params.value_id,
            update_listing=True,
            previous_listing=str(videos)
        )
    })

    return common.PLUGIN.create_listing(
        videos,
        sort_methods=(
            common.sp.xbmcplugin.SORT_METHOD_UNSORTED,
            common.sp.xbmcplugin.SORT_METHOD_PLAYCOUNT,
            common.sp.xbmcplugin.SORT_METHOD_DATE,
            common.sp.xbmcplugin.SORT_METHOD_DURATION,
            common.sp.xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE
        ),
        content='tvshows',
        update_listing='update_listing' in params,
        category=common.get_window_title()
    )


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def list_live(params):
    return None


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def get_video_url(params):
    """Get video URL and start video player"""
    if params.next == 'play_r' or params.next == 'download_video':
        if 'http' in params.video_url:
            video_html = utils.get_webcontent(
                params.video_url)
            stream_id = re.compile(
                '\'media_id\' : "(.*?)"').findall(video_html)[0]
            streams_jsonparser = json.loads(
                utils.get_webcontent(URL_STREAM % stream_id))

            url = ''
            if 'mediaList' in streams_jsonparser:
                # Case Jarvis
                if common.sp.xbmc.__version__ == '2.24.0':
                    for stream in streams_jsonparser["mediaList"][0]["mobileUrls"]:
                        if 'MobileH264' in stream["targetMediaPlatform"]:
                            url = stream["mobileUrl"]
                # Case Krypton and ...
                else:
                    for stream in streams_jsonparser["mediaList"][0]["mobileUrls"]:
                        if 'HttpLiveStreaming' in stream["targetMediaPlatform"]:
                            url = stream["mobileUrl"]
                return url
            else:
                return ''
        else:
            return ''
