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

import datetime
import json
import re
from resources.lib import utils
from resources.lib import common


URL_ROOT = 'https://%s.%s.ch'
# (www or play), channel_name

# Replay
URL_CATEGORIES_JSON = 'https://%s.%s.ch/play/v2/tv/topicList?layout=json'
# (www or play), channel_name

URL_EMISSIONS = 'https://www.%s.ch/play/tv/%s?index=all'
# channel_name, name_emission

URL_LIST_EPISODES = 'https://www.%s.ch/play/v2/tv/show/%s/' \
                    'latestEpisodes?numberOfEpisodes=50' \
                    '&tillMonth=%s&layout=json'
# channel_name, IdEmission, ThisMonth (11-2017)

# Live
URL_LIVE_JSON = 'http://www.%s.ch/play/v2/tv/live/overview?layout=json'
# channel_name

URL_TOKEN = 'https://tp.srgssr.ch/akahd/token?acl=%s'
# acl

URL_INFO_VIDEO = 'https://il.srgssr.ch/integrationlayer' \
                 '/2.0/%s/mediaComposition/video/%s.json' \
                 '?onlyChapters=true&vector=portalplay'
# channel_name, video_id


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


EMISSION_NAME = {
    'rts': 'emissions',
    'rsi': 'programmi',
    'rtr': 'emissiuns',
    'srf': 'sendungen'
}


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def list_shows(params):
    """Build categories listing"""
    shows = []

    if params.next == 'list_shows_1':

        if params.channel_name != 'swissinfo':

            show_title = EMISSION_NAME[params.channel_name]
            show_url = URL_EMISSIONS % (params.channel_name,
                EMISSION_NAME[params.channel_name])

            shows.append({
                'label': show_title,
                'url': common.PLUGIN.get_url(
                    module_path=params.module_path,
                    module_name=params.module_name,
                    action='replay_entry',
                    next='list_shows_2',
                    title=show_title,
                    show_url=show_url,
                    window_title=show_title
                )
            })

        if params.channel_name == 'swissinfo':
            first_part_fqdn = 'play'
        else:
            first_part_fqdn = 'www'

        file_path = utils.get_webcontent(
            URL_CATEGORIES_JSON % (
                first_part_fqdn,
                params.channel_name)
        )
        replay_categories_json = json.loads(file_path)

        for category in replay_categories_json:

            show_title = category["title"].encode('utf-8')
            show_url = URL_ROOT % (first_part_fqdn,
                params.channel_name) + \
                category["latestModuleUrl"].encode('utf-8')

            shows.append({
                'label': show_title,
                'url': common.PLUGIN.get_url(
                    module_path=params.module_path,
                    module_name=params.module_name,
                    action='replay_entry',
                    next='list_videos_1',
                    title=show_title,
                    show_url=show_url,
                    window_title=show_title
                )
            })

    elif params.next == 'list_shows_2':

        file_path = utils.get_webcontent(params.show_url)
        datas_shows = re.compile(
            r'data-alphabetical-sections=\\\"(.*?)\\\"').findall(
            file_path)[0]
        datas_shows = datas_shows.replace('&quot;', '"')
        datas_shows = datas_shows.replace('\\\\"', ' ')
        datas_shows_json = json.loads(datas_shows)

        for letter_show in datas_shows_json:
            for show in letter_show["showTeaserList"]:
                if 'id' in show:
                    show_title = show["title"].encode('utf-8')
                    if 'rts.ch' in show["imageUrl"]:
                        show_image = show["imageUrl"] + \
                            '/scale/width/448'.encode('utf-8')
                    else:
                        show_image = show["imageUrl"].encode('utf-8')
                    show_id = show["id"]

                    shows.append({
                        'label': show_title,
                        'thumb': show_image,
                        'url': common.PLUGIN.get_url(
                        module_path=params.module_path,
                        module_name=params.module_name,
                            action='replay_entry',
                            next='list_videos_2',
                            title=show_title,
                            show_id=show_id,
                            window_title=show_title
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
        file_path = utils.get_webcontent(params.show_url)
        datas_videos = re.compile(
            r'data-teaser=\"(.*?)\"').findall(file_path)[0]
        datas_videos = datas_videos.replace('&quot;', '"')
        datas_videos_json = json.loads(datas_videos)

        for episode in datas_videos_json:

            video_title = ''
            if 'showTitle' in episode:
                video_title = episode["showTitle"].encode('utf-8') + \
                    ' - ' + episode["title"].encode('utf-8')
            else:
                video_title = episode["title"].encode('utf-8')
            video_duration = 0
            video_plot = ''
            if 'description' in episode:
                video_plot = episode["description"].encode('utf-8')
            video_img = episode["imageUrl"].encode('utf-8') + \
                '/scale/width/448'
            video_url = episode["absoluteDetailUrl"].encode('utf-8')

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
                'fanart': video_img,
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

    elif params.next == 'list_videos_2':

        date = datetime.datetime.now()

        actual_month = str(date).split(' ')[0].split('-')[1] + '-' + \
            str(date).split(' ')[0].split('-')[0]

        file_path = utils.get_webcontent(
            URL_LIST_EPISODES % (
                params.channel_name,
                params.show_id,
                actual_month))

        list_episodes = json.loads(file_path)

        for episode in list_episodes["episodes"]:

            video_title = ''
            if 'showTitle' in episode:
                video_title = episode["showTitle"].encode('utf-8') + \
                    ' - ' + episode["title"].encode('utf-8')
            else:
                video_title = episode["title"].encode('utf-8')
            video_duration = 0
            video_plot = ''
            if 'description' in episode:
                video_plot = episode["description"].encode('utf-8')
            video_img = episode["imageUrl"].encode('utf-8') + \
                '/scale/width/448'
            video_url = episode["absoluteDetailUrl"].encode('utf-8')

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
                'fanart': video_img,
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
            common.sp.xbmcplugin.SORT_METHOD_UNSORTED,
            common.sp.xbmcplugin.SORT_METHOD_DURATION,
            common.sp.xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE,
            common.sp.xbmcplugin.SORT_METHOD_GENRE,
            common.sp.xbmcplugin.SORT_METHOD_UNSORTED
        ),
        content='tvshows',
        update_listing='update_listing' in params,
        category=common.get_window_title()
    )


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def get_live_item(params):
    items = []

    title = ''
    # subtitle = ' - '
    plot = ''
    duration = 0
    img = ''

    lives_datas = utils.get_webcontent(
        URL_LIVE_JSON % params.channel_name)
    lives_json = json.loads(lives_datas)

    for live in lives_json["teaser"]:

        title = live["channelName"]
        img = live["logo"] + '/scale/width/448'
        live_id = live["id"]

        info = {
            'video': {
                'title': title,
                'plot': plot,
                'duration': duration
            }
        }

        items.append({
            'label': title,
            'thumb': img,
            'url': common.PLUGIN.get_url(
                action='start_live_tv_stream',
                next='play_l',
                module_name=params.module_name,
                module_path=params.module_path,
                live_id=live_id,
            ),
            'is_playable': True,
            'info': info
        })

    return items


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def get_video_url(params):
    """Get video URL and start video player"""
    if params.next == 'play_r' or params.next == 'download_video':
        video_id = params.video_url.split('=')[1]
        if params.channel_name == 'swissinfo':
            channel_name_value = 'swi'
        else:
            channel_name_value = params.channel_name
        streams_datas = utils.get_webcontent(
            URL_INFO_VIDEO % (channel_name_value, video_id))
        streams_json = json.loads(streams_datas)

        # build url
        url = ''
        for stream in streams_json["chapterList"]:
            if video_id in stream["id"]:
                for url_stream in stream["resourceList"]:
                    if url_stream["quality"] == 'HD' and \
                       'mpegURL' in url_stream["mimeType"]:
                        url = url_stream["url"]
        acl_value = '/i/%s/*' % (re.compile(
            '\/i\/(.*?)\/').findall(url)[0])
        token_datas = utils.get_webcontent(URL_TOKEN % acl_value)
        token_json = json.loads(token_datas)
        token = token_json["token"]["authparams"]

        return url + '?' + token
    elif params.next == 'play_l':

        streams_datas = utils.get_webcontent(
            URL_INFO_VIDEO % (
                params.channel_name,
                params.live_id))
        streams_json = json.loads(streams_datas)

        # build url
        url = ''
        for stream in streams_json["chapterList"]:
            if params.live_id in stream["id"]:
                for url_stream in stream["resourceList"]:
                    if 'HD' in url_stream["quality"]:
                        if url_stream["quality"] == 'HD' and \
                           'mpegURL' in url_stream["mimeType"]:
                            url = url_stream["url"]
                    else:
                        if 'mpegURL' in url_stream["mimeType"]:
                            url = url_stream["url"]
        acl_value = '/i/%s/*' % (re.compile(
            '\/i\/(.*?)\/').findall(url)[0])
        token_datas = utils.get_webcontent(URL_TOKEN % acl_value)
        token_json = json.loads(token_datas)
        token = token_json["token"]["authparams"]

        m3u8_file = utils.get_webcontent(url + '?' + token)
        lines = m3u8_file.splitlines()
        for k in range(0, len(lines) - 1):
            for k in range(0, len(lines) - 1):
                if 'RESOLUTION=' in lines[k]:
                    url = lines[k + 1]
        return url
