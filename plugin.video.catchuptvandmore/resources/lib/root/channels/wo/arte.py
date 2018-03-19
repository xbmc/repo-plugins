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

import json
import re
from resources.lib import utils
from resources.lib import common


URL_ROOT = 'https://www.arte.tv/%s/'
# Language

URL_REPLAY_ARTE = 'https://api.arte.tv/api/player/v1/config/%s/%s'
# desired_language, videoid

URL_LIVE_ARTE = 'https://api.arte.tv/api/player/v1/livestream/%s'
# Langue, ...

DESIRED_LANGUAGE = common.PLUGIN.get_setting(
    'arte.language')


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
        file_path = utils.download_catalog(
            URL_ROOT % DESIRED_LANGUAGE.lower(),
            '%s_%s.json' % (params.channel_name, DESIRED_LANGUAGE)
        )
        file_replay = open(file_path).read()
        file_replay = re.compile(
            r'_INITIAL_STATE__ = (.*?);').findall(file_replay)[0]
        json_parser = json.loads(file_replay)

        value_code = json_parser['pages']['currentCode']

        for category in json_parser['pages']['list'][value_code]['zones']:

            if category['type'] == 'category':
                category_name = category['title']
                category_url = category['link']['url']

                shows.append({
                    'label': category_name,
                    'url': common.PLUGIN.get_url(
                        module_path=params.module_path,
                        module_name=params.module_name,
                        action='replay_entry',
                        next='list_shows_2',
                        category_name=category_name,
                        category_url=category_url,
                        window_title=category_name
                    )
                })
    elif params.next == 'list_shows_2':
        file_path = utils.download_catalog(
            params.category_url,
            '%s_%s_%s.json' % (
                params.channel_name, DESIRED_LANGUAGE, params.category_name)
        )
        file_replay = open(file_path).read()
        file_replay = re.compile(
            r'_INITIAL_STATE__ = (.*?);').findall(file_replay)[0]
        json_parser = json.loads(file_replay)

        value_code = json_parser['pages']['currentCode']

        for category in json_parser['pages']['list'][value_code]['zones']:

            if category['type'] == 'category':
                sub_category_name = category['title']
                sub_category_url = category['link']['url']

                shows.append({
                    'label': sub_category_name,
                    'url': common.PLUGIN.get_url(
                        module_path=params.module_path,
                        module_name=params.module_name,
                        action='replay_entry',
                        next='list_videos_1',
                        sub_category_name=sub_category_name,
                        sub_category_url=sub_category_url,
                        window_title=sub_category_name
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
        file_path = utils.download_catalog(
            params.sub_category_url,
            '%s_%s_%s.json' % (
                params.channel_name, DESIRED_LANGUAGE, params.sub_category_name)
        )
        file_replay = open(file_path).read()
        file_replay = re.compile(
            r'_INITIAL_STATE__ = (.*?);').findall(file_replay)[0]
        json_parser = json.loads(file_replay)

        value_code = json_parser['pages']['currentCode']

        for videos_list in json_parser['pages']['list'][value_code]['zones']:
            if videos_list['type'] == 'listing':
                for video in videos_list['data']:
                    title = video['title']
                    video_id = video['programId']
                    img = ''
                    for images in video['images']['landscape']['resolutions']:
                        img = images['url']

                    # aired = emission['aired'].split(' ')[0]
                    # aired_splited = aired.split('/')
                    # day = aired_splited[0]
                    # mounth = aired_splited[1]
                    # year = aired_splited[2]
                    # date : string (%d.%m.%Y / 01.01.2009)
                    # aired : string (2008-12-07)
                    # date = '.'.join((day, mounth, year))
                    # aired = '-'.join((year, mounth, day))
                    info = {
                        'video': {
                            'title': title,
                            'plot': video['description'],
                            # 'aired': aired,
                            # 'date': date,
                            # 'duration': vid['duration'],
                            # 'year': emission['production_year'],
                            # 'genre': emission['genre'],
                            # 'playcount': emission['playcount'],
                            # 'director': emission['director'],
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
                common.sp.xbmcplugin.SORT_METHOD_DATE,
                common.sp.xbmcplugin.SORT_METHOD_DURATION,
                common.sp.xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE,
                common.sp.xbmcplugin.SORT_METHOD_GENRE,
                common.sp.xbmcplugin.SORT_METHOD_PLAYCOUNT,
                common.sp.xbmcplugin.SORT_METHOD_UNSORTED
            ),
            content='tvshows',
            category=common.get_window_title()
        )


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def get_live_item(params):
    if DESIRED_LANGUAGE == 'FR' or \
            DESIRED_LANGUAGE == 'DE':

        url_live = ''

        file_path = utils.download_catalog(
            URL_LIVE_ARTE % DESIRED_LANGUAGE.lower(),
            '%s_%s_live.json' % (params.channel_name, DESIRED_LANGUAGE)
        )
        file_live = open(file_path).read()
        json_parser = json.loads(file_live)

        title = json_parser["videoJsonPlayer"]["VTI"].encode('utf-8')
        img = json_parser["videoJsonPlayer"]["VTU"]["IUR"].encode('utf-8')
        plot = ''
        if 'V7T' in json_parser["videoJsonPlayer"]:
            plot = json_parser["videoJsonPlayer"]["V7T"].encode('utf-8')
        elif 'VDE' in json_parser["videoJsonPlayer"]:
            plot = json_parser["videoJsonPlayer"]["VDE"].encode('utf-8')
        duration = 0
        duration = json_parser["videoJsonPlayer"]["videoDurationSeconds"]
        url_live = json_parser["videoJsonPlayer"]["VSR"]["HLS_SQ_1"]["url"]

        info = {
            'video': {
                'title': params.channel_label + " - [I]" + title + "[/I]",
                'plot': plot,
                'duration': duration
            }
        }

        return {
            'label': params.channel_label + " - [I]" + title + "[/I]",
            'fanart': img,
            'thumb': img,
            'url': common.PLUGIN.get_url(
                action='start_live_tv_stream',
                next='play_l',
                module_name=params.module_name,
                module_path=params.module_path,
                url=url_live,
            ),
            'is_playable': True,
            'info': info
        }
    else:
        return None


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def get_video_url(params):
    """Get video URL and start video player"""
    if params.next == 'play_r' or params.next == 'download_video':
        file_medias = utils.get_webcontent(
            URL_REPLAY_ARTE % (
                DESIRED_LANGUAGE.lower(), params.video_id))
        json_parser = json.loads(file_medias)

        url_selected = ''
        video_streams = json_parser['videoJsonPlayer']['VSR']

        desired_quality = common.PLUGIN.get_setting('quality')

        if desired_quality == "DIALOG":
            all_datas_videos_quality = []
            all_datas_videos_path = []

            for video in video_streams:
                if not video.find("HLS"):
                        datas = json_parser['videoJsonPlayer']['VSR'][video]
                        all_datas_videos_quality.append(
                            datas['mediaType'] + " (" +
                            datas['versionLibelle'] + ")")
                        all_datas_videos_path.append(datas['url'])

            seleted_item = common.sp.xbmcgui.Dialog().select(
                "Choose Stream", all_datas_videos_quality)

            url_selected = all_datas_videos_path[seleted_item].encode(
                'utf-8')

        elif desired_quality == "BEST":
            url_selected = video_streams['HTTPS_SQ_1']['url']
            url_selected = url_selected.encode('utf-8')
        else:
            url_selected = video_streams['HTTPS_HQ_1']['url'].encode('utf-8')

        return url_selected
    elif params.next == 'play_l':
        return params.url
