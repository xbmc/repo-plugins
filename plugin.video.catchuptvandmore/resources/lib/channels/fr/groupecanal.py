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


# TO DO
# Replay (More Refactoring todo) / Find API for all channel (JSON) get Replay/Live ?
# Get URL Live FROM SITE
# QUALITY
# Add Button "More Videos"

# URL :

URL_ROOT_SITE = 'http://www.%s.fr'
# Channel

# Live :
URL_LIVE_CPLUS = 'http://www.canalplus.fr/pid3580-live-tv-clair.html'
URL_LIVE_C8 = 'http://www.c8.fr/pid5323-c8-live.html'
URL_LIVE_CSTAR = 'http://www.cstar.fr/pid5322-cstar-live.html'
URL_LIVE_CNEWS = 'http://www.cnews.fr/direct'

# Replay Cplus :
URL_ROOT_CPLUS = 'http://www.canalplus.fr'

URL_LIST_EMISSIONS_CPLUS = 'http://www.canalplus.fr/pid8034-les-emissions-de-canal.html'

# Replay C8 & CStar
URL_REPLAY_C8__CSTAR_ROOT = 'http://lab.canal-plus.pro/web/app_prod.php/api/replay/%s'
# Channel id :
# c8 : 1
# cstar : 2
URL_REPLAY_C8__CSTAR_SHOWS = 'http://lab.canal-plus.pro/web/app_prod.php/api/pfv/list/%s/%s'
# channel_id/show_id

# Replay CNews
URL_VIDEOS_CNEWS = URL_ROOT_SITE + '/videos/'

URL_EMISSIONS_CNEWS = URL_ROOT_SITE + '/emissions'

# Replay/Live => Parameters Channel, VideoId
URL_INFO_CONTENT = 'http://service.canal-plus.com/video/rest/getvideos/%s/%s?format=json'

CHANNEL_NAME_CATALOG = {
    'cplus': 'cplus',
    'c8': 'd8',
    'cstar': 'd17',
    'cnews': 'itele'
}

# Initialize GNU gettext emulation in addon
# This allows to use UI strings from addon’s English
# strings.po file instead of numeric codes
_ = common.ADDON.initialize_gettext()

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
    return None

def get_token():
    """Get session token"""
    token_json = utils.get_webcontent(URL_REPLAY_CPLUS_AUTH)
    token_json = json.loads(token_json)
    token = token_json['token']
    return token

@common.PLUGIN.cached(common.CACHE_TIME)
def get_channel_id(params):
    """Get channel id by name"""
    if params.channel_name == 'c8':
        return '1'
    elif params.channel_name == 'cstar':
        return '2'

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
        'label' : _('Live TV'),
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
    """Create categories list"""
    shows = []

    ################### BEGIN CNEWS ###########################
    if params.next == 'list_shows_1' and params.channel_name == 'cnews':

        file_path = utils.download_catalog(
            URL_VIDEOS_CNEWS % params.channel_name,
            '%s_categories.html' % (
                params.channel_name))
        root_html = open(file_path).read()
        root_soup = bs(root_html, 'html.parser')

        menu_soup = root_soup.find('div', class_="nav-tabs-inner")

        categories_soup = menu_soup.find_all('a')

        for category in categories_soup:

            category_name = category.get_text().encode('utf-8')
            category_url = (URL_ROOT_SITE % params.channel_name) + category.get('href')

            if category_name != 'Les tops':
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

    elif params.next == 'list_shows_2' and params.channel_name == 'cnews':

        if params.category_name == 'Les sujets':

            file_path = utils.download_catalog(
                params.category_url,
                '%s_%s.html' % (
                    params.channel_name,params.category_name))
            root_html = open(file_path).read()
            root_soup = bs(root_html, 'html.parser')
            categories_soup = root_soup.find_all('a', class_="checkbox")

            for category in categories_soup:

                category_name = category.get_text().encode('utf-8')
                category_url = (URL_ROOT_SITE % params.channel_name) + category.get('href')

                shows.append({
                    'label': category_name,
                    'url': common.PLUGIN.get_url(
                        action='channel_entry',
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
                (URL_EMISSIONS_CNEWS % params.channel_name),
                '%s_ALL_EMISSION.html' % (
                    params.channel_name))
            root_html = open(file_path).read()
            root_soup = bs(root_html, 'html.parser')

            categories_soup = root_soup.find_all('article', class_="item")

            for category in categories_soup:

                category_name = category.find('h3').get_text().encode('utf-8')
                category_url = (URL_VIDEOS_CNEWS % params.channel_name) + '/emissions' + category.find('a').get('href').split('.fr')[1]
                category_img = category.find('img').get('src').encode('utf-8')

                shows.append({
                    'label': category_name,
                    'thumb': category_img,
                    'fanart': category_img,
                    'url': common.PLUGIN.get_url(
                        action='channel_entry',
                        category_url=category_url,
                        page="1",
                        category_name=category_name,
                        next='list_videos',
                        window_title=category_name
                    )
                })


    ################### END CNEWS ###########################

    ################### BEGIN C8 and CStar ##################
    elif params.next == 'list_shows_1' and (params.channel_name == 'c8' or \
            params.channel_name == 'cstar'):
        file_path = utils.download_catalog(
            URL_REPLAY_C8__CSTAR_ROOT % get_channel_id(params),
            '%s.json' % (params.channel_name))
        file_categories = open(file_path).read()
        json_categories = json.loads(file_categories)

        for categories in json_categories:
            title = categories['title'].encode('utf-8')
            slug = categories['slug'].encode('utf-8')

            shows.append({
                'label': title,
                'url': common.PLUGIN.get_url(
                    action='channel_entry',
                    slug=slug,
                    next='list_shows_2',
                    title=title,
                    window_title=title
                )
            })

    elif params.next == 'list_shows_2' and (params.channel_name == 'c8' or \
            params.channel_name == 'cstar'):
        # Create category's programs list
        file_path = utils.download_catalog(
            URL_REPLAY_C8__CSTAR_ROOT % get_channel_id(params),
            '%s_%s.json' % (params.channel_name, params.slug))
        file_categories = open(file_path).read()
        json_categories = json.loads(file_categories)

        for categories in json_categories:
            if categories['slug'].encode('utf-8') == params.slug:
                for programs in categories['programs']:
                    id = str(programs['id'])
                    title = programs['title'].encode('utf-8')
                    slug = programs['slug'].encode('utf-8')
                    videos_recent = str(programs['videos_recent'])

                    shows.append({
                        'label': title,
                        'url': common.PLUGIN.get_url(
                            action='channel_entry',
                            next='list_videos_cat',
                            id=id,
                            videos_recent=videos_recent,
                            slug=slug,
                            title=title,
                            window_title=title
                        )
                    })
    ################### END C8 and CStar ##################

    ################### BEGIN CANAL + ##################
    elif params.next == 'list_shows_1' and params.channel_name == 'cplus':

        file_path = utils.download_catalog(
            URL_LIST_EMISSIONS_CPLUS,
            '%s_categories.html' % (
                params.channel_name))
        root_html = open(file_path).read()
        root_soup = bs(root_html, 'html.parser')

        categories_soup = root_soup.find_all('div', class_='cell')

        for category in categories_soup:

            category_name = category.find('h6').get_text().encode('utf-8')
            category_url = URL_ROOT_CPLUS + category.find('a').get('href')
            category_img = category.find('img').get('src').encode('utf-8')

            if category_name != 'Les tops':
                shows.append({
                    'label': category_name,
                    'thumb': category_img,
                    'fanart': category_img,
                    'url': common.PLUGIN.get_url(
                        action='channel_entry',
                        category_url=category_url,
                        category_name=category_name,
                        next='list_shows_2',
                        window_title=category_name
                    )
                })

    elif params.next == 'list_shows_2' and params.channel_name == 'cplus':

        file_path = utils.download_catalog(
            params.category_url,
            '%s_%s.html' % (
                params.channel_name,params.category_name))
        root_html = open(file_path).read()
        root_soup = bs(root_html, 'html.parser')

        sections_soup = root_soup.find('div', class_="listeRegroupee")

        list_section = sections_soup.find_all('h2')
        for section in list_section:
            section = section.get_text().encode('utf-8')

            shows.append({
                'label': section,
                'url': common.PLUGIN.get_url(
                    action='channel_entry',
                    category_url=params.category_url,
                    category_name=params.category_name,
                    category_section=section,
                    next='list_videos',
                    window_title=section
                )
            })

    ################### END CANAL + ##################

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

    ################### BEGIN CNEWS ###########################
    if params.channel_name == 'cnews':

        url_page = params.category_url + '/page/%s' % params.page

        file_path = utils.download_catalog(
            url_page,
            '%s_%s_%s.html' % (params.channel_name, params.category_name, params.page))
        root_html = open(file_path).read()
        root_soup = bs(root_html, 'html.parser')

        programs = root_soup.find_all('article', class_='item')

        for program in programs:
            title = program.find('h3').get_text().encode('utf-8')
            thumb = program.find('img').get('src').encode('utf-8')
            #Get Video_ID
            video_html = utils.get_webcontent(program.find('a').get('href').encode('utf-8'))
            id = re.compile(r'videoId=(.*?)"').findall(video_html)[0]
            #Get Description
            datas_video = bs(video_html, 'html.parser')
            description = datas_video.find('article', class_='entry-body').get_text().encode('utf-8')
            duration = 0

            date = re.compile(r'property="video:release_date" content="(.*?)"').findall(video_html)[0].split('T')[0].split('-')
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
                    #'genre': category,
                    'mediatype': 'tvshow'
                }
            }

            context_menu = []
            download_video = (
                 _('Download'),
                'XBMC.RunPlugin(' + common.PLUGIN.get_url(
                    action='download_video',
                    id=id) + ')'
            )
            context_menu.append(download_video)

            videos.append({
                'label': title,
                'thumb': thumb,
                'fanart': thumb,
                'url': common.PLUGIN.get_url(
                    action='channel_entry',
                    next='play_r',
                    id=id
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
                next='list_videos',
                page=str(int(params.page) + 1),
                update_listing=True,
                previous_listing=str(videos)
            ),
        })
    ################### END CNEWS ###########################

    ################### BEGIN C8 and CStar ##################
    elif params.channel_name == 'c8' or params.channel_name == 'cstar':
        file_path = utils.download_catalog(
            URL_REPLAY_C8__CSTAR_SHOWS % (get_channel_id(params), params.videos_recent),
            '%s_%s.json' % (params.channel_name, params.videos_recent))
        file_videos = open(file_path).read()
        videos_json = json.loads(file_videos)

        for video in videos_json:
            id = video['ID'].encode('utf-8')
            try:
                duration = int(video['DURATION'].encode('utf-8'))
            except:
                duration = 0
            description = video['INFOS']['DESCRIPTION'].encode('utf-8')
            views = int(video['INFOS']['NB_VUES'].encode('utf-8'))
            try:
                date_video = video['INFOS']['DIFFUSION']['DATE'].encode('utf-8')  # 31/12/2017
            except:
                date_video = "00/00/0000"
            day = date_video.split('/')[0]
            mounth = date_video.split('/')[1]
            year = date_video.split('/')[2]
            aired = '-'.join((day, mounth, year))
            date = date_video.replace('/', '.')
            title = video['INFOS']['TITRAGE']['TITRE'].encode('utf-8')
            subtitle = video['INFOS']['TITRAGE']['SOUS_TITRE'].encode('utf-8')
            thumb = video['MEDIA']['IMAGES']['GRAND'].encode('utf-8')
            category = video['RUBRIQUAGE']['CATEGORIE'].encode('utf-8')

            if subtitle:
                title = title + ' - [I]' + subtitle + '[/I]'

            info = {
                'video': {
                    'title': title,
                    'plot': description,
                    'aired': aired,
                    'date': date,
                    'duration': duration,
                    'year': year,
                    'genre': category,
                    'playcount': views,
                    'mediatype': 'tvshow'
                }
            }

            context_menu = []
            download_video = (
                _('Download'),
                'XBMC.RunPlugin(' + common.PLUGIN.get_url(
                    action='download_video',
                    id=id) + ')'
            )
            context_menu.append(download_video)

            videos.append({
                'label': title,
                'thumb': thumb,
                'url': common.PLUGIN.get_url(
                    action='channel_entry',
                    next='play_r',
                    id=id,
                ),
                'is_playable': True,
                'info': info,
                'context_menu': context_menu
            })
    ################### END C8 and CStar ##################

    ################### BEGIN Canal + ##################
    elif params.channel_name == 'cplus':

        file_path = utils.download_catalog(
            params.category_url,
            '%s_%s_%s.html' % (params.channel_name, params.category_name, params.category_section))
        root_html = open(file_path).read()
        root_soup = bs(root_html, 'html.parser')

        sections_soup = root_soup.find('div', class_="listeRegroupee")

        i = 0
        j = 0
        list_sections = sections_soup.find_all('h2')
        for section in list_sections:
            i = i + 1
            if section.get_text().encode('utf-8') == params.category_section:
                break

        videos_sections_soup = sections_soup.find_all('ul', class_="features features-alt features-alt-videov3-4x3 features-alt-videov3-4x3-noMarge")
        for videos_section in videos_sections_soup:
            j = j + 1
            if i == j:
                data_videos = videos_section.find_all('li')

                for data_video in data_videos:

                    title = data_video.find('h4').get('title').encode('utf-8')
                    description = data_video.find('p').find('a').get_text().strip().encode('utf-8')
                    duration = 0
                    thumb = data_video.find('img').get('src').encode('utf-8')
                    id = data_video.get('id').split('_')[1]

                    info = {
                        'video': {
                            'title': title,
                            'plot': description,
                            #'aired': aired,
                            #'date': date,
                            'duration': duration,
                            #'year': year,
                            #'genre': category,
                            'mediatype': 'tvshow'
                        }
                    }

                    context_menu = []
                    download_video = (
                         _('Download'),
                        'XBMC.RunPlugin(' + common.PLUGIN.get_url(
                            action='download_video',
                            id=id) + ')'
                    )
                    context_menu.append(download_video)

                    videos.append({
                        'label': title,
                        'thumb': thumb,
                        'fanart': thumb,
                        'url': common.PLUGIN.get_url(
                            action='channel_entry',
                            next='play_r',
                            id=id
                        ),
                        'is_playable': True,
                        'info': info,
                        'context_menu': context_menu
                    })

    ################### END Canal + ##################

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

    url_live_html = ''
    if params.channel_name == 'cplus':
        url_live_html = URL_LIVE_CPLUS
    elif params.channel_name == 'c8':
        url_live_html = URL_LIVE_C8
    elif params.channel_name == 'cstar':
        url_live_html = URL_LIVE_CSTAR
    elif params.channel_name == 'cnews':
        url_live_html = URL_LIVE_CNEWS

    file_path_html = utils.download_catalog(
        url_live_html,
        '%s_live.html' % (params.channel_name)
    )
    html_live = open(file_path_html).read()

    video_id_re = ''

    if params.channel_name == 'cnews':
        video_id_re = re.compile(r'content: \'(.*?)\'').findall(html_live)
    else :
        video_id_re = re.compile(r'\bdata-video="(?P<video_id>[0-9]+)"').findall(html_live)

    file_path_json = utils.download_catalog(
        URL_INFO_CONTENT % (CHANNEL_NAME_CATALOG[params.channel_name], video_id_re[0]),
        '%s_%s_live.json' % (CHANNEL_NAME_CATALOG[params.channel_name], video_id_re[0])
    )
    file_live_json = open(file_path_json).read()
    json_parser = json.loads(file_live_json)

    title = json_parser["INFOS"]["TITRAGE"]["TITRE"].encode('utf-8')
    plot = json_parser["INFOS"]["DESCRIPTION"].encode('utf-8')
    img = json_parser["MEDIA"]["IMAGES"]["GRAND"].encode('utf-8')
    url_live = json_parser["MEDIA"]["VIDEOS"]["IPAD"].encode('utf-8')

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
        file_video = utils.get_webcontent(
            URL_INFO_CONTENT % (CHANNEL_NAME_CATALOG[params.channel_name],params.id)
        )
        media_json = json.loads(file_video)
        return media_json['MEDIA']['VIDEOS']['HLS'].encode('utf-8')
    # Live CPlus, C8, CStar and CNews
    elif params.next == 'play_l':
        return params.url
