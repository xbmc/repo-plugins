# -*- coding: utf-8 -*-
"""
    Catch-up TV & More
    Copyright (C) 2017 SylvainCecchetto

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
import json
from resources.lib import utils
from resources.lib import resolver
from resources.lib import common

# URL :
URL_ROOT_SITE = 'https://www.mycanal.fr'
# Channel

# Replay channel :
URL_REPLAY = URL_ROOT_SITE + '/chaines/%s'
# Channel name

# Replay => VideoId
URL_INFO_CONTENT = 'https://secure-service.canal-plus.com/' \
                   'video/rest/getVideosLiees/cplus/%s?format=json'


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


# Dailymotion Id get from these pages below
# - http://www.dailymotion.com/cstar
# - http://www.dailymotion.com/canalplus
# - http://www.dailymotion.com/C8TV
LIVE_DAILYMOTION_ID = {
    'c8': 'x5gv5rr',
    'cstar': 'x5gv5v0',
    'canalplus': 'x5gv6be'
}


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def list_shows(params):
    """Create categories list"""
    shows = []

    if params.next == 'list_shows_1':
        value_next = ''

        replay_html = utils.get_webcontent(
            URL_REPLAY % (params.channel_name)
        )
        json_replay = re.compile(
            'window.__data=(.*?)};').findall(replay_html)[0]
        replay_jsonparse = json.loads(json_replay + ('}'))

        for category in replay_jsonparse["landing"]["strates"]:
            if category["type"] == "contentRow" or \
                    category["type"] == "contentGrid":
                if 'title' in category:
                    title = category['title'].encode('utf-8')
                else:
                    title = replay_jsonparse["page"]["displayName"].encode('utf-8')

                if category["contents"][0]["type"] == 'quicktime':
                    value_next = 'list_videos_1'
                elif category["contents"][0]["type"] == 'landing':
                    value_next = 'list_shows_2'
                elif category["contents"][0]["type"] == 'pfv':
                    value_next = 'list_videos_1'

                shows.append({
                    'label': title,
                    'url': common.PLUGIN.get_url(
                        module_path=params.module_path,
                        module_name=params.module_name,
                        action='replay_entry',
                        next=value_next,
                        url_next=URL_REPLAY % (params.channel_name),
                        title=title,
                        window_title=title
                    )
                })

    elif params.next == 'list_shows_2':

        replay_html = utils.get_webcontent(
            URL_REPLAY % (params.channel_name)
        )
        json_replay = re.compile(
            'window.__data=(.*?)};').findall(replay_html)[0]
        replay_jsonparse = json.loads(json_replay + ('}'))

        for emissions in replay_jsonparse["landing"]["strates"]:
            if emissions["type"] == "contentRow" or \
                    emissions["type"] == "contentGrid":
                if params.title == replay_jsonparse["page"]["displayName"].encode('utf-8'):
                    if 'title' not in emissions:
                        for emission in emissions["contents"]:
                            title = emission["onClick"]["displayName"].encode('utf-8')
                            img = emission['URLImage'].encode('utf-8')
                            url_emission = URL_ROOT_SITE + \
                                emission["onClick"]["path"].encode('utf-8')

                            shows.append({
                                'label': title,
                                'thumb': img,
                                'url': common.PLUGIN.get_url(
                                    module_path=params.module_path,
                                    module_name=params.module_name,
                                    action='replay_entry',
                                    next='list_shows_3',
                                    url_next=url_emission,
                                    title=title,
                                    window_title=title
                                )
                            })
                else:
                    if 'title' in emissions:
                        if emissions['title'].encode('utf-8') == params.title:
                            for emission in emissions["contents"]:
                                title = emission["onClick"]["displayName"].encode('utf-8')
                                img = emission['URLImage'].encode('utf-8')
                                url_emission = URL_ROOT_SITE + \
                                    emission["onClick"]["path"].encode('utf-8')

                                shows.append({
                                    'label': title,
                                    'thumb': img,
                                    'url': common.PLUGIN.get_url(
                                        module_path=params.module_path,
                                        module_name=params.module_name,
                                        action='replay_entry',
                                        next='list_shows_3',
                                        url_next=url_emission,
                                        title=title,
                                        window_title=title
                                    )
                                })

    elif params.next == 'list_shows_3':

        replay_html = utils.get_webcontent(params.url_next)
        json_replay = re.compile(
            'window.__data=(.*?)};').findall(replay_html)[0]
        replay_jsonparse = json.loads(json_replay + ('}'))

        for category in replay_jsonparse["landing"]["strates"]:
            if category["type"] == "contentRow" or \
                    category["type"] == "contentGrid":
                if 'title' in category:
                    title = category['title'].encode('utf-8')
                else:
                    title = replay_jsonparse["page"]["displayName"].encode('utf-8')
                shows.append({
                    'label': title,
                    'url': common.PLUGIN.get_url(
                        module_path=params.module_path,
                        module_name=params.module_name,
                        action='replay_entry',
                        next='list_videos_1',
                        title=title,
                        url_next=params.url_next,
                        window_title=title
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

        replay_html = utils.get_webcontent(params.url_next)
        json_replay = re.compile(
            'window.__data=(.*?)};').findall(replay_html)[0]
        replay_jsonparse = json.loads(json_replay + ('}'))

        for emissions in replay_jsonparse["landing"]["strates"]:
            if emissions["type"] == "contentRow" or \
                    emissions["type"] == "contentGrid":

                if params.title == replay_jsonparse["page"]["displayName"].encode('utf-8'):
                    if 'title' not in emissions:
                        for emission in emissions["contents"]:
                            title = emission["title"].encode('utf-8')
                            plot = emission["subtitle"].encode('utf-8')
                            img = emission['URLImage'].encode('utf-8')
                            video_id = emission["contentID"]
                            duration = 0

                            info = {
                                'video': {
                                    'title': title,
                                    'plot': plot,
                                    # 'aired': aired,
                                    # 'date': date,
                                    'duration': duration,
                                    # 'year': year,
                                    # 'genre': category,
                                    'mediatype': 'tvshow'
                                }
                            }

                            download_video = (
                                common.GETTEXT('Download'),
                                'XBMC.RunPlugin(' + common.PLUGIN.get_url(
                                    action='download_video',
                                    module_path=params.module_path,
                                    module_name=params.module_name,
                                    video_id=video_id) + ')'
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
                                    video_id=video_id,
                                ),
                                'is_playable': True,
                                'info': info,
                                'context_menu': context_menu
                            })
                    elif 'title' in emissions:
                        if emissions['title'].encode('utf-8') == params.title:
                            for emission in emissions["contents"]:
                                title = emission["title"].encode('utf-8')
                                plot = emission["subtitle"].encode('utf-8')
                                img = emission['URLImage'].encode('utf-8')
                                video_id = emission["contentID"]
                                duration = 0

                                info = {
                                    'video': {
                                        'title': title,
                                        'plot': plot,
                                        # 'aired': aired,
                                        # 'date': date,
                                        'duration': duration,
                                        # 'year': year,
                                        # 'genre': category,
                                        'mediatype': 'tvshow'
                                    }
                                }

                                download_video = (
                                    common.GETTEXT('Download'),
                                    'XBMC.RunPlugin(' + common.PLUGIN.get_url(
                                        action='download_video',
                                        module_path=params.module_path,
                                        module_name=params.module_name,
                                        video_id=video_id) + ')'
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
                                        video_id=video_id,
                                    ),
                                    'is_playable': True,
                                    'info': info,
                                    'context_menu': context_menu
                                })
                else:
                    if 'title' in emissions:
                        if emissions['title'].encode('utf-8') == params.title:
                            for emission in emissions["contents"]:
                                title = emission["title"].encode('utf-8')
                                plot = emission["subtitle"].encode('utf-8')
                                img = emission['URLImage'].encode('utf-8')
                                video_id = emission["contentID"]
                                duration = 0

                                info = {
                                    'video': {
                                        'title': title,
                                        'plot': plot,
                                        # 'aired': aired,
                                        # 'date': date,
                                        'duration': duration,
                                        # 'year': year,
                                        # 'genre': category,
                                        'mediatype': 'tvshow'
                                    }
                                }

                                download_video = (
                                    common.GETTEXT('Download'),
                                    'XBMC.RunPlugin(' + common.PLUGIN.get_url(
                                        action='download_video',
                                        module_path=params.module_path,
                                        module_name=params.module_name,
                                        video_id=video_id) + ')'
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
                                        video_id=video_id,
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


#@common.PLUGIN.mem_cached(common.CACHE_TIME)
def start_live_tv_stream(params):
    params['next'] = 'play_l'
    params['live_dailymotion_id'] = LIVE_DAILYMOTION_ID[params.channel_name]
    return get_video_url(params)


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def get_video_url(params):
    """Get video URL and start video player"""
    if params.next == 'play_r' or params.next == 'download_video':
        file_video = utils.get_webcontent(
            URL_INFO_CONTENT % (params.video_id)
        )
        media_json = json.loads(file_video)
        stream_url = ''
        if 'ID' in media_json:
            if media_json['ID'] == params.video_id:
                stream_url = media_json['MEDIA']['VIDEOS']['HLS'].encode('utf-8')
        else:
            for media in media_json:
                if media['ID'] == params.video_id:
                    stream_url = media['MEDIA']['VIDEOS']['HLS'].encode('utf-8')
        return stream_url
    elif params.next == 'play_l':
        return resolver.get_stream_dailymotion(
            params.live_dailymotion_id, False)