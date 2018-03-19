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
from resources.lib import resolver
from resources.lib import common

URL_ROOT = 'https://tver.jp'

URL_REPLAY_BY_TV = URL_ROOT + '/%s'
# channel

list_channels = {
    'ntv': URL_REPLAY_BY_TV % 'ntv',
    'ex': URL_REPLAY_BY_TV % 'ex',
    'tbs': URL_REPLAY_BY_TV % 'tbs',
    'tx': URL_REPLAY_BY_TV % 'tx',
    # 'cx': URL_REPLAY_BY_TV % 'cx', (protectd by DRM)
    'mbs': URL_REPLAY_BY_TV % 'mbs',
    'abc': URL_REPLAY_BY_TV % 'abc',
    'ytv': URL_REPLAY_BY_TV % 'ytv'
}


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


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def list_shows(params):
    """Build shows listing"""
    shows = []

    if params.next == 'list_shows_1':

        all_video = common.ADDON.get_localized_string(30701)
        url_channel_replay = list_channels[params.module_name]

        shows.append({
            'label': common.GETTEXT('All videos'),
            'url': common.PLUGIN.get_url(
                module_path=params.module_path,
                module_name=params.module_name,
                action='replay_entry',
                next='list_videos_1',
                url_channel_replay=url_channel_replay,
                all_video=all_video,
                window_title=all_video
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

        replays_html = utils.get_webcontent(params.url_channel_replay)
        replays_soup = bs(replays_html, 'html.parser')
        if params.module_name == 'cx':
            list_videos = replays_soup.find(
                'div', class_='listinner').find_all(
                    'li')
        else:
            list_videos = replays_soup.find_all(
                'li', class_='resumable')
        
        for video_data in list_videos:
            
            title = video_data.find('h3').get_text()
            plot = video_data.find('p', class_='summary').get_text()
            duration = 0
            img = re.compile(
                r'url\((.*?)\);').findall(video_data.find('div' , class_='picinner').get('style'))[0]
            video_url = URL_ROOT + video_data.find('a').get('href')

            info = {
                'video': {
                    'title': title,
                    'plot': plot,
                    #'episode': episode_number,
                    #'season': season_number,
                    #'rating': note,
                    #'aired': aired,
                    #'date': date,
                    'duration': duration,
                    #'year': year,
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
                'fanart': img,
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

    return common.PLUGIN.create_listing(
        videos,
        sort_methods=(
            common.sp.xbmcplugin.SORT_METHOD_UNSORTED
        ),
        content='tvshows',
        category=common.get_window_title()
    )


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def list_live(params):
    return None


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def get_video_url(params):
    """Get video URL and start video player"""
    if params.next == 'download_video':
        return params.video_url
    elif params.next == 'play_r':
        video_html = utils.get_webcontent(params.video_url)

        video_data = video_html.split(
            'addPlayer(')[1].split(
                ');')[0].replace(
                    "\n", "").replace("\r", "").split(',')
        
        data_account = video_data[0].strip().replace("'", "")
        data_player = video_data[1].strip().replace("'", "")
        if params.module_name == 'tx':
            data_video_id = video_data[4].strip().replace("'", "")
        else:
            data_video_id = 'ref:' + video_data[4].strip().replace("'", "")

        json_parser = resolver.get_brightcove_video_json(
            data_account,
            data_player,
            data_video_id)

        video_url = ''
        for url in json_parser["sources"]:
            if 'm3u8' in url["src"]:
                video_url = url["src"]
        return video_url

