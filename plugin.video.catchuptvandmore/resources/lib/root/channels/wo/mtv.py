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
from resources.lib import utils
from resources.lib import common


URL_ROOT = 'http://www.mtv.fr'
# Contents

URL_JSON_MTV = URL_ROOT + '/feeds/triforce/manifest/v8?url=%s'
# URL

URL_EMISSION = URL_ROOT + '/emissions/'

URL_VIDEOS = URL_ROOT + '/dernieres-videos'

URL_STREAM = 'https://media-utils.mtvnservices.com/services/' \
             'MediaGenerator/mgid:arc:video:mtv.fr:%s?' \
             '&format=json&acceptMethods=hls'
# videoID


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

        emission_name = common.GETTEXT('All videos')

        file_path = utils.get_webcontent(
            URL_JSON_MTV % URL_VIDEOS)
        json_mtv = json.loads(file_path)
        emission_url = json_mtv["manifest"]["zones"]["t4_lc_promo1"]["feed"]

        shows.append({
            'label': emission_name,
            'url': common.PLUGIN.get_url(
                module_path=params.module_path,
                module_name=params.module_name,
                action='replay_entry',
                emission_url=emission_url,
                category_name=emission_name,
                next='list_videos_1',
                window_title=emission_name
            )
        })

        # Get Emission :
        root_json = utils.get_webcontent(
            URL_JSON_MTV % URL_EMISSION)
        json_emission_mtv = json.loads(root_json)
        emission_json_url = json_emission_mtv["manifest"]["zones"]["t5_lc_promo1"]["feed"]
        emission_json = utils.get_webcontent(emission_json_url)
        emission_json_parser = json.loads(emission_json)

        for emissions in emission_json_parser["result"]["shows"]:
            emissions_letter = emissions["key"]
            shows.append({
                'label': emissions_letter,
                'url': common.PLUGIN.get_url(
                    module_path=params.module_path,
                    module_name=params.module_name,
                    action='replay_entry',
                    emissions_letter=emissions_letter,
                    category_name=emissions_letter,
                    next='list_shows_2',
                    window_title=emissions_letter
                )
           })

    elif params.next == 'list_shows_2':

        root_json = utils.get_webcontent(
            URL_JSON_MTV % URL_EMISSION)
        json_emission_mtv = json.loads(root_json)
        emission_json_url = json_emission_mtv["manifest"]["zones"]["t5_lc_promo1"]["feed"]
        emission_json = utils.get_webcontent(emission_json_url)
        emission_json_parser = json.loads(emission_json)

        for emissions in emission_json_parser["result"]["shows"]:
            if params.emissions_letter == emissions["key"]:
                for emission in emissions["value"]:
                    emission_name = emission["title"]
                    file_path_2 = utils.get_webcontent(
                        URL_JSON_MTV % emission["url"])
                    json_mtv = json.loads(file_path_2)
                    emission_url = json_mtv["manifest"]["zones"]["t5_lc_promo1"]["feed"]

                    shows.append({
                        'label': emission_name,
                        'url': common.PLUGIN.get_url(
                            module_path=params.module_path,
                            module_name=params.module_name,
                            action='replay_entry',
                            emission_url=emission_url,
                            category_name=emission_name,
                            next='list_videos_1',
                            window_title=emission_name
                        )
                    })

    return common.PLUGIN.create_listing(
        shows,
        sort_methods=(
            common.sp.xbmcplugin.SORT_METHOD_UNSORTED
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

        file_path = utils.get_webcontent(
            params.emission_url)
        json_mtv = json.loads(file_path)

        if 'data' in json_mtv["result"]:
            for episode in json_mtv["result"]["data"]["items"]:

                video_title = episode["title"]
                video_plot = episode["description"]
                video_duration = 0
                video_url = episode["canonicalURL"]
                if 'images' in episode:
                    video_img = episode["images"]["url"]
                else:
                    video_img = ''

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

        # More videos...
        if 'nextPageURL' in json_mtv["result"]:
            videos.append({
                'label': '# ' + common.ADDON.get_localized_string(30700),
                'url': common.PLUGIN.get_url(
                    module_path=params.module_path,
                    module_name=params.module_name,
                    action='replay_entry',
                    next='list_videos_1',
                    update_listing=True,
                    emission_url=json_mtv["result"]["nextPageURL"],
                    previous_listing=str(videos)
                )
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
def list_live(params):
    return None


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def get_video_url(params):
    """Get video URL and start video player"""
    if params.next == 'play_r' or params.next == 'download_video':
        video_html = utils.get_webcontent(
            params.video_url)
        video_id = re.compile(
            r'itemId":"(.*?)"').findall(video_html)[0]
        json_video_stream = utils.get_webcontent(
            URL_STREAM % video_id)
        json_video_stream_parser = json.loads(json_video_stream)
        return json_video_stream_parser["package"]["video"]["item"][0]["rendition"][0]["src"]
