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

import ast
import re
from bs4 import BeautifulSoup as bs
from resources.lib import utils
from resources.lib import common


URL_ROOT = 'http://www.rtl.be/tv/%s/replay'
# channel name : plugrtl, rtltvi or clubrtl

URL_XML = 'http://www.rtl.be/videos/player/replays/%s/%s.xml'
# program_id, video_id

URL_ROOT_LIVE = 'http://www.rtl.be/tv/%s/live'
# channel

URL_XML_LIVE = 'http://www.rtl.be/videos/player/lives/12000/%s.xml'
# live id


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
    if 'previous_listing' in params:
        shows = ast.literal_eval(params['previous_listing'])

    if params.next == 'list_shows_1':
        file_path = utils.download_catalog(
            URL_ROOT % params.channel_name,
            '%s_root.html' % params.channel_name)
        root_html = open(file_path).read()
        root_soup = bs(root_html, 'html.parser')

        main_soup = root_soup.find('main')
        categories_soup = main_soup.find_all(True, recursive=False)

        for category_soup in categories_soup:
            if category_soup.find('h2'):
                h2_titles = category_soup.find_all('h2')
                category_title = h2_titles[len(
                    h2_titles) - 1].get_text().encode('utf-8')
                try:
                    category_url = category_soup.find(
                        'a')['href'].encode('utf-8').replace('//', 'http://')
                except:
                    category_url = ''
                try:
                    category_type = category_soup['type'].encode('utf-8')
                except:
                    category_type = ''

                if category_type == 'videos':
                    next = 'list_videos'
                    videos_len = -1
                elif category_type == 'carousel':
                    next = 'list_shows_carousel'
                    videos_len = -1
                else:
                    videos_len = len(category_soup.find_all(
                        'article',
                        attrs={'card': 'video'}))
                    next = 'list_videos'
                    category_url = URL_ROOT % params.channel_name

                shows.append({
                    'label': category_title,
                    'url': common.PLUGIN.get_url(
                        module_path=params.module_path,
                        module_name=params.module_name,
                        category_title=category_title,
                        action='replay_entry',
                        category_url=category_url,
                        next=next,
                        window_title=category_title,
                        videos_len=videos_len
                    )
                })

    elif params.next == 'list_shows_carousel':
        file_path = utils.download_catalog(
            params.category_url,
            '%s_%s.html' % (
                params.channel_name,
                params.category_title))
        replay_html = open(file_path).read()
        replay_soup = bs(replay_html, 'html.parser')

        categories_soup = replay_soup.find('ul', class_='list')

        for category_soup in categories_soup.find_all('li'):
            category_title = category_soup.find(
                'a').get_text().encode('utf-8').replace(
                    '\n', '').replace(' ', '')
            category_url = category_soup.find(
                'a')['href'].encode('utf-8').replace('//', 'http://')

            shows.append({
                'label': category_title,
                'url': common.PLUGIN.get_url(
                    module_path=params.module_path,
                    module_name=params.module_name,
                    category_title=category_title,
                    action='replay_entry',
                    category_url=category_url,
                    next='list_shows_cat',
                    window_title=category_title,
                    index_page='1'
                )
            })

    elif params.next == 'list_shows_cat':
        file_path = utils.download_catalog(
            params.category_url,
            '%s_%s_%s.html' % (
                params.channel_name,
                params.category_title,
                params.index_page))
        category_html = open(file_path).read()
        category_soup = bs(category_html, 'html.parser')

        programs_soup = category_soup.find_all(
            'article',
            attrs={'card': 'tv-show'})

        for program_soup in programs_soup:
            program_title = program_soup.find('h3').get_text().encode('utf-8')
            program_url = program_soup.find(
                'a')['href'].encode('utf-8').replace('//', 'http://')
            program_url = program_url + '/videos'
            program_img = program_soup.find(
                'img')['src'].encode('utf-8').replace('//', 'http://')
            program_img = utils.get_redirected_url(program_img)

            shows.append({
                'label': program_title,
                'thumb': program_img,
                'url': common.PLUGIN.get_url(
                    module_path=params.module_path,
                    module_name=params.module_name,
                    program_title=program_title,
                    action='replay_entry',
                    program_url=program_url,
                    next='list_videos',
                    window_title=program_title
                )
            })

        if category_soup.find('nav', attrs={'pagination': 'infinite'}):
            url = category_soup.find(
                'nav', attrs={'pagination': 'infinite'}).find(
                'a')['href'].encode('utf-8').replace('//', 'http://')
            # More programs...

            shows.append({
                'label': common.ADDON.get_localized_string(30708),
                'url': common.PLUGIN.get_url(
                    module_path=params.module_path,
                    module_name=params.module_name,
                    category_title=params.category_title,
                    action='replay_entry',
                    category_url=url,
                    next=params.next,
                    window_title=params.category_title,
                    index_page=str(int(params.index_page) + 1),
                    update_listing=True,
                    previous_listing=str(shows)
                )
            })

    return common.PLUGIN.create_listing(
        shows,
        sort_methods=(
            common.sp.xbmcplugin.SORT_METHOD_UNSORTED,
            common.sp.xbmcplugin.SORT_METHOD_LABEL
        ),
        update_listing='update_listing' in params,
        category=common.get_window_title()
    )


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def list_videos(params):
    """Build videos listing"""
    videos = []
    if 'previous_listing' in params:
        videos = ast.literal_eval(params['previous_listing'])

    if 'index_page' in params:
        index_page = params.index_page
    else:
        index_page = '1'

    if 'category_url' in params:
        url = params.category_url
    else:
        url = params.program_url

    if 'category_title' in params:
        title = params.category_title
    else:
        title = params.program_title

    videos_len_bool = False
    if 'videos_len' in params:
        videos_len = int(params.videos_len)
        if videos_len != -1:
            videos_len_bool = True

    file_path = utils.download_catalog(
        url,
        '%s_%s_%s.html' % (
            params.channel_name,
            title,
            index_page))
    videos_html = open(file_path).read()
    videos_soup = bs(videos_html, 'html.parser')

    videos_soup_2 = videos_soup.find_all(
        'article',
        attrs={'card': 'video'})

    if videos_len_bool is True:
        videos_soup_2.insert(0, videos_soup.find_all(
            'article',
            attrs={'card': 'big-video'})[0])

    count = 0

    for video_soup in videos_soup_2:
        if videos_len_bool is True and count > videos_len:
            break
        count += 1
        video_content = video_soup.find('div', class_='content')
        video_title = ''
        if video_content.find('a'):
            video_title = video_content.find(
                'a').get_text().encode('utf-8')
        video_subtitle = video_content.find(
            'h3').get_text().encode('utf-8')
        video_url = video_soup.find(
            'a')['href'].encode('utf-8').replace('//', 'http://')

        video_img = video_soup.find(
            'img')['src'].encode('utf-8').replace('//', 'http://')
        video_img = utils.get_redirected_url(video_img)

        try:
            video_aired = video_soup.find('time')['datetime'].encode('utf-8')
            video_aired = video_aired.split('T')[0]
            video_aired_splited = video_aired.split('-')

            day = video_aired_splited[2]
            mounth = video_aired_splited[1]
            year = video_aired_splited[0]
            video_date = '.'.join((day, mounth, year))
            # date : string (%d.%m.%Y / 01.01.2009)
            # aired : string (2008-12-07)
        except:
            year = 0
            video_aired = ''
            video_date = ''

        if video_subtitle:
            video_title = video_title + ' - [I]' + video_subtitle + '[/I]'

        info = {
            'video': {
                'title': video_title,
                'aired': video_aired,
                'date': video_date,
                'year': int(year),
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
            'label': video_title,
            'thumb': video_img,
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

    if videos_len_bool is False:
        prev_next_soup = videos_soup.find(
            'div',
            attrs={'pagination': 'prev-next'})
        if prev_next_soup.find('a', class_='next'):
            url = prev_next_soup.find(
                'a', class_='next')['href'].encode('utf-8').replace('//', '')
            url = 'http://' + url

            # More videos...
            videos.append({
                'label': common.ADDON.get_localized_string(30700),
                'url': common.PLUGIN.get_url(
                    module_path=params.module_path,
                    module_name=params.module_name,
                    category_title=title,
                    action='replay_entry',
                    category_url=url,
                    next=params.next,
                    window_title=title,
                    index_page=str(int(index_page) + 1),
                    update_listing=True,
                    previous_listing=str(videos)
                )
            })

    return common.PLUGIN.create_listing(
        videos,
        sort_methods=(
            common.sp.xbmcplugin.SORT_METHOD_UNSORTED,
            common.sp.xbmcplugin.SORT_METHOD_DATE,
            common.sp.xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE
        ),
        content='tvshows',
        update_listing='update_listing' in params,
        category=common.get_window_title()
    )


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def get_live_item(params):
    """Build live listing"""
    lives = []

    title = ''
    subtitle = ' - '
    plot = ''
    duration = 0
    img = ''
    url_live = ''

    # get liveid
    file_path = utils.download_catalog(
        URL_ROOT_LIVE % (params.channel_name),
        '%s_live.html' % (params.channel_name))
    live_html = open(file_path).read()

    root_soup = bs(live_html, 'html.parser')
    live_soup = root_soup.find('main', class_="main-container")

    # Live
    if live_soup.find('section'):

        get_liveid = re.compile(
            r'liveid="(.*?)"').findall(live_html)[0]

        file_path = utils.download_catalog(
            URL_XML_LIVE % (get_liveid),
            '%s_live.xml' % (params.channel_name))
        live_xml = open(file_path).read()

        # XML not well build (missing header ...)
        img = 'http://' + re.compile(
            r'<Thumbnail>(.*?)<').findall(live_xml)[0]
        url_live = re.compile(r'<URL_HLS>(.*?)<').findall(live_xml)[0]
        title = re.compile(r'<tv><!\[CDATA\[(.*?)\]').findall(live_xml)[0]
        plot = re.compile(r'<From>(.*?)<').findall(live_xml)[0] + \
            ' - ' + re.compile(r'<To>(.*?)<').findall(live_xml)[0]

        info = {
            'video': {
                'title': title,
                'plot': plot,
                'duration': duration
            }
        }

        lives.append({
            'label': title,
            'fanart': img,
            'thumb': img,
            'url': common.PLUGIN.get_url(
                module_path=params.module_path,
                module_name=params.module_name,
                action='replay_entry',
                next='play_l',
                url_live=url_live,
            ),
            'is_playable': True,
            'info': info
        })
    # No live
    else:

        title = params.channel_name + ' - ' + live_soup.find(
            'div', class_="container").find('h2').get_text().encode('utf-8')

        info = {
            'video': {
                'title': title,
                'plot': plot,
                'duration': duration
            }
        }

        lives.append({
            'label': title,
            'fanart': img,
            'thumb': img,
            'url': common.PLUGIN.get_url(
                module_path=params.module_path,
                module_name=params.module_name,
                action='replay_entry',
                next='play_l',
                url_live=url_live,
            ),
            'is_playable': False,
            'info': info
        })

    return lives


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def get_video_url(params):
    """Get video URL and start video player"""

    if params.next == 'play_r' or params.next == 'download_video':
        video_html = utils.get_webcontent(params.video_url)
        video_soup = bs(video_html, 'html.parser')
        video_id = video_soup.find('div', class_='player')
        video_id = video_id.find('script')['videoid']

        program_id = video_id[:-3] + '000'

        xml = utils.get_webcontent(
            URL_XML % (program_id, video_id))

        m3u8 = re.compile(r'<URL_HLS>(.*?)</URL_HLS>').findall(xml)[0]

        return m3u8

    elif params.next == 'play_l':
        return params.url_live
