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


url_root = 'http://lab.canal-plus.pro/web/app_prod.php/api/replay/%s'
# Channel id :
# c8 : 1
# cstar : 2

url_shows = 'http://lab.canal-plus.pro/web/app_prod.php/api/pfv/list/%s/%s'
# channel_id/show_id

url_video = 'http://lab.canal-plus.pro/web/app_prod.php/api/pfv/video/%s/%s'
# channel_id/video_id


def get_channel_id(params):
    if params.channel_name == 'c8':
        return '1'
    elif params.channel_name == 'cstar':
        return '2'
    else:
        return '1'


def channel_entry(params):
    if 'list_shows' in params.next:
        return list_shows(params)
    elif 'list_videos' in params.next:
        return list_videos(params)
    elif 'play' in params.next:
        return get_video_URL(params)


@common.plugin.cached(common.cache_time)
def list_shows(params):
    # Create categories list
    shows = []

    if params.next == 'list_shows_1':
        file_path = utils.download_catalog(
            url_root % get_channel_id(params),
            '%s.json' % (params.channel_name))
        file_categories = open(file_path).read()
        json_categories = json.loads(file_categories)

        for categories in json_categories:
            title = categories['title'].encode('utf-8')
            slug = categories['slug'].encode('utf-8')

            shows.append({
                'label': title,
                'url': common.plugin.get_url(
                    action='channel_entry',
                    slug=slug,
                    next='list_shows_2',
                    title=title
                )
            })

        return common.plugin.create_listing(
            shows,
            sort_methods=(
                common.sp.xbmcplugin.SORT_METHOD_UNSORTED,
                common.sp.xbmcplugin.SORT_METHOD_LABEL
            )
        )

    elif params.next == 'list_shows_2':
        # Create category's programs list
        file_path = utils.download_catalog(
            url_root % get_channel_id(params),
            '%s_%s.json' % (params.channel_name, params.slug))
        file_categories = open(file_path).read()
        json_categories = json.loads(file_categories)

        for categories in json_categories:
            if categories['slug'].encode('utf-8') == params.slug:
                for programs in categories['programs']:
                    id = str(programs['id'])
                    title = programs['title'].encode('utf-8')
                    slug = programs['slug'].encode('utf-8')
                    videos_recent = str(programs['videos_recent'])

                    shows.append({
                        'label': title,
                        'url': common.plugin.get_url(
                            action='channel_entry',
                            next='list_videos',
                            id=id,
                            videos_recent=videos_recent,
                            slug=slug,
                            title=title
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
        url_shows % (get_channel_id(params), params.videos_recent),
        '%s_%s.json' % (params.channel_name, params.videos_recent))
    file_videos = open(file_path).read()
    videos_json = json.loads(file_videos)

    for video in videos_json:
        id = video['ID'].encode('utf-8')
        try:
            duration = int(video['DURATION'].encode('utf-8'))
        except:
            duration = 0
        description = video['INFOS']['DESCRIPTION'].encode('utf-8')
        views = int(video['INFOS']['NB_VUES'].encode('utf-8'))
        try:
            date_video = video['INFOS']['DIFFUSION']['DATE'].encode('utf-8')  # 31/12/2017
        except:
            date_video = "00/00/0000"
        day = date_video.split('/')[0]
        mounth = date_video.split('/')[1]
        year = date_video.split('/')[2]
        aired = '-'.join((day, mounth, year))
        date = date_video.replace('/', '.')
        title = video['INFOS']['TITRAGE']['TITRE'].encode('utf-8')
        subtitle = video['INFOS']['TITRAGE']['SOUS_TITRE'].encode('utf-8')
        thumb = video['MEDIA']['IMAGES']['GRAND'].encode('utf-8')
        category = video['RUBRIQUAGE']['CATEGORIE'].encode('utf-8')

        if subtitle:
            title = title + ' - [I]' + subtitle + '[/I]'

        info = {
            'video': {
                'title': title,
                'plot': description,
                'aired': aired,
                'date': date,
                'duration': duration,
                'year': year,
                'genre': category,
                'playcount': views
            }
        }

        videos.append({
            'label': title,
            'thumb': thumb,
            'url': common.plugin.get_url(
                action='channel_entry',
                next='play',
                id=id,
            ),
            'is_playable': True,
            'info': info
        })

    return common.plugin.create_listing(
        videos,
        sort_methods=(
            common.sp.xbmcplugin.SORT_METHOD_DATE,
            common.sp.xbmcplugin.SORT_METHOD_DURATION,
            common.sp.xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE,
            common.sp.xbmcplugin.SORT_METHOD_GENRE,
            common.sp.xbmcplugin.SORT_METHOD_PLAYCOUNT,
            common.sp.xbmcplugin.SORT_METHOD_UNSORTED
        ),
        content='tvshows')



@common.plugin.cached(common.cache_time)
def get_video_URL(params):
    file_video = utils.get_webcontent(
        url_video % (get_channel_id(params), params.id)
    )
    video_json = json.loads(file_video)
    return video_json['main']['MEDIA']['VIDEOS']['HLS'].encode('utf-8')

