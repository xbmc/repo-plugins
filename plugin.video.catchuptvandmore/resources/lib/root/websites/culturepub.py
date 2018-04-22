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
import json
import re
from bs4 import BeautifulSoup as bs
from resources.lib import utils
from resources.lib import common


URL_ROOT = 'http://www.culturepub.fr'

INFO_VIDEO = 'http://api.cbnews.webtv.flumotion.com/videos/%s'
# IdVideo

INFO_STREAM = 'http://cbnews.ondemand.flumotion.com/video/mp4/%s/%s.mp4'
# Quality, IdStream


QUALITIES_STREAM = ['low', 'hd']


def website_entry(params):
    """Entry function of the module"""
    if 'root' in params.next:
        return root(params)
    elif 'list_shows' in params.next:
        return list_shows(params)
    elif 'list_videos' in params.next:
        return list_videos(params)
    elif 'play' in params.next:
        return get_video_url(params)
    return None


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def root(params):
    """Add modes in the listing"""
    modes = []

    list_categories_html = utils.get_webcontent(URL_ROOT)
    list_categories_soup = bs(list_categories_html, 'html.parser')
    list_categories = list_categories_soup.find(
        'ul', class_='nav').find_all('a', class_='dropdown-toggle')

    for category in list_categories:

        if 'emissions' in category.get('href'):
            category_title = category.get_text().strip()
            category_url = URL_ROOT + category.get('href')

            modes.append({
                'label': category_title,
                'url': common.PLUGIN.get_url(
                    module_path=params.module_path,
                    module_name=params.module_name,
                    action='website_entry',
                    next='list_shows_1',
                    title=category_title,
                    category_url=category_url,
                    window_title=category_title
                )
            })

        elif 'videos' in category.get('href'):
            category_title = category.get_text().strip()
            category_url = URL_ROOT + category.get('href')

            modes.append({
                'label': category_title,
                'url': common.PLUGIN.get_url(
                    module_path=params.module_path,
                    module_name=params.module_name,
                    action='website_entry',
                    next='list_videos_1',
                    title=category_title,
                    page='1',
                    category_url=category_url,
                    window_title=category_title
                )
            })

    return common.PLUGIN.create_listing(
        modes,
        sort_methods=(
            common.sp.xbmcplugin.SORT_METHOD_LABEL,
            common.sp.xbmcplugin.SORT_METHOD_UNSORTED
        ),
        category=common.get_window_title()
    )


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def list_shows(params):
    """Build categories listing"""
    shows = []

    list_shows_html = utils.get_webcontent(params.category_url)
    list_shows_soup = bs(list_shows_html, 'html.parser')
    list_shows = list_shows_soup.find_all(
        'div',
        class_='widget-header')

    for show in list_shows:

        show_title = show.find('h3').get_text()
        show_url = show.find('a').get('href').encode('utf-8')

        shows.append({
            'label': show_title,
            'url': common.PLUGIN.get_url(
                module_path=params.module_path,
                module_name=params.module_name,
                action='website_entry',
                next='list_videos_1',
                title=show_title,
                page='1',
                category_url=show_url,
                window_title=show_title
            )
        })

    return common.PLUGIN.create_listing(
        shows,
        sort_methods=(
            common.sp.xbmcplugin.SORT_METHOD_UNSORTED
        ),
        category=common.get_window_title()
    )


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def list_videos(params):
    """Build videos listing"""
    videos = []
    if 'previous_listing' in params:
        videos = ast.literal_eval(params['previous_listing'])

    if params.next == 'list_videos_1':

        replay_videos_html = utils.get_webcontent(
            params.category_url + '?paged=%s' % params.page)
        replay_videos_soup = bs(replay_videos_html, 'html.parser')
        all_videos = replay_videos_soup.find_all('article')

        for video in all_videos:

            video_title = video.find('h2').find(
                'a').get('title').encode('utf-8')
            if video.find('img').get('data-src'):
                video_img = video.find('img').get('data-src')
            else:
                video_img = video.find('img').get('src')
            video_url = URL_ROOT + video.find('h2').find(
                'a').get('href').encode('utf-8')

            info = {
                'video': {
                    'title': video_title,
                    # 'aired': aired,
                    # 'date': date,
                    # 'duration': video_duration,
                    # 'plot': video_plot,
                    # 'year': year,
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
                    action='website_entry',
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
                action='website_entry',
                category_url=params.category_url,
                next=params.next,
                page=str(int(params.page) + 1),
                title=params.title,
                window_title=params.window_title,
                update_listing=True,
                previous_listing=str(videos)
            )
        })

    return common.PLUGIN.create_listing(
        videos,
        sort_methods=(
            common.sp.xbmcplugin.SORT_METHOD_UNSORTED
        ),
        content='tvshows',
        update_listing='update_listing' in params,
        category=common.get_window_title()
    )


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def get_video_url(params):
    """Get video URL and start video player"""

    info_video_html = utils.get_webcontent(params.video_url)
    video_id = re.compile(
        'player=7&pod=(.*?)[\"\&]').findall(
        info_video_html)[0]

    info_video_json = utils.get_webcontent(INFO_VIDEO % video_id)
    info_video_json = json.loads(info_video_json)

    stream_id = re.compile(
        'images/(.*).jpg').findall(
        info_video_json["thumbnail_url_static"])[0].split('/')[1]

    desired_quality = common.PLUGIN.get_setting('quality')
    all_datas_videos_quality = []
    all_datas_videos_path = []
    for quality in QUALITIES_STREAM:
        all_datas_videos_quality.append(quality)
        all_datas_videos_path.append(
            INFO_STREAM % (quality, stream_id))

    if desired_quality == "DIALOG":
        seleted_item = common.sp.xbmcgui.Dialog().select(
            common.GETTEXT('Choose video quality'),
            all_datas_videos_quality)
        if seleted_item == -1:
            return ''
        return all_datas_videos_path[seleted_item]
    elif desired_quality == "BEST":
        url_best = ''
        for data_video in all_datas_videos_path:
            url_best = data_video
        return url_best
    else:
        return all_datas_videos_path[0]
