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
from bs4 import BeautifulSoup as bs
from resources.lib import utils
from resources.lib import common


SECRET_KEY = '19nBVBxv791Xs'

CATEGORIES = {}

CATEGORIES['Dessins animés'] = 'http://sslreplay.gulli.fr/replay/api?' \
                               'call=%%7B%%22api_key%%22:%%22%s%%22,%%22' \
                               'method%%22:%%22programme.getLatest' \
                               'Episodes%%22,%%22params%%22:%%7B%%22' \
                               'program_image_thumb%%22:%%5B310,230%%5D,%%22' \
                               'category_id%%22:%%22dessins-animes%%22%%7D%%7D'

CATEGORIES['Émissions'] = 'https://sslreplay.gulli.fr/replay/api?' \
                          'call=%%7B%%22api_key%%22:%%22%s%%22,%%22method' \
                          '%%22:%%22programme.getLatestEpisodes%%22,%%' \
                          '22params%%22:%%7B%%22program_image_thumb%%' \
                          '22:%%5B310,230%%5D,%%22category_id%%22:%%22' \
                          'emissions%%22%%7D%%7D'

CATEGORIES['Séries & films'] = 'https://sslreplay.gulli.fr/replay/api?' \
                               'call=%%7B%%22api_key%%22:%%22%s%%22,%%2' \
                               '2method%%22:%%22programme.getLatest' \
                               'Episodes%%22,%%22params%%22:%%7B%%22program_' \
                               'image_thumb%%22:%%5B310,230%%5D,%%22category' \
                               '_id%%22:%%22series%%22%%7D%%7D'

URL_LIST_SHOW = 'https://sslreplay.gulli.fr/replay/api?call=%%7B%%22api_key' \
                '%%22:%%22%s%%22,%%22' \
                'method%%22:%%22programme.getEpisodesByProgramIds%%22,%%22' \
                'params%%22:%%7B%%22program_id_list%%22:%%5B%%22%s%%22%%5D' \
                '%%7D%%7D'

URL_LIVE_TV = 'http://replay.gulli.fr/Direct'

# program_id


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
def get_api_key():
    """Compute the API key"""
    date = time.strftime("%Y%m%d")
    key = SECRET_KEY + date
    key = common.sp.md5(key).hexdigest()
    return 'iphoner_' + key


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def list_shows(params):
    """Build categories listing"""
    shows = []

    if params.next == 'list_shows_1':
        for category_title, category_url in CATEGORIES.iteritems():
            shows.append({
                'label': category_title,
                'url': common.PLUGIN.get_url(
                    module_path=params.module_path,
                    module_name=params.module_name,
                    action='replay_entry',
                    category_url=category_url % get_api_key(),
                    next='list_shows_cat',
                    title=category_title,
                    window_title=category_title
                )
            })

    elif params.next == 'list_shows_cat':
        file_path = utils.download_catalog(
            params.category_url,
            '%s_%s.json' % (params.channel_name, params.title),
            random_ua=True)
        file = open(file_path).read()
        json_category = json.loads(file)

        for show in json_category['res']:
            program_title = show['program_title'.encode('utf-8')]
            program_id = show['program_id'].encode('utf-8')
            fanart = show['program_image'].encode('utf-8')

            shows.append({
                'label': program_title,
                'thumb': fanart,
                'fanart': fanart,
                'url': common.PLUGIN.get_url(
                    module_path=params.module_path,
                    module_name=params.module_name,
                    action='replay_entry',
                    program_id=program_id,
                    next='list_videos',
                    title=program_title,
                    window_title=program_title
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

    file_path = utils.download_catalog(
        URL_LIST_SHOW % (get_api_key(), params.program_id),
        '%s_%s.json' % (params.channel_name, params.program_id))
    file = open(file_path).read()
    json_show = json.loads(file)

    for show in json_show['res']:
        # media_id = show['media_id'].encode('utf-8')
        # program_title = show['program_title'.encode('utf-8')]
        # cat_id = show['cat_id'].encode('utf-8')
        # program_id = show['program_id'].encode('utf-8')
        fanart = show['program_image'].encode('utf-8')
        thumb = show['episode_image'].encode('utf-8')
        episode_title = show['episode_title'].encode('utf-8')
        episode_number = show['episode_number']
        season_number = show['season_number']
        # total_episodes_in_season = show['total_episodes_in_season']
        url_streaming = show['url_streaming'].encode('utf-8')
        # url_streaming = show['url_streaming'].encode('utf-8')
        short_desc = show['short_desc'].encode('utf-8')
        note = float(show['note'].encode('utf-8')) * 2
        date_debut = show['date_debut'].encode('utf-8')
        # "2017-02-03 00:00:00"
        year = int(date_debut[:4])
        day = date_debut[8:10]
        month = date_debut[5:7]
        date = '.'.join((day, month, str(year)))
        aired = '-'.join((str(year), month, day))

        info = {
            'video': {
                'title': episode_title,
                'plot': short_desc,
                'episode': episode_number,
                'season': season_number,
                'rating': note,
                'aired': aired,
                'date': date,
                # 'duration': duration,
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
                url_streaming=url_streaming) + ')'
        )
        context_menu = []
        context_menu.append(download_video)

        videos.append({
            'label': episode_title,
            'thumb': thumb,
            'fanart': fanart,
            'url': common.PLUGIN.get_url(
                module_path=params.module_path,
                module_name=params.module_name,
                action='replay_entry',
                next='play_r',
                url_streaming=url_streaming
            ),
            'is_playable': True,
            'info': info,
            'context_menu': context_menu
        })

    return common.PLUGIN.create_listing(
        videos,
        sort_methods=(
            common.sp.xbmcplugin.SORT_METHOD_UNSORTED,
            common.sp.xbmcplugin.SORT_METHOD_DATE,
            common.sp.xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE
        ),
        content='tvshows',
        category=common.get_window_title()
    )


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def start_live_tv_stream(params):
    url_live = ''

    file_path = utils.download_catalog(
        URL_LIVE_TV,
        params.channel_name + '_live.html')
    root_live_html = open(file_path).read()
    root_live_soup = bs(root_live_html, 'html.parser')

    live_soup = root_live_soup.find(
        'div',
        class_='wrapperVideo'
    )

    url_live_embeded = ''
    for live in live_soup.find_all('iframe'):
        url_live_embeded = live.get('src').encode('utf-8')

    file_path_2 = utils.download_catalog(
        url_live_embeded,
        params.channel_name + '_live_embeded.html')
    root_live_embeded_html = open(file_path_2).read()

    all_url_video = re.compile(
        r'file: \'(.*?)\'').findall(root_live_embeded_html)

    for url_video in all_url_video:
        if url_video.count('m3u8') > 0:
            url_live = url_video

    params['next'] = 'play_l'
    params['url_live'] = url_live
    return get_video_url(params)


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def get_video_url(params):
    """Get video URL and start video player"""
    if params.next == 'play_r' or params.next == 'download_video':
        url_root = params.url_streaming.replace('playlist.m3u8', '')
        m3u8_content = utils.get_webcontent(params.url_streaming)
        last_url = ''

        for line in m3u8_content.splitlines():
            if 'm3u8' in line and 'video' in line:
                last_url = line

        return url_root + last_url

    elif params.next == 'play_l':
        return params.url_live
