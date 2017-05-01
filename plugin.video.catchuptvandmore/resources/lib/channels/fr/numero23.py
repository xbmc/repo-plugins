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

from bs4 import BeautifulSoup as bs
from resources.lib import utils
from resources.lib import common
import ast
import re

url_root = 'http://www.numero23.fr/replay/'


def channel_entry(params):
    if 'list_shows' in params.next:
        return list_shows(params)
    elif 'list_videos' in params.next:
        return list_videos(params)
    elif 'play' in params.next:
        return get_video_url(params)
    else:
        return None


@common.plugin.cached(common.cache_time)
def list_shows(params):
    shows = []
    if 'previous_listing' in params:
        shows = ast.literal_eval(params['previous_listing'])
    unique_item = {}
    if 'unique_item' in params:
        unique_item = ast.literal_eval(params['unique_item'])

    if params.next == 'list_shows_1':
        file_path = utils.download_catalog(
            url_root,
            params.channel_name + '.html')
        root_html = open(file_path).read()
        root_soup = bs(root_html, 'html.parser')

        categories_soup = root_soup.find(
            'div',
            class_='nav-programs'
        )

        for category in categories_soup.find_all('a'):
            category_name = category.find('span').get_text().encode('utf-8')
            category_url = category['href'].encode('utf-8')

            shows.append({
                'label': category_name,
                'url': common.plugin.get_url(
                    action='channel_entry',
                    category_url=category_url,
                    next='list_shows_cat',
                    window_title=category_name,
                    category_name=category_name,
                    page='1'
                )
            })

    elif params.next == 'list_shows_cat':
        url_splited = params.category_url.split('?')
        url_category = url_splited[0] + 'page/' + \
            params.page + '/?' + url_splited[1]
        file_path = utils.download_catalog(
            url_category,
            '%s_%s.html' % (params.channel_name, params.category_name)
        )
        category_html = open(file_path).read()
        category_soup = bs(category_html, 'html.parser')

        programs_soup = category_soup.find(
            'div',
            class_='videos replay'
        )
        for program in programs_soup.find_all('div', class_='program'):
            program_name_url = program.find('h3').find('a')
            program_name = program_name_url.get_text().encode('utf-8')
            if program_name not in unique_item:
                unique_item[program_name] = program_name
                program_url = program_name_url['href'].encode('utf-8')
                program_img = program.find('img')['src'].encode('utf-8')

                shows.append({
                    'label': program_name,
                    'thumb': program_img,
                    'url': common.plugin.get_url(
                        action='channel_entry',
                        program_url=program_url,
                        next='list_videos',
                        window_title=program_name,
                        program_name=program_name
                    )
                })

        # More videos...
        shows.append({
            'label': common.addon.get_localized_string(30108),
            'url': common.plugin.get_url(
                action='channel_entry',
                next='list_shows_cat',
                page=str(int(params.page) + 1),
                window_title=params.window_title,
                update_listing=True,
                unique_item=str(unique_item),
                category_url=params.category_url,
                category_name=params.category_name,
                previous_listing=str(shows)

            )
        })

    return common.plugin.create_listing(
        shows,
        sort_methods=(
            common.sp.xbmcplugin.SORT_METHOD_UNSORTED,
            common.sp.xbmcplugin.SORT_METHOD_LABEL
        ),
        update_listing='update_listing' in params,
    )


@common.plugin.cached(common.cache_time)
def list_videos(params):
    videos = []

    file_path = utils.download_catalog(
        params.program_url,
        '%s_%s.html' % (params.channel_name, params.program_name)
    )
    program_html = open(file_path).read()
    program_soup = bs(program_html, 'html.parser')

    videos_soup = program_soup.find_all('div', class_='box program')

    if len(videos_soup) == 0:
        videos_soup = program_soup.find_all(
            'div', class_='program sticky video')

    for video in videos_soup:
        video_title = video.find(
            'p').get_text().encode('utf-8').replace(
                '\n', ' ').replace('\r', ' ').rstrip('\r\n')
        video_img = video.find('img')['src'].encode('utf-8')
        video_url = video.find('a')['href'].encode('utf-8')

        info = {
            'video': {
                'title': video_title,
                'mediatype': 'tvshow'
            }
        }

        videos.append({
            'label': video_title,
            'thumb': video_img,
            'url': common.plugin.get_url(
                action='channel_entry',
                next='play',
                video_url=video_url
            ),
            'is_playable': True,
            'info': info
        })

    return common.plugin.create_listing(
        videos,
        sort_methods=(
            common.sp.xbmcplugin.SORT_METHOD_UNSORTED,
            common.sp.xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE
        ),
        content='tvshows')


@common.plugin.cached(common.cache_time)
def get_video_url(params):
    video_html = utils.get_webcontent(
        params.video_url
    )
    video_soup = bs(video_html, 'html.parser')
    video_id = video_soup.find(
        'div', class_='video')['data-video-id'].encode('utf-8')

    url_daily = 'http://www.dailymotion.com/embed/video/' + video_id

    html_daily = utils.get_webcontent(
        url_daily,)

    html_daily = html_daily.replace('\\', '')

    urls_mp4 = re.compile(
        r'{"type":"video/mp4","url":"(.*?)"}],"(.*?)"').findall(html_daily)

    for url, quality in urls_mp4:
        if quality == '480':
            url_sd = url
        elif quality == '720':
            url_hd = url
        elif quality == '1080':
            url_hdplus = url
        else:
            continue
        url_default = url

    desired_quality = common.plugin.get_setting(
        params.channel_id + '.quality')

    if desired_quality == 'HD+' and url_hdplus is not None:
        return url_hdplus
    elif desired_quality == 'HD' and url_hd is not None:
        return url_hd
    elif desired_quality == 'SD' and url_sd is not None:
        return url_sd
    else:
        return url_default
