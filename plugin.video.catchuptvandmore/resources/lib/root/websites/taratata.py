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
from resources.lib import resolver
from resources.lib import common


URL_ROOT = 'https://mytaratata.com'

URL_EMBED_FTV = 'http://api-embed.webservices.francetelevisions.fr/key/%s'
# Id Video
# http://embed.francetv.fr/?ue=fb23d5e2c7e5c020b2e710c5fe233aea

SHOW_INFO_FTV = 'http://webservices.francetelevisions.fr/tools/' \
                'getInfosOeuvre/v2/?idDiffusion=%s'
# idDiffusion


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
        'ul', class_='nav navbar-nav').find_all('a')

    for category in list_categories:

        category_title = category.get_text()
        category_url = URL_ROOT + category.get('href')

        value_next = ''
        if 'taratata' in category.get('href'):
            value_next = 'list_shows_taratata'
        elif 'artistes' in category.get('href'):
            value_next = 'list_shows_artistes_1'
        elif 'bonus' in category.get('href'):
            value_next = 'list_shows_bonus'
        else:
            return None

        modes.append({
            'label': category_title,
            'url': common.PLUGIN.get_url(
                module_path=params.module_path,
                module_name=params.module_name,
                action='website_entry',
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
        category=common.get_window_title()
    )


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def list_shows(params):
    """Build categories listing"""
    shows = []
    if 'previous_listing' in params:
        shows = ast.literal_eval(params['previous_listing'])

    if params.next == 'list_shows_taratata':

        list_shows_html = utils.get_webcontent(
            params.category_url + '?page=%s' % params.page)
        list_shows_soup = bs(list_shows_html, 'html.parser')
        list_shows = list_shows_soup.find_all(
            'div', class_='col-md-6')

        for live in list_shows:

            show_title = live.find('img').get('alt')
            show_img = live.find('img').get('src')
            show_url = URL_ROOT + live.find(
                'a').get('href').encode('utf-8')

            shows.append({
                'label': show_title,
                'thumb': show_img,
                'url': common.PLUGIN.get_url(
                    module_path=params.module_path,
                    module_name=params.module_name,
                    action='website_entry',
                    next='list_videos_1',
                    title=show_title,
                    category_url=show_url,
                    window_title=show_title
                )
            })

        # More programs...
        shows.append({
            'label': common.ADDON.get_localized_string(30708),
            'url': common.PLUGIN.get_url(
                module_path=params.module_path,
                module_name=params.module_name,
                action='website_entry',
                next='list_shows_taratata',
                page=str(int(params.page) + 1),
                update_listing=True,
                category_url=params.category_url,
                previous_listing=str(shows)
            )
        })

    elif params.next == 'list_shows_artistes_1':

        # Build categories alphabet artistes
        list_alphabet_html = utils.get_webcontent(params.category_url)
        list_alphabet_soup = bs(list_alphabet_html, 'html.parser')
        list_alphabet = list_alphabet_soup.find(
            'ul', class_='pagination pagination-artists').find_all('a')

        for alphabet in list_alphabet:

            alphabet_title = alphabet.get_text()
            alphabet_url = URL_ROOT + alphabet.get('href')

            shows.append({
                'label': alphabet_title,
                'url': common.PLUGIN.get_url(
                    module_path=params.module_path,
                    module_name=params.module_name,
                    action='website_entry',
                    next='list_shows_artistes_2',
                    title=alphabet_title,
                    category_url=alphabet_url,
                    window_title=alphabet_title
                )
            })

    elif params.next == 'list_shows_artistes_2':

        # Build list artistes
        list_artistes_html = utils.get_webcontent(params.category_url)
        list_artistes_soup = bs(list_artistes_html, 'html.parser')
        list_artistes = list_artistes_soup.find_all(
            'div', class_='slot slot-artist')

        for artiste in list_artistes:

            artiste_title = artiste.find('img').get('alt')
            artiste_url = URL_ROOT + artiste.find('a').get('href')
            artiste_img = artiste.find('img').get('src')

            shows.append({
                'label': artiste_title,
                'thumb': artiste_img,
                'url': common.PLUGIN.get_url(
                    module_path=params.module_path,
                    module_name=params.module_name,
                    action='website_entry',
                    next='list_shows_artistes_3',
                    title=artiste_title,
                    category_url=artiste_url,
                    window_title=artiste_title
                )
            })

    elif params.next == 'list_shows_artistes_3':

        # Build Live and Bonus for an artiste
        videos_artiste_html = utils.get_webcontent(params.category_url)
        videos_artiste_soup = bs(videos_artiste_html, 'html.parser')
        videos_artiste = videos_artiste_soup.find(
            'ul', class_='nav nav-tabs').find_all('a')

        for videos in videos_artiste:

            if 'Infos' not in videos.get_text():
                videos_title = videos.get_text()
                videos_url = URL_ROOT + videos.get('href')

                shows.append({
                    'label': videos_title,
                    'url': common.PLUGIN.get_url(
                        module_path=params.module_path,
                        module_name=params.module_name,
                        action='website_entry',
                        next='list_videos_1',
                        title=videos_title,
                        category_url=videos_url,
                        window_title=videos_title
                    )
                })

    elif params.next == 'list_shows_bonus':

        # Build categories bonus
        list_bonus_html = utils.get_webcontent(params.category_url)
        list_bonus_soup = bs(list_bonus_html, 'html.parser')
        list_bonus = list_bonus_soup.find(
            'ul', class_='nav nav-pills').find_all('a')

        for bonus in list_bonus:

            bonus_title = bonus.get_text()
            bonus_url = URL_ROOT + bonus.get('href')

            shows.append({
                'label': bonus_title,
                'url': common.PLUGIN.get_url(
                    module_path=params.module_path,
                    module_name=params.module_name,
                    action='website_entry',
                    next='list_videos_1',
                    title=bonus_title,
                    page='1',
                    category_url=bonus_url,
                    window_title=bonus_title
                )
            })

    return common.PLUGIN.create_listing(
        shows,
        sort_methods=(
            common.sp.xbmcplugin.SORT_METHOD_LABEL,
            common.sp.xbmcplugin.SORT_METHOD_UNSORTED
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

    if params.next == 'list_videos_1':

        if params.page is not None:
            replay_episodes_html = utils.get_webcontent(
                params.category_url + '?page=%s' % params.page)
        else:
            replay_episodes_html = utils.get_webcontent(
                params.category_url)
        replay_episodes_soup = bs(replay_episodes_html, 'html.parser')
        video_integral = replay_episodes_soup.find(
            'div', class_='col-md-6')
        all_videos = replay_episodes_soup.find_all(
            'div', class_='col-md-3')

        if video_integral is not None:

            video_title = video_integral.find('img').get('alt')
            video_url = URL_ROOT + video_integral.find(
                'a').get('href')
            video_img = video_integral.find('img').get('src')
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

        for video in all_videos:
            video_title = video.find('img').get('alt')
            video_url = URL_ROOT + video.find('a').get('href')
            video_img = video.find('img').get('src')
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

    if params.page is not None:
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
            common.sp.xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE,
            common.sp.xbmcplugin.SORT_METHOD_UNSORTED
        ),
        content='tvshows',
        update_listing='update_listing' in params,
        category=common.get_window_title()
    )


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def get_video_url(params):
    """Get video URL and start video player"""
    url_selected = ''
    all_datas_videos_quality = []
    all_datas_videos_path = []
    videos_html = utils.get_webcontent(params.video_url)
    videos_soup = bs(videos_html, 'html.parser')

    list_videos = videos_soup.find(
        'ul', class_='nav nav-tabs').find_all('a')

    for video in list_videos:
        if '#video-' in video.get('href'):
            # Find a better solution to strip
            all_datas_videos_quality.append(video.get_text().strip())
            # Get link
            value_jwplayer_id = video.get('data-jwplayer-id')
            # Case mp4
            if value_jwplayer_id != '':
                list_streams = videos_soup.find_all(
                    'div', class_='jwplayer')
                for stream in list_streams:
                    if stream.get('id') == value_jwplayer_id:
                        url = stream.get('data-source')
            # Cas Yt
            else:
                video_id = re.compile(
                    'youtube.com/embed/(.*?)\?').findall(videos_html)[0]
                url = resolver.get_stream_youtube(video_id, False)
            all_datas_videos_path.append(url)
        # Get link from FranceTV
        elif '#ftv-player-' in video.get('href'):
            # Find a better solution to strip
            all_datas_videos_quality.append(video.get_text().strip())
            # Get link
            value_ftvlayer_id = video.get('data-ftvplayer-id')
            list_streams = videos_soup.find_all(
                'iframe', class_='embed-responsive-item')
            for stream in list_streams:
                if stream.get('id') == value_ftvlayer_id:
                    url_id = stream.get('src')
            ydl = YoutubeDL()
            ydl.add_default_info_extractors()
            with ydl:
                result = ydl.extract_info(
                    url_id, download=False)
                for format_video in result['formats']:
                    url = format_video['url']
            all_datas_videos_path.append(url)

    if len(all_datas_videos_quality) > 1:
        seleted_item = common.sp.xbmcgui.Dialog().select(
            common.GETTEXT('Choose video quality'),
            all_datas_videos_quality)
        if seleted_item == -1:
            return ''
        url_selected = all_datas_videos_path[seleted_item]
        return url_selected
    else:
        return all_datas_videos_path[0]
