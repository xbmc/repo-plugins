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
from resources.lib import utils
from resources.lib import common


def channel_entry(params):
    if 'list_shows' in params.next:
        return list_shows(params)
    elif 'list_videos' in params.next:
        return list_videos(params)
    elif 'play' in params.next:
        return get_video_URL(params)


categories = {}

categories['Dessins animés'] = 'http://sslreplay.gulli.fr/replay/api?' \
                               'call=%7B%22api_key%22:%22iphoner_a140e' \
                               'e8cb4b10fcd8b12a7fe688b34de%22,%22method' \
                               '%22:%22programme.getLatestEpisodes%22,%' \
                               '22params%22:%7B%22program_image_thumb%' \
                               '22:%5B310,230%5D,%22category_id%22:%22' \
                               'dessins-animes%22%7D%7D'

categories['Émissions'] = 'https://sslreplay.gulli.fr/replay/api?' \
                          'call=%7B%22api_key%22:%22iphoner_a140e' \
                          'e8cb4b10fcd8b12a7fe688b34de%22,%22method' \
                          '%22:%22programme.getLatestEpisodes%22,%' \
                          '22params%22:%7B%22program_image_thumb%' \
                          '22:%5B310,230%5D,%22category_id%22:%22' \
                          'emissions%22%7D%7D'

categories['Séries & films'] = 'https://sslreplay.gulli.fr/replay/api?' \
                               'call=%7B%22api_key%22:%22iphoner_a140e' \
                               'e8cb4b10fcd8b12a7fe688b34de%22,%22method' \
                               '%22:%22programme.getLatestEpisodes%22,%' \
                               '22params%22:%7B%22program_image_thumb%' \
                               '22:%5B310,230%5D,%22category_id%22:%22' \
                               'series%22%7D%7D'

url_list_show = 'https://sslreplay.gulli.fr/replay/api?call=%%7B%%22api_key' \
                '%%22:%%22iphoner_a140ee8cb4b10fcd8b12a7fe688b34de%%22,%%22' \
                'method%%22:%%22programme.getEpisodesByProgramIds%%22,%%22' \
                'params%%22:%%7B%%22program_id_list%%22:%%5B%%22%s%%22%%5D' \
                '%%7D%%7D'
# program_id


@common.plugin.cached(common.cache_time)
def list_shows(params):
    # Create categories list
    shows = []

    if params.next == 'list_shows_1':
        for category_title, category_url in categories.iteritems():
            shows.append({
                'label': category_title,
                'url': common.plugin.get_url(
                    action='channel_entry',
                    category_url=category_url,
                    next='list_shows_cat',
                    title=category_title
                )
            })

        return common.plugin.create_listing(
            shows,
            sort_methods=(
                common.sp.xbmcplugin.SORT_METHOD_UNSORTED,
                common.sp.xbmcplugin.SORT_METHOD_LABEL
            )
        )

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
                'url': common.plugin.get_url(
                    action='channel_entry',
                    program_id=program_id,
                    next='list_videos',
                    title=program_title
                )
            })

        return common.plugin.create_listing(
            shows,
            sort_methods=(
                common.sp.xbmcplugin.SORT_METHOD_UNSORTED,
                common.sp.xbmcplugin.SORT_METHOD_LABEL
            )
        )


@common.plugin.cached(common.cache_time)
def list_videos(params):
    videos = []

    file_path = utils.download_catalog(
        url_list_show % params.program_id,
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
        url_ipad = show['url_ipad'].encode('utf-8')
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
                'year': year
            }
        }

        videos.append({
            'label': episode_title,
            'thumb': thumb,
            'fanart': fanart,
            'url': common.plugin.get_url(
                action='channel_entry',
                next='play',
                url_ipad=url_ipad
            ),
            'is_playable': True,
            'info': info
        })

    return common.plugin.create_listing(
        videos,
        sort_methods=(
            common.sp.xbmcplugin.SORT_METHOD_UNSORTED,
            common.sp.xbmcplugin.SORT_METHOD_DATE,
            common.sp.xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE
        ),
        content='tvshows')


@common.plugin.cached(common.cache_time)
def get_video_URL(params):
    return params.video_urlhd
