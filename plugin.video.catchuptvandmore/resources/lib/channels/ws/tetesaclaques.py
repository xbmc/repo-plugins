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

import ast
import re
from bs4 import BeautifulSoup as bs
from youtube_dl import YoutubeDL
from resources.lib import utils
from resources.lib import common

# TO DO
# Play Spanish Videos

URL_ROOT = 'https://www.tetesaclaques.tv'

URL_YOUTUBE = 'https://www.youtube.com/embed/%s?&autoplay=0'
# YTid

# Initialize GNU gettext emulation in addon
# This allows to use UI strings from addon’s English
# strings.po file instead of numeric codes
_ = common.ADDON.initialize_gettext()


def channel_entry(params):
    """Entry function of the module"""
    if 'root' in params.next:
        return root(params)
    if 'list_shows' in params.next:
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
        'div', class_='jqueryslidemenu').find('ul').find('ul').find_all('li')

    for category in list_categories:

        if 'personnages' in category.find('a').get('href'):
            value_next = 'list_shows_1'
        else:
            value_next = 'list_videos_1'
        category_title = category.find('a').get_text()
        category_url = URL_ROOT + '/' + category.find('a').get('href')

        modes.append({
            'label': category_title,
            'url': common.PLUGIN.get_url(
                action='channel_entry',
                next=value_next,
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
    )


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def list_shows(params):
    """Build categories listing"""
    shows = []

    list_shows_html = utils.get_webcontent(params.category_url)
    list_shows_soup = bs(list_shows_html, 'html.parser')
    list_shows = list_shows_soup.find(
        'div', class_='personnages').find_all('a')

    for personnage in list_shows:

        show_title = personnage.get('title')
        show_img = URL_ROOT + personnage.find('img').get('src')
        show_url = URL_ROOT + personnage.get('href').encode('utf-8')

        shows.append({
            'label': show_title,
            'thumb': show_img,
            'url': common.PLUGIN.get_url(
                action='channel_entry',
                next='list_videos_2',
                title=show_title,
                category_url=show_url,
                window_title=show_title
            )
        })

    return common.PLUGIN.create_listing(
        shows,
        sort_methods=(
            common.sp.xbmcplugin.SORT_METHOD_LABEL,
            common.sp.xbmcplugin.SORT_METHOD_UNSORTED
        ),
    )


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def list_videos(params):
    """Build videos listing"""
    videos = []
    if 'previous_listing' in params:
        videos = ast.literal_eval(params['previous_listing'])

    if params.next == 'list_videos_1':

        replay_episodes_html = utils.get_webcontent(
            params.category_url + '/par_date/%s' % params.page)
        replay_episodes_soup = bs(replay_episodes_html, 'html.parser')

        if 'serietele' in params.category_url:
            episodes = replay_episodes_soup.find(
                'div', class_='serieTele').find_all('div')

            for episode in episodes:
                if episode.find('a') is not None and \
                        episode.find('img', class_='thumb') is not None:
                    video_title = episode.find('a').find(
                        'span', class_='saison-episode'
                    ).get_text().strip() + ' ' + episode.find('img').get('alt')
                    video_url = URL_ROOT + episode.find('a').get('href')
                    video_img = URL_ROOT + '/' + episode.find('img').get('src')
                    video_duration = 0

                    info = {
                        'video': {
                            'title': video_title,
                            # 'aired': aired,
                            # 'date': date,
                            'duration': video_duration,
                            # 'plot': video_plot,
                            # 'year': year,
                            'mediatype': 'tvshow'
                        }
                    }

                    context_menu = []
                    download_video = (
                        _('Download'),
                        'XBMC.RunPlugin(' + common.PLUGIN.get_url(
                            action='download_video',
                            video_url=video_url) + ')'
                    )
                    context_menu.append(download_video)

                    videos.append({
                        'label': video_title,
                        'thumb': video_img,
                        'url': common.PLUGIN.get_url(
                            action='channel_entry',
                            next='play_r',
                            video_url=video_url
                        ),
                        'is_playable': True,
                        'info': info  # ,
                        # 'context_menu': context_menu
                    })
        else:
            episodes = replay_episodes_soup.find_all(
                'a', class_='lienThumbCollection')

            for episode in episodes:
                video_title = episode.find('img').get('alt')
                video_url = URL_ROOT + episode.get('href')
                video_img = URL_ROOT + '/' + episode.find('img').get('src')
                video_duration = 0

                info = {
                    'video': {
                        'title': video_title,
                        # 'aired': aired,
                        # 'date': date,
                        'duration': video_duration,
                        # 'plot': video_plot,
                        # 'year': year,
                        'mediatype': 'tvshow'
                    }
                }

                context_menu = []
                download_video = (
                    _('Download'),
                    'XBMC.RunPlugin(' + common.PLUGIN.get_url(
                        action='download_video',
                        video_url=video_url) + ')'
                )
                context_menu.append(download_video)

                videos.append({
                    'label': video_title,
                    'thumb': video_img,
                    'url': common.PLUGIN.get_url(
                        action='channel_entry',
                        next='play_r',
                        video_url=video_url
                    ),
                    'is_playable': True,
                    'info': info  # ,
                    # 'context_menu': context_menu
                })

        # More videos...
        videos.append({
            'label': '# ' + common.ADDON.get_localized_string(30100),
            'url': common.PLUGIN.get_url(
                action='channel_entry',
                category_url=params.category_url,
                next='list_videos_1',
                page=str(int(params.page) + 1),
                update_listing=True,
                previous_listing=str(videos)
            ),
        })

    elif 'list_videos_2':

        replay_episodes_html = utils.get_webcontent(params.category_url)
        replay_episodes_soup = bs(replay_episodes_html, 'html.parser')
        episodes = replay_episodes_soup.find_all(
            'a', class_='lienThumbCollection')

        for episode in episodes:
            video_title = episode.find('img').get('alt')
            video_url = URL_ROOT + episode.get('href')
            video_img = URL_ROOT + '/' + episode.find('img').get('src')
            video_duration = 0

            info = {
                'video': {
                    'title': video_title,
                    # 'aired': aired,
                    # 'date': date,
                    'duration': video_duration,
                    # 'plot': video_plot,
                    # 'year': year,
                    'mediatype': 'tvshow'
                }
            }

            context_menu = []
            download_video = (
                _('Download'),
                'XBMC.RunPlugin(' + common.PLUGIN.get_url(
                    action='download_video',
                    video_url=video_url) + ')'
            )
            context_menu.append(download_video)

            videos.append({
                'label': video_title,
                'thumb': video_img,
                'url': common.PLUGIN.get_url(
                    action='channel_entry',
                    next='play_r',
                    video_url=video_url
                ),
                'is_playable': True,
                'info': info  # ,
                # 'context_menu': context_menu
            })

    return common.PLUGIN.create_listing(
        videos,
        sort_methods=(
            common.sp.xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE,
            common.sp.xbmcplugin.SORT_METHOD_UNSORTED
        ),
        content='tvshows',
        update_listing='update_listing' in params,
    )


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def get_video_url(params):
    """Get video URL and start video player"""
    video_html = utils.get_webcontent(params.video_url)
    if re.compile('AtedraVideo.video_id = "(.*?)"').findall(video_html):
        url_ytdl = URL_YOUTUBE % re.compile(
            'AtedraVideo.video_id = "(.*?)"').findall(video_html)[0]
    else:
        # TO DO Espagnol Video
        return ''

    ydl = YoutubeDL()
    ydl.add_default_info_extractors()
    with ydl:
        result = ydl.extract_info(url_ytdl, download=False)
        for format_video in result['formats']:
            url = format_video['url']
    return url
