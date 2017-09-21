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
import ast
from bs4 import BeautifulSoup as bs
from resources.lib import utils
from resources.lib import common

# TO DO
# Add info LIVE TV

# Initialize GNU gettext emulation in addon
# This allows to use UI strings from addon’s English
# strings.po file instead of numeric codes
_ = common.ADDON.initialize_gettext()

URL_ROOT = 'https://www.publicsenat.fr'

URL_LIVE_SITE = 'https://www.publicsenat.fr/direct'

URL_DAILYMOTION_EMBED = 'http://www.dailymotion.com/embed/video/%s'

def channel_entry(params):
    """Entry function of the module"""
    if 'root' in params.next:
        return root(params)
    elif 'list_shows' in params.next:
        return list_shows(params)
    elif 'list_videos' in params.next:
        return list_videos(params)
    elif 'live' in params.next:
        return list_live(params)
    elif 'play' in params.next:
        return get_video_url(params)

CATEGORIES = {
    'https://www.publicsenat.fr/recherche/type/episode/' \
    'field_theme/politique-4127?sort_by=pse_search_date_publication' : 'Politique',
    'https://www.publicsenat.fr/recherche/type/episode/' \
    'field_theme/societe-4126?sort_by=pse_search_date_publication' : 'Société',
    'https://www.publicsenat.fr/recherche/type/episode/' \
    'field_theme/debat-4128?sort_by=pse_search_date_publication' : 'Débat'
}

CORRECT_MONTH = {
    'janvier' : '01',
    'février' : '02',
    'mars' : '03',
    'avril' : '04',
    'mai' : '05',
    'juin' : '06',
    'juillet' : '07',
    'août' : '08',
    'septembre' : '09',
    'octobre' : '10',
    'novembre' : '11',
    'décembre' : '12'
}

@common.PLUGIN.cached(common.CACHE_TIME)
def root(params):
    """Add Replay and Live in the listing"""
    modes = []

    # Add Replay
    modes.append({
        'label' : 'Replay',
        'url': common.PLUGIN.get_url(
            action='channel_entry',
            next='list_shows_1',
            category='%s Replay' % params.channel_name.upper(),
            window_title='%s Replay' % params.channel_name.upper()
        ),
    })

    # Add Live
    modes.append({
        'label' : 'Live TV',
        'url': common.PLUGIN.get_url(
            action='channel_entry',
            next='live_cat',
            category='%s Live TV' % params.channel_name.upper(),
            window_title='%s Live TV' % params.channel_name.upper()
        ),
    })

    return common.PLUGIN.create_listing(
        modes,
        sort_methods=(
            common.sp.xbmcplugin.SORT_METHOD_UNSORTED,
            common.sp.xbmcplugin.SORT_METHOD_LABEL
        ),
    )

@common.PLUGIN.cached(common.CACHE_TIME)
def list_shows(params):
    """Build shows listing"""
    shows = []

    if params.next == 'list_shows_1':

        for category_url, category_name in CATEGORIES.iteritems():

            shows.append({
                'label': category_name,
                'url': common.PLUGIN.get_url(
                    action='channel_entry',
                    category_url=category_url,
                    category_name=category_name,
                    page='0',
                    next='list_videos_1',
                    window_title=category_name
                )
            })

    return common.PLUGIN.create_listing(
        shows,
        sort_methods=(
            common.sp.xbmcplugin.SORT_METHOD_UNSORTED,
            common.sp.xbmcplugin.SORT_METHOD_LABEL
        )
    )

@common.PLUGIN.cached(common.CACHE_TIME)
def list_videos(params):
    """Build videos listing"""
    videos = []

    if 'previous_listing' in params:
        videos = ast.literal_eval(params['previous_listing'])

    url = params.category_url + '&page=' + str(params.page)

    file_path = utils.download_catalog(
        url,
        '%s_%s_%s.html' % (
            params.channel_name,
            params.category_name,
            params.page))
    root_html = open(file_path).read()
    root_soup = bs(root_html, 'html.parser')

    if params.category_name == 'Politique':
        video_soup = root_soup.find_all(
            'article',
            class_="node node-episode node-episode-pse-search-result theme-4127 clearfix")
    elif params.category_name == 'Société':
        video_soup = root_soup.find_all(
            'article',
            class_="node node-episode node-episode-pse-search-result theme-4126 clearfix")
    elif params.category_name == 'Débat':
        video_soup = root_soup.find_all(
            'article',
            class_="node node-episode node-episode-pse-search-result theme-4128 clearfix")

    for video in video_soup:

        # Test Existing Video
        if video.find('div', class_="content").find( \
                'div', class_="right").find('div', class_="wrapper-duree"):

            title = ''
            if video.find('div', class_="content").find( \
                    'div',
                    class_="field field-name-title-field field-type-text field-label-hidden"):
                title = video.find(
                    'div',
                    class_="content"
                ).find(
                    'div',
                    class_="field field-name-field-ref-emission field-type-entityreference field-label-hidden"
                ).find(
                    'div',
                    class_="field-items"
                ).find(
                    'div',
                    class_="field-item even"
                ).get_text().encode('utf-8') + ' - ' \
                    + video.find(
                        'div',
                        class_="content"
                    ).find(
                        'div',
                        class_="field field-name-title-field field-type-text field-label-hidden"
                    ).find(
                        'div',
                        class_="field-items"
                    ).find(
                        'div',
                        class_="field-item even"
                    ).get_text().encode('utf-8')
            else:
                title = video.find(
                    'div',
                    class_="content"
                ).find(
                    'div',
                    class_="field field-name-field-ref-emission field-type-entityreference field-label-hidden"
                ).find(
                    'div',
                    class_="field-items"
                ).find(
                    'div',
                    class_="field-item even"
                ).get_text().encode('utf-8')

            img = ''
            if video.find('div', class_="content").find('div', class_="wrapper-visuel" \
                    ).find('div', class_="scald-atom video").find('div', \
                    class_="field field-name-scald-thumbnail field-type-image field-label-hidden"):
                img = video.find(
                    'div',
                    class_="content"
                ).find(
                    'div',
                    class_="wrapper-visuel"
                ).find(
                    'div',
                    class_="scald-atom video"
                ).find(
                    'div',
                    class_="field field-name-scald-thumbnail field-type-image field-label-hidden"
                ).find(
                    'div',
                    class_="field-items"
                ).find(
                    'div',
                    class_="field-item even"
                ).find('img').get('src')

            plot = ''
            if video.find('div', class_="content").find('div', \
                    class_="field field-name-field-contenu field-type-text-long field-label-hidden"):
                plot = video.find(
                    'div',
                    class_="content"
                ).find(
                    'div',
                    class_="field field-name-field-contenu field-type-text-long field-label-hidden"
                ).find(
                    'div',
                    class_="field-items"
                ).find(
                    'div',
                    class_="field-item even"
                ).get_text().encode('utf-8')


            value_date = video.find(
                'div',
                class_="content"
            ).find('div', class_="first-diffusion").get_text().encode('utf-8')
            date = value_date.split(' ')
            day = date[2]
            try:
                mounth = CORRECT_MONTH[date[3]]
            except:
                mounth = '00'
            year = date[4]

            date = '.'.join((day, mounth, year))
            aired = '-'.join((year, mounth, day))

            duration = 0
            duration = int(video.find('div', class_="content").find(
                'div', class_="right").find(
                    'div',
                    class_="wrapper-duree").get_text().encode('utf-8')[:-3]) * 60


            url_video = URL_ROOT + video.find(
                'div', class_="content").find('a').get('href').encode('utf-8')

            info = {
                'video': {
                    'title': title,
                    'aired': aired,
                    'date': date,
                    'duration': duration,
                    'year': year,
                    'plot' : plot,
                    'mediatype': 'tvshow'
                }
            }

            context_menu = []
            download_video = (
                _('Download'),
                'XBMC.RunPlugin(' + common.PLUGIN.get_url(
                    action='download_video',
                    url_video=url_video) + ')'
            )
            context_menu.append(download_video)

            videos.append({
                'label': title,
                'thumb': img,
                'fanart': img,
                'url': common.PLUGIN.get_url(
                    action='channel_entry',
                    next='play_r',
                    url_video=url_video
                ),
                'is_playable': True,
                'info': info,
                'context_menu': context_menu
            })

    # More videos...
    videos.append({
        'label': common.ADDON.get_localized_string(30100),
        'url': common.PLUGIN.get_url(
            action='channel_entry',
            category_url=params.category_url,
            category_name=params.category_name,
            next='list_videos_1',
            page=str(int(params.page) + 1),
            update_listing=True,
            previous_listing=str(videos)
        ),
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
    )

@common.PLUGIN.cached(common.CACHE_TIME)
def list_live(params):
    """Build live listing"""
    lives = []

    title = ''
    plot = ''
    duration = 0
    img = ''
    url_live = ''

    html_live = utils.get_webcontent(URL_LIVE_SITE)
    root_soup = bs(html_live, 'html.parser')
    live_soup = root_soup.find(
        'div',
        class_='iframe-responsive')

    url_live = live_soup.find('iframe').get('src')

    title = '%s Live' % params.channel_name.upper()

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
        'url' : common.PLUGIN.get_url(
            action='channel_entry',
            next='play_l',
            url=url_live,
        ),
        'is_playable': True,
        'info': info
    })

    return common.PLUGIN.create_listing(
        lives,
        sort_methods=(
            common.sp.xbmcplugin.SORT_METHOD_UNSORTED,
            common.sp.xbmcplugin.SORT_METHOD_LABEL
        )
    )

@common.PLUGIN.cached(common.CACHE_TIME)
def get_video_url(params):
    """Get video URL and start video player"""
    if params.next == 'play_r' or params.next == 'download_video':

        url = ''

        html_video = utils.get_webcontent(params.url_video)
        ur_video_soup = bs(html_video, 'html.parser')
        urlembeded_videos_soup = ur_video_soup.find_all('iframe')

        for url in urlembeded_videos_soup:
            url_video_embed = url.get('src').encode('utf-8')
            break # get first video hard to find by another method


        url_video_embed_http = url_video_embed
        if params.next == 'download_video':
            return url_video_embed_http
        html_video = utils.get_webcontent(url_video_embed_http)
        html_video = html_video.replace('\\', '')

        all_url_video = re.compile(r'"type":"video/mp4","url":"(.*?)"').findall(html_video)
        for datas in all_url_video:
            url = datas

        return url

    elif params.next == 'play_l':

        html_live = utils.get_webcontent(params.url)
        html_live = html_live.replace('\\', '')

        url_live = re.compile(
            r'{"type":"application/x-mpegURL","url":"(.*?)"}]}').findall(html_live)

        # Just one flux no quality to choose
        return url_live[0]
