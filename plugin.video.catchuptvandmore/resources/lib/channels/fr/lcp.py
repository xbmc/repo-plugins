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
import json
from bs4 import BeautifulSoup as bs
from resources.lib import utils
from resources.lib import common

# TO DO
# Use some API to simplify
# Add info LIVE TV

# LCP contient deux sources de video pour les replays
# New : play1.qbrick.com
# Old : www.dailymotion.com

# Initialize GNU gettext emulation in addon
# This allows to use UI strings from addon’s English
# strings.po file instead of numeric codes
_ = common.ADDON.initialize_gettext()

URL_ROOT = 'http://www.lcp.fr'

URL_LIVE_SITE = 'http://www.lcp.fr/le-direct'

URL_DAILYMOTION_EMBED = 'http://www.dailymotion.com/embed/video/%s'

URL_VIDEO_REPLAY = 'http://play1.qbrick.com/config/avp/v1/player/' \
                   'media/%s/darkmatter/%s/'
# VideoID, AccountId


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
    'http://www.lcp.fr/actualites': 'Actualités',
    'http://www.lcp.fr/emissions': 'Émissions',
    'http://www.lcp.fr/documentaires': 'Documentaires'
}

CORRECT_MOUNTH = {
    'janvier': '01',
    'février': '02',
    'mars': '03',
    'avril': '04',
    'mai': '05',
    'juin': '06',
    'juillet': '07',
    'août': '08',
    'septembre': '09',
    'octobre': '10',
    'novembre': '11',
    'décembre': '12'
}


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def root(params):
    """Add Replay and Live in the listing"""
    modes = []

    # Add Replay Desactiver
    modes.append({
        'label': 'Replay',
        'url': common.PLUGIN.get_url(
            action='channel_entry',
            next='list_shows_1',
            category='%s Replay' % params.channel_name.upper(),
            window_title='%s Replay' % params.channel_name.upper()
        ),
    })

    # Add Live
    modes.append({
        'label': 'Live TV',
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


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def list_shows(params):
    """Build shows listing"""
    shows = []

    if params.next == 'list_shows_1':

        for category_url, category_name in CATEGORIES.iteritems():

            if category_name == 'Émissions':
                shows.append({
                    'label': category_name,
                    'url': common.PLUGIN.get_url(
                        action='channel_entry',
                        category_url=category_url,
                        category_name=category_name,
                        next='list_shows_2',
                        window_title=category_name
                    )
                })
            elif category_name == 'Actualités':
                shows.append({
                    'label': category_name,
                    'url': common.PLUGIN.get_url(
                        action='channel_entry',
                        actualites_url=category_url,
                        actualites_name=category_name,
                        page='0',
                        next='list_videos_actualites',
                        window_title=category_name
                    )
                })
            elif category_name == 'Documentaires':
                shows.append({
                    'label': category_name,
                    'url': common.PLUGIN.get_url(
                        action='channel_entry',
                        documentaires_url=category_url,
                        documentaires_name=category_name,
                        page='0',
                        next='list_videos_documentaires',
                        window_title=category_name
                    )
                })

    elif params.next == 'list_shows_2':

        file_path = utils.download_catalog(
            params.category_url,
            '%s_%s.html' % (
                params.channel_name,
                params.category_name))
        root_html = open(file_path).read()
        root_soup = bs(root_html, 'html.parser')

        emissions_soup = root_soup.find_all('div', class_='content')

        for emission in emissions_soup:

            emission_name = emission.find('h2').get_text().encode('utf-8')
            emission_img = emission.find('img')['src'].encode('utf-8')
            emission_url = URL_ROOT + emission.find(
                'a')['href'].encode('utf-8')

            shows.append({
                'label': emission_name,
                'thumb': emission_img,
                'url': common.PLUGIN.get_url(
                    action='channel_entry',
                    emission_url=emission_url,
                    emission_name=emission_name,
                    page='0',
                    next='list_videos_emissions',
                    window_title=emission_name
                )
            })

    return common.PLUGIN.create_listing(
        shows,
        sort_methods=(
            common.sp.xbmcplugin.SORT_METHOD_UNSORTED,
            common.sp.xbmcplugin.SORT_METHOD_LABEL
        )
    )


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def list_videos(params):
    """Build videos listing"""
    videos = []

    if 'previous_listing' in params:
        videos = ast.literal_eval(params['previous_listing'])

    if params.next == 'list_videos_documentaires':

        if params.page == 0:
            url = params.documentaires_url
        else:
            url = params.documentaires_url + '?page=' + str(params.page)

        file_path = utils.download_catalog(
            url,
            '%s_%s_%s.html' % (
                params.channel_name,
                params.documentaires_name,
                params.page))
        root_html = open(file_path).read()
        root_soup = bs(root_html, 'html.parser')

        video_soup = root_soup.find_all(
            'div', class_="node node-lcp-tv-episode node-teaser clearfix")

        for video in video_soup:

            title = video.find('h2').find('a').get_text().encode('utf-8')
            value_date = video.find(
                'div', class_="content").find(
                    'span', class_="date").get_text().encode('utf-8')
            date = value_date.split(' ')
            day = date[0]
            try:
                mounth = CORRECT_MOUNTH[date[1]]
            except Exception:
                mounth = '00'
            year = date[2]

            date = '.'.join((day, mounth, year))
            aired = '-'.join((year, mounth, day))
            duration = 0
            duration = int(
                video.find(
                    'div', class_="content").find(
                        'div', class_="duration").find(
                            'div').find('span').get_text()) * 60
            img = video.find('a').find('img')['src'].encode('utf-8')
            url_video = URL_ROOT + video['about'].encode('utf-8')

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

            # Nouveau pour ajouter le menu pour télécharger la vidéo
            context_menu = []
            download_video = (
                _('Download'),
                'XBMC.RunPlugin(' + common.PLUGIN.get_url(
                    action='download_video',
                    url_video=url_video) + ')'
            )
            context_menu.append(download_video)
            # Fin

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
                documentaires_url=params.documentaires_url,
                documentaires_name=params.documentaires_name,
                next='list_videos_documentaires',
                page=str(int(params.page) + 1),
                update_listing=True,
                previous_listing=str(videos)
            ),
        })

    elif params.next == 'list_videos_actualites':

        if params.page == 0:
            url = params.actualites_url
        else:
            url = params.actualites_url + '?page=' + str(params.page)

        file_path = utils.download_catalog(
            url,
            '%s_%s_%s.html' % (
                params.channel_name,
                params.actualites_name,
                params.page))
        root_html = open(file_path).read()
        root_soup = bs(root_html, 'html.parser')

        video_soup = root_soup.find_all(
            'div',
            class_="node node-lcp-reportage "
                   "node-promoted node-teaser actu-teaser clearfix")

        for video in video_soup:

            title = video.find('h2').find('a').get_text().encode('utf-8')
            aired = video.find(
                'div', class_="content").find(
                    'div', class_="field field_submitted").get_text()
            date = ''
            duration = 0
            year = int(aired.split('/', -1)[2])
            img = video.find('a').find('img')['src'].encode('utf-8')

            url_video = URL_ROOT + video['about'].encode('utf-8')

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

            # Nouveau pour ajouter le menu pour télécharger la vidéo
            context_menu = []
            download_video = (
                _('Download'),
                'XBMC.RunPlugin(' + common.PLUGIN.get_url(
                    action='download_video',
                    url_video=url_video) + ')'
            )
            context_menu.append(download_video)
            # Fin

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
                actualites_url=params.actualites_url,
                actualites_name=params.actualites_name,
                next='list_videos_actualites',
                page=str(int(params.page) + 1),
                update_listing=True,
                previous_listing=str(videos)
            ),
        })

    elif params.next == 'list_videos_emissions':

        # Cas emission (2 cas) (-0) ou (sans -0)
        # 1ère page http://www.lcp.fr/emissions/evenements/replay-0
            # (url départ => http://www.lcp.fr/emissions/evenements-0)
        # 1ère page http://www.lcp.fr/emissions/evenements/replay-0?page=1
        # ainsi de suite
        # 1ère page : http://www.lcp.fr/emissions/en-voiture-citoyens/replay
            # (url départ => http://www.lcp.fr/emissions/en-voiture-citoyens)
        # 2ème page :
            # http://www.lcp.fr/emissions/en-voiture-citoyens/replay?page=1
        # ainsi de suite

        if params.page == 0 and '-0' not in params.emission_url:
            url = params.emission_url + '/replay'
        elif params.page > 0 and '-0' not in params.emission_url:
            url = params.emission_url + '/replay?page=' + str(params.page)
        elif params.page == 0 and '-0' in params.emission_url:
            url = params.emission_url[:-2] + '/replay-0'
        elif params.page > 0 and '-0' in params.emission_url:
            url = params.emission_url[:-2] + \
                '/replay-0?page=' + str(params.page)

        file_path = utils.download_catalog(
            url,
            '%s_%s_%s.html' % (
                params.channel_name,
                params.emission_name,
                params.page))
        root_html = open(file_path).read()
        root_soup = bs(root_html, 'html.parser')

        video_soup = root_soup.find_all(
            'div', class_="node node-lcp-tv-episode node-teaser clearfix")

        for video in video_soup:

            title = video.find(
                'h2').find('a').get_text().encode(
                    'utf-8') + ' - ' + video.find(
                        'h4').find('a').get_text().encode('utf-8')
            value_date = video.find(
                'div', class_="content").find(
                    'span', class_="date").get_text().encode('utf-8')
            date = value_date.split(' ')
            day = date[0]
            try:
                mounth = CORRECT_MOUNTH[date[1]]
            except Exception:
                mounth = '00'
            year = date[2]

            date = '.'.join((day, mounth, year))
            aired = '-'.join((year, mounth, day))
            duration = 0
            duration = int(video.find('div', class_="content").find(
                'div', class_="duration").find(
                    'div').find('span').get_text()) * 60
            img = video.find('a').find('img')['src'].encode('utf-8')

            url_video = URL_ROOT + video['about'].encode('utf-8')

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

            # Nouveau pour ajouter le menu pour télécharger la vidéo
            context_menu = []
            download_video = (
                _('Download'),
                'XBMC.RunPlugin(' + common.PLUGIN.get_url(
                    action='download_video',
                    url_video=url_video) + ')'
            )
            context_menu.append(download_video)
            # Fin

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
                emission_url=params.emission_url,
                emission_name=params.emission_name,
                next='list_videos_emissions',
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


@common.PLUGIN.mem_cached(common.CACHE_TIME)
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
        'iframe',
        class_='embed-responsive-item')

    url_live_embeded = live_soup.get('src')
    url_live = 'http:%s' % url_live_embeded

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
        'url': common.PLUGIN.get_url(
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


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def get_video_url(params):
    """Get video URL and start video player"""
    if params.next == 'play_r' or params.next == 'download_video':

        url = ''

        html_video = utils.get_webcontent(params.url_video)
        url_video_embed = re.compile(
            r'<iframe src="(.*?)"').findall(html_video)[0]

        if 'dailymotion' in url_video_embed:

            url_video_embed_http = 'http:%s' % url_video_embed
            if params.next == 'download_video':
                return url_video_embed_http
            html_video = utils.get_webcontent(url_video_embed_http)
            html_video = html_video.replace('\\', '')

            all_url_video = re.compile(
                r'"type":"video/mp4","url":"(.*?)"').findall(html_video)
            for datas in all_url_video:
                url = datas
        else:
            # get videoId and accountId
            videoId, accountId = re.compile(
                r'embed/(.*?)/(.*?)/').findall(url_video_embed)[0]

            html_json = utils.get_webcontent(
                URL_VIDEO_REPLAY % (videoId, accountId))

            html_json_2 = re.compile(r'\((.*?)\);').findall(html_json)[0]
            json_parser = json.loads(html_json_2)

            for playlist in json_parser['Playlist']:
                datas_video = playlist['MediaFiles']['M3u8']
                for data in datas_video:
                    url = data['Url']

        return url

    elif params.next == 'play_l':

        html_live = utils.get_webcontent(params.url)
        html_live = html_live.replace('\\', '')

        url_live = re.compile(
            r'{"type":"application/x-mpegURL","url":"(.*?)"}]}'
        ).findall(html_live)

        # Just one flux no quality to choose
        return url_live[0]
