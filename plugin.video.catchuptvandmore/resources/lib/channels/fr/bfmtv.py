# -*- coding: utf-8 -*-
'''
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
'''

import json
from resources.lib import utils
from resources.lib import common

url_token = 'http://api.nextradiotv.com/bfmtv-applications/'

url_menu = 'http://www.bfmtv.com/static/static-mobile/bfmtv/' \
           'ios-smartphone/v0/configuration.json'

url_replay = 'http://api.nextradiotv.com/bfmtv-applications/%s/' \
             'getPage?pagename=replay'
# token

url_show = 'http://api.nextradiotv.com/bfmtv-applications/%s/' \
           'getVideosList?category=%s&count=100&page=%s'
# token, category, page_number

url_video = 'http://api.nextradiotv.com/bfmtv-applications/%s/' \
            'getVideo?idVideo=%s'
# token, video_id


@common.plugin.cached(common.cache_time)
def get_token():
    file_token = utils.get_webcontent(url_token)
    token_json = json.loads(file_token)
    return token_json['session']['token'].encode('utf-8')


def channel_entry(params):
    if 'list_shows' in params.next:
        return list_shows(params)
    elif 'list_videos' in params.next:
        return list_videos(params)
    elif 'play' in params.next:
        return get_video_URL(params)


#@common.plugin.cached(common.cache_time)
def list_shows(params):
    # Create categories list
    shows = []

    if params.next == 'list_shows_1':
        file_path = utils.download_catalog(
            url_replay % get_token(),
            '%s.json' % (params.channel_name))
        file_categories = open(file_path).read()
        json_categories = json.loads(file_categories)
        json_categories = json_categories['page']['contents'][0]
        json_categories = json_categories['elements'][0]['items']

        for categories in json_categories:
            title = categories['title'].encode('utf-8')
            image_url = categories['image_url'].encode('utf-8')
            category = categories['categories'].encode('utf-8')

            shows.append({
                'label': title,
                'thumb': image_url,
                'url': common.plugin.get_url(
                    action='channel_entry',
                    category=category,
                    next='list_videos_1',
                    title=title,
                    page='1'
                )
            })

        return common.plugin.create_listing(
            shows,
            sort_methods=(
                common.sp.xbmcplugin.SORT_METHOD_UNSORTED,
                common.sp.xbmcplugin.SORT_METHOD_LABEL
            )
        )


def list_videos(params):
    videos = []
    if params.next == 'list_videos_1':
        file_path = utils.download_catalog(
            url_show % (
                get_token(),
                params.category,
                params.page),
            '%s_%s_%s.json' % (
                params.channel_name,
                params.category,
                params.page))
        file_show = open(file_path).read()
        json_show = json.loads(file_show)

        for video in json_show['videos']:
            video_id = video['video'].encode('utf-8')
            video_id_ext = video['id_ext'].encode('utf-8')
            category = video['category'].encode('utf-8')
            title = video['title'].encode('utf-8')
            description = video['description'].encode('utf-8')
            begin_date = video['begin_date'] # 1486725600,
            image = video['image'].encode('utf-8')
            duration = video['video_duration_ms'] / 1000

            info = {
                'video': {
                    'title': title,
                    'plot': description,
                    #'aired': aired,
                    #'date': date,
                    'duration': duration,
                    #'year': year,
                    'genre': category
                }
            }

            videos.append({
                'label': title,
                'thumb': image,
                'url': common.plugin.get_url(
                    action='channel_entry',
                    next='play',
                    video_id=video_id,
                    video_id_ext=video_id_ext
                ),
                'is_playable': True,
                'info': info
            })

        # More videos...
        videos.append({
            'label': common.addon.get_localized_string(30100),
            'url': common.plugin.get_url(
                action='channel_entry',
                category=params.category,
                next='list_videos_1',
                title=title,
                page=str(int(params.page) + 1)
            )

        })

        return common.plugin.create_listing(
            videos,
            sort_methods=(
                common.sp.xbmcplugin.SORT_METHOD_UNSORTED,
                common.sp.xbmcplugin.SORT_METHOD_DURATION,
                common.sp.xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE,
                common.sp.xbmcplugin.SORT_METHOD_GENRE,
                common.sp.xbmcplugin.SORT_METHOD_UNSORTED
            ),
            content='tvshows')


@common.plugin.cached(common.cache_time)
def get_video_URL(params):
    file_medias = utils.get_webcontent(
        url_video % (get_token(), params.video_id))
    json_parser = json.loads(file_medias)

    url_hd_plus = ''
    url_hd = ''
    url_sd = ''
    url_sd_minus = ''
    url_default = ''

    for media in json_parser['video']['medias']:
        if media['frame_height'] == 270:
            url_sd_minus = media['video_url'].encode('utf-8')
        elif media['frame_height'] == 360:
            url_sd = media['video_url'].encode('utf-8')
        elif media['frame_height'] == 720:
            url_hd = media['video_url'].encode('utf-8')
        elif media['frame_height'] == 1080:
            url_hd_plus = media['video_url'].encode('utf-8')
        url_default = media['video_url'].encode('utf-8')

    disered_quality = common.plugin.get_setting(
        params.channel_id + '.quality')

    if disered_quality == 'HD+' and url_hd_plus:
        return url_hd_plus
    elif url_hd:
        return url_hd

    if disered_quality == 'HD' and url_hd:
        return url_hd
    elif url_hd_plus:
        return url_hd_plus

    if disered_quality == 'SD' and url_sd:
        return url_sd
    elif url_sd_minus:
        return url_sd_minus

    if disered_quality == 'SD-' and url_sd_minus:
        return url_sd_minus
    elif url_sd:
        return url_sd

    return url_default
