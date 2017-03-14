# -*- coding: utf-8 -*-
"""
    Catch-up TV & More
    Original work (C) JUL1EN094, SPM, SylvainCecchetto
    Copyright (C) 2016  SylvainCecchetto

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


url_auth = 'http://service.mycanal.fr/authenticate.json/iphone/' \
           '1.6?highResolution=1&isActivated=0&isAuthenticated=0&paired=0'

url_categories = 'http://service.mycanal.fr/page/%s/4578.json?' \
                 'cache=60000&nbContent=96'


def channel_entry(params):
    if 'list_shows' in params.next:
        return list_shows(params)
    elif 'list_videos' in params.next:
        return list_videos(params)
    elif 'play' in params.next:
        return get_video_URL(params)


def get_token():
    token_json = utils.get_webcontent(url_auth)
    token_json = json.loads(token_json)
    token = token_json['token']
    return token


@common.plugin.cached(common.cache_time)
def list_shows(params):
    # Create categories list
    shows = []

    if params.next == 'list_shows_1':
        file_path = utils.download_catalog(
            url_categories % get_token(),
            '%s.json' % (params.channel_name))
        file_categories = open(file_path).read()
        json_categories = json.loads(file_categories)

        for strate in json_categories['strates']:
            if strate['type'] == 'textList':
                for content in strate['contents']:
                    title = content['title'].encode('utf-8')
                    url_page = content['onClick']['URLPage'].encode('utf-8')

                    shows.append({
                        'label': title,
                        'url': common.plugin.get_url(
                            action='channel_entry',
                            url_page=url_page,
                            next='list_shows_2',
                            title=title
                        )
                    })

        shows = common.plugin.create_listing(
            shows,
            sort_methods=(
                common.sp.xbmcplugin.SORT_METHOD_UNSORTED,
                common.sp.xbmcplugin.SORT_METHOD_LABEL
            )
        )

    elif params.next == 'list_shows_2':
        # Create category's programs list
        file_path = utils.download_catalog(
            params.url_page,
            '%s.json' % (params.title))
        file_shows = open(file_path).read()
        shows_json = json.loads(file_shows)

        for strate in shows_json['strates']:
            if strate['type'] == 'contentGrid':
                for content in strate['contents']:
                    title = content['title'].encode('utf-8')
                    try:
                        subtitle = content['subtitle'].encode('utf-8')
                    except:
                        subtitle = ''
                    img = content['URLImage'].encode('utf-8')
                    url_page = content['onClick']['URLPage'].encode('utf-8')

                    info = {
                        'video': {
                            'title': title,
                            'plot': subtitle,
                        }
                    }
                    shows.append({
                        'label': title,
                        'thumb': img,
                        'url': common.plugin.get_url(
                            action='channel_entry',
                            next='list_shows_3',
                            url_page=url_page,
                            title=title
                        ),
                        'info': info
                    })

        shows = common.plugin.create_listing(
            shows,
            content='tvshows',
            sort_methods=(
                common.sp.xbmcplugin.SORT_METHOD_UNSORTED,
                common.sp.xbmcplugin.SORT_METHOD_LABEL
            )
        )

    elif params.next == 'list_shows_3':
        # Check if there is any folder for this program
        file_path = utils.download_catalog(
            params.url_page,
            '%s.json' % (params.title))
        file_shows = open(file_path).read()
        shows_json = json.loads(file_shows)

        if 'strates' not in shows_json or len(shows_json['strates']) <= 2:
            params.next = 'list_videos'
            params.title = 'none'
            params.index_page = 1
            return list_videos(params)
        else:
            fanart = ''
            for strate in shows_json['strates']:
                if strate['type'] == 'carrousel':
                    for content in strate['contents']:
                        fanart = content['URLImage'].encode('utf-8')
                elif strate['type'] == 'contentRow':
                    title = strate['title'].encode('utf-8')

                    info = {
                        'video': {
                            'title': title,
                        }
                    }

                    shows.append({
                        'label': title,
                        'fanart': fanart,
                        'url': common.plugin.get_url(
                            action='channel_entry',
                            next='list_videos',
                            url_page=params.url_page,
                            title=title,
                            index_page=1
                        ),
                        'info': info
                    })

            shows = common.plugin.create_listing(
                shows,
                content='tvshows',
                sort_methods=(
                    common.sp.xbmcplugin.SORT_METHOD_UNSORTED,
                    common.sp.xbmcplugin.SORT_METHOD_LABEL
                )
            )

    return shows


@common.plugin.cached(common.cache_time)
def list_videos(params):
    videos = []
    file_path = utils.download_catalog(
        params.url_page,
        '%s.json' % (params.url_page))
    file_videos = open(file_path).read()
    videos_json = json.loads(file_videos)

    more_videos = False
    no_strates = False
    fanart = ''

    if 'strates' not in videos_json:
        no_strates = True
    else:
        for strate in videos_json['strates']:
            if strate['type'] == 'carrousel':
                for content in strate['contents']:
                    fanart = content['URLImage'].encode('utf-8')
            if strate['type'] == 'contentRow' or strate['type'] == 'contentGrid':
                if strate['title'].encode('utf-8') == params.title or params.title == 'none':
                    if 'URLPage' in strate['paging']:
                        url = strate['paging']['URLPage'].encode('utf-8')
                        url = url + '&indexPage=' + params.index_page
                        params.index_page = int(params.index_page) + 1
                        more_videos = True
                        file_videos = utils.get_webcontent(url)
                        videos_json = json.loads(file_videos)

    if more_videos or no_strates:
        if len(videos_json['contents']) == 0:
            more_videos = False
        for content in videos_json['contents']:
            title = content['title'].encode('utf-8')
            try:
                subtitle = content['subtitle'].encode('utf-8')
            except:
                subtitle = ''
            img = content['URLImage'].encode('utf-8')
            url_media = content['onClick']['URLPage'].encode('utf-8')

            info = {
                'video': {
                    'title': title,
                    'plot': subtitle,
                }
            }

            videos.append({
                'label': title,
                'thumb': img,
                'fanart': fanart,
                'url': common.plugin.get_url(
                    action='channel_entry',
                    next='play',
                    url_media=url_media,
                    url_page=params.url_page,
                    title=title,
                    index_page=params.index_page
                ),
                'info': info,
                'is_playable': True
            })
    else:
        for strate in videos_json['strates']:
            if strate['type'] == 'contentRow' or strate['type'] == 'contentGrid':
                if strate['title'].encode('utf-8') == params.title or params.title == 'none':
                    for content in strate['contents']:
                        title = content['title'].encode('utf-8')
                        try:
                            subtitle = content['subtitle'].encode('utf-8')
                        except:
                            subtitle = ''
                        img = content['URLImage'].encode('utf-8')
                        url_media = content['onClick']['URLPage'].encode('utf-8')

                        info = {
                            'video': {
                                'title': title,
                                'plot': subtitle,
                            }
                        }

                        videos.append({
                            'label': title,
                            'thumb': img,
                            'fanart': fanart,
                            'url': common.plugin.get_url(
                                action='channel_entry',
                                next='play',
                                url_media=url_media,
                                url_page=params.url_page,
                                title=title,
                                index_page=params.index_page
                            ),
                            'info': info,
                            'is_playable': True
                        })

    if more_videos:
        videos.append({
            'label': common.addon.get_localized_string(30100),
            'url': common.plugin.get_url(
                action='channel_entry',
                next='list_videos',
                url_media=url_media,
                title=params.title,
                url_page=params.url_page,
                index_page=params.index_page
            ),

        })

    videos = common.plugin.create_listing(
        videos,
        content='tvshows',
        sort_methods=(
            common.sp.xbmcplugin.SORT_METHOD_UNSORTED,
            common.sp.xbmcplugin.SORT_METHOD_LABEL
        )
    )

    return videos


@common.plugin.cached(common.cache_time)
def get_video_URL(params):
    file_path = utils.get_webcontent(params.url_media)
    media_json = json.loads(file_path)
    url = media_json['detail']['informations']['VoD']['videoURL'].encode('utf-8')
    return url
