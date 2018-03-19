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
import ast
from bs4 import BeautifulSoup as bs
from resources.lib import utils
from resources.lib import common


URL_ROOT_BRF = 'https://m.brf.be/'


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

    # Get categories :
    file_path = utils.download_catalog(
        URL_ROOT_BRF,
        '%s_categories.html' % (
            params.channel_name))
    root_html = open(file_path).read()
    root_soup = bs(root_html, 'html.parser')

    menu_soup = root_soup.find('ul', class_="off-canvas-list")
    categories_soup = menu_soup.find_all('a')

    for category in categories_soup:

        category_name = category.get_text().encode('utf-8')
        category_url = category.get('href')

        if 'http' in category_url:
            shows.append({
                'label': category_name,
                'url': common.PLUGIN.get_url(
                    module_path=params.module_path,
                    module_name=params.module_name,
                    action='replay_entry',
                    category_url=category_url,
                    page='1',
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

    url_videos = params.category_url + 'page/%s' % params.page

    file_path = utils.download_catalog(
        url_videos,
        '%s_%s_%s.html' % (
            params.channel_name,
            params.category_name,
            params.page))
    root_html = open(file_path).read()
    root_soup = bs(root_html, 'html.parser')
    programs_soup = root_soup.find_all(
        'article', class_='post column small-12 medium-6 large-4 left')

    for program in programs_soup:

        video_url = program.find_all(
            'a')[0].get('href').encode('utf-8')
        title = program.find_all(
            'a')[0].get('title').encode('utf-8')
        img = program.find_all(
            'a')[0].find('img').get('src').encode('utf-8')

        date = program.find(
            'time').get_text().split('-')[0].strip().split('.')
        if len(date[0]) == 1:
            day = "0" + date[0]
        else:
            day = date[0]
        if len(date[1]) == 1:
            mounth = "0" + date[1]
        else:
            mounth = date[1]
        year = date[2]

        date = '.'.join((day, mounth, year))
        aired = '-'.join((year, mounth, day))

        duration_list = program.find(
            'time').get_text().split('-')[1].strip().split(':')
        duration = int(duration_list[0]) * 60 + int(duration_list[1])

        info = {
            'video': {
                'title': title,
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
                video_url=video_url) + ')'
        )
        context_menu = []
        context_menu.append(download_video)

        videos.append({
            'label': title,
            'thumb': img,
            'fanart': img,
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
            common.sp.xbmcplugin.SORT_METHOD_UNSORTED,
            common.sp.xbmcplugin.SORT_METHOD_PLAYCOUNT,
            common.sp.xbmcplugin.SORT_METHOD_DATE,
            common.sp.xbmcplugin.SORT_METHOD_DURATION,
            common.sp.xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE
        ),
        content='tvshows',
        update_listing='update_listing' in params,
        category=common.get_window_title()
    )


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def get_video_url(params):
    """Get video URL and start video player"""
    if params.next == 'play_r' or params.next == 'download_video':
        video_html = utils.get_webcontent(
            params.video_url)
        url_video = re.compile(
            r'jQuery.get\("(.*?)"').findall(video_html)[0]
        if params.next == 'download_video':
            return url_video
        else:
            url = utils.get_webcontent(
                url_video)
            return re.compile(
                r'src="(.*?)"').findall(url)[0]

