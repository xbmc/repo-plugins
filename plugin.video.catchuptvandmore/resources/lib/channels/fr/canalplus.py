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
import ast


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
    shows = []
    if params.next == 'list_shows_1':
        if 'url_page' not in params:
            params.url_page = url_categories % get_token()
        if 'title' not in params:
            params.title = 'root'
        if 'fanart' in params:
            fanart = params.fanart
        else:
            fanart = ''

        file_path = utils.download_catalog(
            params.url_page,
            '%s_%s_%s.json' % (
                params.channel_name,
                params.title,
                common.sp.md5(params.url_page).hexdigest()))
        file_shows = open(file_path).read()
        shows_json = json.loads(file_shows)
        if 'strates' in shows_json:
            strates = shows_json['strates']
            if len(strates) == 1 and 'textList_like' not in params:
                params['title'] = strates[0]['title'].encode('utf-8')
                params['next'] = 'list_shows_2'
                return list_shows(params)
            elif len(strates) == 2 and 'textList_like' not in params:
                for strate in strates:
                    if strate['type'].encode('utf-8') != 'carrousel':
                        params['title'] = strate['title'].encode('utf-8')
                        params['next'] = 'list_shows_2'
                        return list_shows(params)

            for strate in strates:
                if strate['type'] == 'carrousel':
                    for content in strate['contents']:
                        fanart = content['URLImage'].encode('utf-8')
                # Main categories e.g. Séries, Humour, Sport
                if 'textList_like' in params and params.textList_like is True:
                    if 'title' in strate and \
                            strate['title'].encode('utf-8') == params.title:
                        for content in strate['contents']:
                            title = content['title'].encode('utf-8')
                            url_page = content[
                                'onClick']['URLPage'].encode('utf-8')
                            try:
                                subtitle = content['subtitle'].encode('utf-8')
                            except:
                                subtitle = ''
                            try:
                                img = content['URLImage'].encode('utf-8')
                            except:
                                img = ''

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
                                    url_page=url_page,
                                    next='list_shows_1',
                                    title=title,
                                    window_title=title,
                                    fanart=fanart
                                ),
                                'info': info
                            })
                else:
                    if strate['type'] == 'textList':
                        for content in strate['contents']:
                            title = content['title'].encode('utf-8')
                            url_page = content[
                                'onClick']['URLPage'].encode('utf-8')
                            try:
                                subtitle = content['subtitle'].encode('utf-8')
                            except:
                                subtitle = ''
                            try:
                                img = content['URLImage'].encode('utf-8')
                            except:
                                img = ''

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
                                    url_page=url_page,
                                    next='list_shows_1',
                                    title=title,
                                    window_title=title,
                                    fanart=fanart
                                ),
                                'info': info
                            })
                    # Videos, e.g. "Ne manquez pas"
                    elif strate['type'] == 'contentGrid':
                        title = strate['title'].encode('utf-8')
                        shows.append({
                            'label': title,
                            'url': common.plugin.get_url(
                                action='channel_entry',
                                url_page=params.url_page,
                                next='list_shows_2',
                                title=title,
                                window_title=title,
                            )
                        })
                    # Other levels (subcategories, ...) e.g. "Top emissions"
                    elif strate['type'] == 'contentRow':
                        title = strate['title'].encode('utf-8')
                        shows.append({
                            'label': title,
                            'url': common.plugin.get_url(
                                action='channel_entry',
                                url_page=params.url_page,
                                next='list_shows_2',
                                title=title,
                                window_title=title,
                            )
                        })
        elif 'textList_like' not in params:
            for content in shows_json['contents']:
                title = content['title'].encode('utf-8')
                params['title'] = title
                params['next'] = 'list_shows_2'
                return list_shows(params)

        else:
            for content in shows_json['contents']:
                title = content['title'].encode('utf-8')
                url_page = content[
                    'onClick']['URLPage'].encode('utf-8')
                try:
                    subtitle = content['subtitle'].encode('utf-8')
                except:
                    subtitle = ''
                try:
                    img = content['URLImage'].encode('utf-8')
                except:
                    img = ''

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
                        url_page=url_page,
                        next='list_shows_1',
                        title=title,
                        window_title=title,
                        fanart=fanart
                    ),
                    'info': info
                })

        return common.plugin.create_listing(
            shows,
            sort_methods=(
                common.sp.xbmcplugin.SORT_METHOD_UNSORTED,
                common.sp.xbmcplugin.SORT_METHOD_LABEL
            )
        )

    elif params.next == 'list_shows_2':
        file_path = utils.download_catalog(
            params.url_page,
            '%s_%s_%s.json' % (
                params.channel_name,
                params.title,
                common.sp.md5(params.url_page).hexdigest()))
        file_shows = open(file_path).read()
        shows_json = json.loads(file_shows)

        if 'strates' in shows_json:
            strates = shows_json['strates']
            for strate in strates:
                if 'title' in strate and \
                        strate['title'].encode('utf-8') == params.title:
                    contents = strate['contents']
        else:
            contents = shows_json['contents']
        for content in contents:
            if 'type' in content and \
                    content['type'].encode('utf-8') == 'quicktime':
                return list_videos(params)
            else:
                params['textList_like'] = True
                params['title'] = params.title
                params['next'] = 'list_shows_1'
                return list_shows(params)


@common.plugin.cached(common.cache_time)
def list_videos(params):
    videos = []
    if 'previous_listing' in params:
        videos = ast.literal_eval(params['previous_listing'])
    file_path = utils.download_catalog(
        params.url_page,
        '%s_%s_%s.json' % (
            params.channel_name,
            params.title,
            common.sp.md5(params.url_page).hexdigest()))
    file_videos = open(file_path).read()
    videos_json = json.loads(file_videos)
    more_videos = True
    fanart = ''

    if 'strates' in videos_json:
        for strate in videos_json['strates']:
            if strate['type'] == 'carrousel':
                for content in strate['contents']:
                    fanart = content['URLImage'].encode('utf-8')

            # Check if we are in the correct cotegory
            if 'title' in strate and \
                    strate['title'].encode('utf-8') == params.title:

                # If we have lot of videos ...
                if 'URLPage' in strate['paging']:
                    url = strate['paging']['URLPage'].encode('utf-8')
                    url = url + '&indexPage=1'
                    params['url_page'] = url
                    params['fanart'] = fanart
                    return list_videos(params)

                # Else show only this videos
                else:
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
                                'mediatype': 'tvshow'

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
                                title=title
                            ),
                            'info': info,
                            'is_playable': True
                        })
    else:
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
                    'mediatype': 'tvshow'

                }
            }

            videos.append({
                'label': title,
                'thumb': img,
                'fanart': params.fanart,
                'url': common.plugin.get_url(
                    action='channel_entry',
                    next='play',
                    url_media=url_media,
                    title=title,
                    fanart=params.fanart
                ),
                'info': info,
                'is_playable': True
            })

        if more_videos is True:
            # More videos...
            current_index_page = int(params.url_page[-1])
            videos.append({
                'fanart': params.fanart,
                'label': common.addon.get_localized_string(30100),
                'url': common.plugin.get_url(
                    action='channel_entry',
                    next='list_videos',
                    title=params.title,
                    url_page=params.url_page[:-1] + str(
                        current_index_page + 1),
                    update_listing=True,
                    previous_listing=str(videos),
                    fanart=params.fanart
                ),

            })

    return common.plugin.create_listing(
        videos,
        content='tvshows',
        sort_methods=(
            common.sp.xbmcplugin.SORT_METHOD_UNSORTED,
            common.sp.xbmcplugin.SORT_METHOD_LABEL
        ),
        update_listing='update_listing' in params
    )


@common.plugin.cached(common.cache_time)
def get_video_URL(params):
    file_path = utils.get_webcontent(params.url_media)
    media_json = json.loads(file_path)
    url = media_json['detail']['informations']['VoD']['videoURL'].encode('utf-8')
    return url
