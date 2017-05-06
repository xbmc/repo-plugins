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

from bs4 import BeautifulSoup as bs
from resources.lib import utils
from resources.lib import common
import json

url_root = "http://www.tf1.fr/"
url_time = 'http://www.wat.tv/servertime2/'
url_token = 'http://api.wat.tv/services/Delivery'

secret_key = 'W3m0#1mFI'
app_name = 'sdk/Iphone/1.0'
version = '2.1.3'
hosting_application_name = 'com.tf1.applitf1'
hosting_application_version = '7.0.4'


def channel_entry(params):
    if 'list_shows' in params.next:
        return list_shows(params)
    elif 'list_videos_categories' in params.next:
        return list_videos_categories(params)
    elif 'list_videos' in params.next:
        return list_videos(params)
    elif 'play' in params.next:
        return get_video_url(params)
    else:
        return None


@common.plugin.cached(common.cache_time)
def list_shows(params):
    shows = []

    url = ''.join((
        url_root,
        params.channel_name,
        '/programmes-tv'))
    file_path = utils.download_catalog(
        url,
        params.channel_name + '.html')
    root_html = open(file_path).read()
    root_soup = bs(root_html, 'html.parser')

    if params.next == 'list_shows_1':
        categories_soup = root_soup.find(
            'ul',
            attrs={'class': 'filters_2 contentopen'})
        for category in categories_soup.find_all('a'):
            category_name = category.get_text().encode('utf-8')
            category_url = category['data-target'].encode('utf-8')

            shows.append({
                'label': category_name,
                'url': common.plugin.get_url(
                    action='channel_entry',
                    category=category_url,
                    next='list_shows_2',
                    window_title=category_name
                )
            })

    elif params.next == 'list_shows_2':
        programs_soup = root_soup.find(
            'ul',
            attrs={'id': 'js_filter_el_container'})
        for program in programs_soup.find_all('li'):
            category = program['data-type'].encode('utf-8')
            if params.category == category or params.category == 'all':
                program_url = program.find(
                    'div',
                    class_='description')
                program_url = program_url.find('a')['href'].encode('utf-8')
                program_name = program.find(
                    'p',
                    class_='program').get_text().encode('utf-8')
                img = program.find('img')
                try:
                    img = img['data-srcset'].encode('utf-8')
                except:
                    img = img['srcset'].encode('utf-8')

                img = 'http:' + img.split(',')[-1].split(' ')[0]

                shows.append({
                    'label': program_name,
                    'thumb': img,
                    'url': common.plugin.get_url(
                        action='channel_entry',
                        program_url=program_url,
                        next='list_videos_categories',
                        window_title=program_name
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
def list_videos_categories(params):
    videos_categories = []
    url = ''.join((
        url_root,
        params.program_url,
        '/videos'))
    program_html = utils.get_webcontent(url)
    program_soup = bs(program_html, 'html.parser')

    filters_1_soup = program_soup.find(
        'ul',
        class_='filters_1')
    for li in filters_1_soup.find_all('li'):
        category_title = li.get_text().encode('utf-8')
        category_id = li.find('a')['data-filter'].encode('utf-8')
        videos_categories.append({
                    'label': category_title,
                    'url': common.plugin.get_url(
                        action='channel_entry',
                        program_url=params.program_url,
                        next='list_videos',
                        window_title=category_title,
                        category_id=category_id
                    )
                })
    return common.plugin.create_listing(
        videos_categories,
        sort_methods=(
            common.sp.xbmcplugin.SORT_METHOD_UNSORTED,
            common.sp.xbmcplugin.SORT_METHOD_LABEL
        )
    )



@common.plugin.cached(common.cache_time)
def list_videos(params):
    videos = []

    url = ''.join((
        url_root,
        params.program_url,
        '/videos/',
        '?filter=',
        params.category_id))
    program_html = utils.get_webcontent(url)
    program_soup = bs(program_html, 'html.parser')

    grid = program_soup.find(
        'ul',
        class_='grid')

    for li in grid.find_all('li'):
        video_type_string = li.find('div', class_='description').find('a')['data-xiti-libelle'].encode('utf-8')
        video_type_string = video_type_string.split('-')[0]

        if 'Playlist' not in video_type_string:
            title = li.find(
                'p',
                class_='title').get_text().encode('utf-8')

            try:
                stitle = li.find(
                    'p',
                    class_='stitle').get_text().encode('utf-8')
            except:
                stitle = ''

            try:
                duration = li.find(
                    'span',
                    attrs={'data-format': 'duration'})
                duration = int(duration.get_text().encode('utf-8'))
            except:
                duration = 0

            img = li.find('img')
            try:
                img = img['data-srcset'].encode('utf-8')
            except:
                img = img['srcset'].encode('utf-8')

            img = 'http:' + img.split(',')[-1].split(' ')[0]

            # aired = li.find(
            #     'span',
            #     attrs={'data-format': None, 'class': 'momentDate'})
            # aired = aired.get_text().encode('utf-8')
            # aired = aired.split('T')[0]
            aired = ''

            # day = aired.split('-')[2]
            # mounth = aired.split('-')[1]
            # year = aired.split('-')[0]
            # date = '.'.join((day, mounth, year))
            date =''
            # date : string (%d.%m.%Y / 01.01.2009)
            # aired : string (2008-12-07)
            program_id = li.find('a')['href'].encode('utf-8')

            info = {
                'video': {
                    'title': title,
                    'plot': stitle,
                    'aired': aired,
                    'date': date,
                    'duration': duration,
                    #'year': int(aired[:4]),
                    'mediatype': 'tvshow'
                }
            }

            videos.append({
                'label': title,
                'thumb': img,
                'url': common.plugin.get_url(
                    action='channel_entry',
                    next='play',
                    program_id=program_id,
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
            common.sp.xbmcplugin.SORT_METHOD_UNSORTED
        ),
        content='tvshows')


@common.plugin.cached(common.cache_time)
def get_video_url(params):
    url = url_root + params.program_id
    video_html = utils.get_webcontent(url)
    video_html_soup = bs(video_html, 'html.parser')

    iframe_player_soup = video_html_soup.find(
        'div',
        class_='iframe_player')

    data_src = iframe_player_soup['data-src'].encode('utf-8')

    video_id = data_src[-8:]

    timeserver = str(utils.get_webcontent(url_time))

    auth_key = '%s-%s-%s-%s-%s' % (
        video_id,
        secret_key,
        app_name,
        secret_key,
        timeserver
    )

    auth_key = common.sp.md5(auth_key).hexdigest()
    auth_key = auth_key + '/' + timeserver

    post_data = {
        'appName': app_name,
        'method': 'getUrl',
        'mediaId': video_id,
        'authKey': auth_key,
        'version': version,
        'hostingApplicationName': hosting_application_name,
        'hostingApplicationVersion': hosting_application_version
    }

    url_video = utils.get_webcontent(
        url=url_token,
        request_type='post',
        post_dic=post_data)
    url_video = json.loads(url_video)
    url_video = url_video['message'].replace('\\', '')

    desired_quality = common.plugin.get_setting(
        params.channel_id + '.quality')

    if desired_quality == 'Force HD':
        try:
            url_video = url_video.split('&bwmax')[0]
        except:
            pass

    return url_video