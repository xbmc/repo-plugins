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
import json
import time
from resources.lib import utils
from resources.lib import common
from bs4 import BeautifulSoup as bs


URL_ROOT = 'https://www.bvn.tv'

# LIVE :
URL_LIVE_SITE = 'https://www.bvn.tv/bvnlive'
# Get Id
JSON_LIVE = 'https://json.dacast.com/b/%s/%s/%s'
# Id in 3 part
JSON_LIVE_TOKEN = 'https://services.dacast.com/token/i/b/%s/%s/%s'
# Id in 3 part

# REPLAY :
URL_TOKEN = 'https://ida.omroep.nl/app.php/auth'
URL_PROGRAMS = 'https://www.bvn.tv/programmas'
URL_INFO_REPLAY = 'https://e.omroep.nl/metadata/%s?callback=jsonpCallback%s5910'
# Id Video, time
URL_VIDEO_REPLAY = 'https://ida.omroep.nl/app.php/%s?adaptive=yes&token=%s'
# Id Video, Token


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
    else:
        return None


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def list_shows(params):
    """Build categories listing"""
    shows = []

    if params.next == 'list_shows_1':
        file_path = utils.download_catalog(
            URL_PROGRAMS,
            '%s_programs.html' % params.channel_name)
        programs_html = open(file_path).read()

        programs_soup = bs(programs_html, 'html.parser')
        list_js = programs_soup.find_all("script")
        # 7ème script contient la liste des categories au format json
        json_categories = list_js[6].prettify().replace(
            '</script>', ''
        ).replace(
            '<script>', ''
        ).replace(
            'var programList = ', ''
        ).replace(
            '\n', ''
        ).replace(
            '\r', ''
        ).replace(
            ',]', ']')
        json_categories_jsonparser = json.loads(json_categories)

        for category in json_categories_jsonparser["programmings"]:
            category_name = category["title"]
            category_img = URL_ROOT + category["image"]
            category_url = URL_ROOT + '/programma/' + category["description"]

            shows.append({
                'label': category_name,
                'thumb': category_img,
                'fanart': category_img,
                'url': common.PLUGIN.get_url(
                    module_path=params.module_path,
                    module_name=params.module_name,
                    action='replay_entry',
                    next='list_videos_cat',
                    category_url=category_url,
                    window_title=category_name,
                    category_name=category_name,
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

    file_path_2 = utils.download_catalog(
        params.category_url,
        '%s_%s_list_episodes.html' % (params.channel_name, params.category_url))
    episodes_html = open(file_path_2).read()

    episodes_soup = bs(episodes_html, 'html.parser')
    shows_soup = episodes_soup.find(
        'div',
        class_='active item'
    )

    for episode in shows_soup.find_all('a'):
        id_episode_list = episode.get('href').encode('utf-8').rsplit('/')
        id_episode = id_episode_list[len(id_episode_list)-1]

        # get token
        file_path_json_token = utils.download_catalog(
            URL_TOKEN,
            '%s_replay_token.json' % (params.channel_name))
        replay_json_token = open(file_path_json_token).read()

        replay_jsonparser_token = json.loads(replay_json_token)
        token = replay_jsonparser_token["token"]

        # get info replay
        file_path_info_replay = utils.download_catalog(
            URL_INFO_REPLAY % (id_episode, str(time.time()).replace('.', '')),
            '%s_%s_info_replay.js' % (params.channel_name, id_episode))
        info_replay_js = open(file_path_info_replay).read()

        info_replay_json = re.compile(r'\((.*?)\)\n').findall(info_replay_js)[0]
        info_replay_jsonparser = json.loads(info_replay_json)
        title = info_replay_jsonparser["titel"].encode('utf-8') + ' ' + \
            info_replay_jsonparser["aflevering_titel"].encode('utf-8')
        img = ''
        if 'images' in info_replay_jsonparser:
            img = info_replay_jsonparser["images"][0]["url"].encode('utf-8')

        plot = info_replay_jsonparser["info"].encode('utf-8')
        duration = 0
        duration = int(info_replay_jsonparser["tijdsduur"].split(':')[0]) * 3600 + \
            int(info_replay_jsonparser["tijdsduur"].split(':')[1]) * 60 \
            + int(info_replay_jsonparser["tijdsduur"].split(':')[2])

        value_date = info_replay_jsonparser["gidsdatum"].split('-')
        day = value_date[2]
        mounth = value_date[1]
        year = value_date[0]

        date = '.'.join((day, mounth, year))
        aired = '-'.join((year, mounth, day))

        # Get HLS link
        file_path_video_replay = utils.download_catalog(
            URL_VIDEO_REPLAY % (id_episode, token),
            '%s_%s_video_replay.js' % (params.channel_name, id_episode))
        video_replay_json = open(file_path_video_replay).read()

        video_replay_jsonparser = json.loads(video_replay_json)
        url_hls = ''
        if 'items' in video_replay_jsonparser:
            for video in video_replay_jsonparser["items"][0]:
                url_json_url_hls = video["url"].encode('utf-8')
                break

            file_path_hls_replay = utils.download_catalog(
                url_json_url_hls + \
                'jsonpCallback%s5910' % (str(time.time()).replace('.', '')),
                '%s_%s_hls_replay.js' % (params.channel_name, id_episode))
            hls_replay_js = open(file_path_hls_replay).read()
            hls_replay_json = re.compile(r'\((.*?)\)').findall(hls_replay_js)[0]
            hls_replay_jsonparser = json.loads(hls_replay_json)

            if 'url' in hls_replay_jsonparser:
                url_hls = hls_replay_jsonparser["url"].encode('utf-8')

        info = {
            'video': {
                'title': title,
                'plot': plot,
                # 'episode': episode_number,
                # 'season': season_number,
                # 'rating': note,
                'aired': aired,
                'date': date,
                'duration': duration,
                'year': year,
                'mediatype': 'tvshow'
            }
        }

        download_video = (
            common.GETTEXT('Download'),
            'XBMC.RunPlugin(' + common.PLUGIN.get_url(
                action='download_video',
                module_path=params.module_path,
                module_name=params.module_name,
                url_hls=url_hls) + ')'
        )
        context_menu = []
        context_menu.append(download_video)

        if url_hls != '':
            videos.append({
                'label': title,
                'thumb': img,
                'fanart': img,
                'url': common.PLUGIN.get_url(
                    module_path=params.module_path,
                    module_name=params.module_name,
                    action='replay_entry',
                    next='play_r',
                    url_hls=url_hls
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
    plot = ''
    duration = 0
    img = ''
    url_live = ''

    file_path = utils.download_catalog(
        URL_LIVE_SITE,
        '%s_live.html' % (params.channel_name))
    live_html = open(file_path).read()
    id_value = re.compile(
        r'<script id="(.*?)"').findall(live_html)[0].split('_')

    # json with hls
    file_path_json = utils.download_catalog(
        JSON_LIVE % (id_value[0], id_value[1], id_value[2]),
        '%s_live.json' % (params.channel_name))
    live_json = open(file_path_json).read()
    live_jsonparser = json.loads(live_json)

    # json with token
    file_path_json_token = utils.download_catalog(
        JSON_LIVE_TOKEN % (id_value[0], id_value[1], id_value[2]),
        '%s_live_token.json' % (params.channel_name))
    live_json_token = open(file_path_json_token).read()
    live_jsonparser_token = json.loads(live_json_token)

    url_live = 'http:' + live_jsonparser["hls"].encode('utf-8') + \
        live_jsonparser_token["token"].encode('utf-8')

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
            url_live=url_live
        ),
        'is_playable': True,
        'info': info
    }


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def get_video_url(params):
    """Get video URL and start video player"""
    if params.next == 'play_l':
        return params.url_live
    elif params.next == 'play_r' or params.next == 'download_video':
        return params.url_hls
