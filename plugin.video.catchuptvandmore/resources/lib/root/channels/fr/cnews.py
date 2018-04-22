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

import re
import json
import ast
from bs4 import BeautifulSoup as bs
from resources.lib import utils
from resources.lib import common


# URL :
URL_ROOT_SITE = 'http://www.cnews.fr'

# Live :
URL_LIVE_CNEWS = URL_ROOT_SITE + '/direct'

# Replay CNews
URL_VIDEOS_CNEWS = URL_ROOT_SITE + '/videos/'
URL_EMISSIONS_CNEWS = URL_ROOT_SITE + '/emissions'

# Replay/Live => VideoId
URL_INFO_CONTENT = 'https://secure-service.canal-plus.com/' \
                   'video/rest/getVideosLiees/cplus/%s?format=json'


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
    """Create categories list"""
    shows = []

    if params.next == 'list_shows_1':

        file_path = utils.download_catalog(
            URL_VIDEOS_CNEWS,
            '%s_categories.html' % (
                params.channel_name))
        root_html = open(file_path).read()
        root_soup = bs(root_html, 'html.parser')

        menu_soup = root_soup.find('div', class_="nav-tabs-inner")

        categories_soup = menu_soup.find_all('a')

        for category in categories_soup:

            category_name = category.get_text().encode('utf-8')
            category_url = URL_ROOT_SITE + category.get('href')

            if category_name != 'Les tops':
                shows.append({
                    'label': category_name,
                    'url': common.PLUGIN.get_url(
                        module_path=params.module_path,
                        module_name=params.module_name,
                        action='replay_entry',
                        category_url=category_url,
                        category_name=category_name,
                        next='list_shows_2',
                        window_title=category_name
                    )
                })

    elif params.next == 'list_shows_2':

        if params.category_name == 'Les sujets':

            file_path = utils.download_catalog(
                params.category_url,
                '%s_%s.html' % (
                    params.channel_name, params.category_name))
            root_html = open(file_path).read()
            root_soup = bs(root_html, 'html.parser')
            categories_soup = root_soup.find_all('a', class_="checkbox")

            for category in categories_soup:

                category_name = category.get_text().encode('utf-8')
                category_url = URL_ROOT_SITE + category.get('href')

                shows.append({
                    'label': category_name,
                    'url': common.PLUGIN.get_url(
                        module_path=params.module_path,
                        module_name=params.module_name,
                        action='replay_entry',
                        category_url=category_url,
                        page="1",
                        category_name=category_name,
                        next='list_videos',
                        window_title=category_name
                    )
                })
        else:
            # Find all emissions
            file_path = utils.download_catalog(
                URL_EMISSIONS_CNEWS,
                '%s_ALL_EMISSION.html' % (
                    params.channel_name))
            root_html = open(file_path).read()
            root_soup = bs(root_html, 'html.parser')

            categories_soup = root_soup.find_all('article', class_="item")

            for category in categories_soup:

                category_name = category.find('h3').get_text().encode('utf-8')
                category_url = URL_VIDEOS_CNEWS + \
                    '/emissions' + \
                    category.find('a').get('href').split('.fr')[1]
                category_img = category.find('img').get('src').encode('utf-8')

                shows.append({
                    'label': category_name,
                    'thumb': category_img,
                    'fanart': category_img,
                    'url': common.PLUGIN.get_url(
                        module_path=params.module_path,
                        module_name=params.module_name,
                        action='replay_entry',
                        category_url=category_url,
                        page="1",
                        category_name=category_name,
                        next='list_videos',
                        window_title=category_name
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
    if 'previous_listing' in params:
        videos = ast.literal_eval(params['previous_listing'])

    if params.channel_name == 'cnews':

        url_page = params.category_url + '/page/%s' % params.page

        file_path = utils.download_catalog(
            url_page,
            '%s_%s_%s.html' % (
                params.channel_name, params.category_name, params.page))
        root_html = open(file_path).read()
        root_soup = bs(root_html, 'html.parser')

        programs = root_soup.find_all('article', class_='item')

        for program in programs:
            title = program.find('h3').get_text().encode('utf-8')
            thumb = program.find('img').get('src').encode('utf-8')
            # Get Video_ID
            video_html = utils.get_webcontent(
                program.find('a').get('href').encode('utf-8'))
            id = re.compile(r'videoId=(.*?)"').findall(video_html)[0]
            # Get Description
            datas_video = bs(video_html, 'html.parser')
            description = datas_video.find(
                'article', class_='entry-body').get_text().encode('utf-8')
            duration = 0

            date = re.compile(
                r'property="video:release_date" content="(.*?)"'
            ).findall(video_html)[0].split('T')[0].split('-')
            day = date[2]
            mounth = date[1]
            year = date[0]

            date = '.'.join((day, mounth, year))
            aired = '-'.join((year, mounth, day))

            info = {
                'video': {
                    'title': title,
                    'plot': description,
                    'aired': aired,
                    'date': date,
                    'duration': duration,
                    'year': year,
                    # 'genre': category,
                    'mediatype': 'tvshow'
                }
            }

            download_video = (
                common.GETTEXT('Download'),
                'XBMC.RunPlugin(' + common.PLUGIN.get_url(
                    action='download_video',
                    module_path=params.module_path,
                    module_name=params.module_name,
                    id=id) + ')'
            )
            context_menu = []
            context_menu.append(download_video)

            videos.append({
                'label': title,
                'thumb': thumb,
                'fanart': thumb,
                'url': common.PLUGIN.get_url(
                    module_path=params.module_path,
                    module_name=params.module_name,
                    action='replay_entry',
                    next='play_r',
                    id=id
                ),
                'is_playable': True,
                'info': info,
                'context_menu': context_menu
            })

        # More videos...
        videos.append({
            'label': common.ADDON.get_localized_string(30700),
            'url': common.PLUGIN.get_url(
                module_path=params.module_path,
                module_name=params.module_name,
                action='replay_entry',
                category_url=params.category_url,
                category_name=params.category_name,
                next='list_videos',
                page=str(int(params.page) + 1),
                update_listing=True,
                previous_listing=str(videos)
            )
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
        update_listing='update_listing' in params,
        category=common.get_window_title()
    )


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def start_live_tv_stream(params):
    file_path_html = utils.download_catalog(
        URL_LIVE_CNEWS,
        '%s_live.html' % (params.channel_name)
    )
    html_live = open(file_path_html).read()

    video_id_re = re.compile(r'content: \'(.*?)\'').findall(html_live)

    file_live_json = utils.get_webcontent(
        URL_INFO_CONTENT % (video_id_re[0]))
    json_parser = json.loads(file_live_json)

    url_live = json_parser[0]["MEDIA"]["VIDEOS"]["IPAD"].encode('utf-8')
    params['next'] = 'play_l'
    params['url'] = url_live
    return get_video_url(params)


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def get_video_url(params):
    """Get video URL and start video player"""
    if params.next == 'play_r' or params.next == 'download_video':
        file_video = utils.get_webcontent(
            URL_INFO_CONTENT % (params.id)
        )
        media_json = json.loads(file_video)
        stream_url = ''
        for media in media_json:
            if media['ID'] == params.id:
                stream_url = media['MEDIA']['VIDEOS']['HLS'].encode('utf-8')
        return stream_url
    elif params.next == 'play_l':
        return params.url
