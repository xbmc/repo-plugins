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

import json
import re
import xml.etree.ElementTree as ET
import requests
from bs4 import BeautifulSoup as bs
from resources.lib import utils
from resources.lib import common

# TO DO
# Get Info Live
# Get CATEGORIES

# Initialize GNU gettext emulation in addon
# This allows to use UI strings from addon’s English
# strings.po file instead of numeric codes
_ = common.ADDON.initialize_gettext()

URL_ROOT = 'http://www.nrj-play.fr'

URL_REPLAY = 'http://www.nrj-play.fr/%s/replay'
# channel_name (nrj12, ...)

URL_COLLECTION_API = 'http://www.nrj-play.fr/%s/api/getreplaytvcollection'
# channel_name (nrj12, ...)

URL_REPLAY_API = 'http://www.nrj-play.fr/%s/api/getreplaytvlist'
# channel_name (nrj12, ...) - HTTP 500 non stable

URL_ALL_VIDEO = 'http://www.nrj-play.fr/sitemap-videos.xml'
# Meilleur stabilité mais perte des collections

URL_GET_API_LIVE = 'http://www.nrj-play.fr/sitemap.xml'
# NOT_USED in this script (link api, live and more)

URL_COMPTE_LOGIN = 'https://www.nrj-play.fr/compte/login'
# TO DO add account for using Live Direct

URL_LIVE_WITH_TOKEN = 'http://www.nrj-play.fr/compte/live?channel=%s'
# channel (nrj12, ...) - call this url after get session (url live with token inside this page)

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
    else:
        return None


@common.PLUGIN.cached(common.CACHE_TIME)
def root(params):
    """Add Replay and Live in the listing"""
    modes = []

    # Add Replay with Categories
    modes.append({
        'label' : 'Replay',
        'url': common.PLUGIN.get_url(
            action='channel_entry',
            next='list_shows_1',
            category='%s Replay' % params.channel_name.upper(),
            window_title='%s Replay' % params.channel_name.upper()
        ),
    })

    # Add Replay
    modes.append({
        'label' : 'Replay sans categorie',
        'url': common.PLUGIN.get_url(
            action='channel_entry',
            next='list_shows_without_categories',
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

    if 'list_shows_without_categories' in params.next:

        # Pour avoir toutes les videos
        state_video = 'Toutes les videos (sans les categories)'

        shows.append({
            'label': state_video,
            'url': common.PLUGIN.get_url(
                action='channel_entry',
                state_video=state_video,
                next='list_videos_1',
                #title_category=category_name,
                window_title=state_video
            )
        })

    else:
        unique_item = dict()

        file_path = utils.download_catalog(
            URL_COLLECTION_API % params.channel_name,
            '%s_collection.xml' % params.channel_name,
        )
        collection_xml = open(file_path).read()

        xml_elements = ET.XML(collection_xml)

        if 'list_shows_1' in params.next:
            # Build categories list (Tous les programmes, Séries, ...)
            collections = xml_elements.findall("collection")

            # Pour avoir toutes les videos, certaines videos ont des
            # categories non presentes dans cette URL 'url_collection_api'
            state_video = 'Toutes les videos'

            shows.append({
                'label': state_video,
                'url': common.PLUGIN.get_url(
                    action='channel_entry',
                    state_video=state_video,
                    next='list_videos_1',
                    #title_category=category_name,
                    window_title=state_video
                )
            })

            for collection in collections:

                category_name = collection.findtext("category").encode('utf-8')
                if category_name not in unique_item:
                    if category_name == '':
                        category_name = 'NO_CATEGORY'
                    unique_item[category_name] = category_name
                    shows.append({
                        'label': category_name,
                        'url': common.PLUGIN.get_url(
                            action='channel_entry',
                            category_name=category_name,
                            next='list_shows_programs',
                            #title_category=category_name,
                            window_title=category_name
                        )
                    })

        elif 'list_shows_programs' in params.next:
            # Build programm list (Tous les programmes, Séries, ...)
            collections = xml_elements.findall("collection")

            state_video = 'VIDEOS_BY_CATEGORY'

            for collection in collections:
                if params.category_name == collection.findtext("category").encode('utf-8') \
                        or (params.category_name == 'NO_CATEGORY' and \
                        collection.findtext("category").encode('utf-8') == ''):
                    name_program = collection.findtext("name").encode('utf-8')
                    img_program = collection.findtext("picture")
                    id_program = collection.get("id")

                    shows.append({
                        'label': name_program,
                        'thumb': img_program,
                        'url': common.PLUGIN.get_url(
                            action='channel_entry',
                            next='list_videos_1',
                            state_video=state_video,
                            id_program=id_program,
                            #title_program=name_program,
                            window_title=name_program
                        )
                    })

    return common.PLUGIN.create_listing(
        shows,
        sort_methods=(
            common.sp.xbmcplugin.SORT_METHOD_UNSORTED,
            common.sp.xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE
        ),
    )

@common.PLUGIN.cached(common.CACHE_TIME)
def list_videos(params):
    """Build videos listing"""
    videos = []

    if params.state_video == 'Toutes les videos (sans les categories)':

        file_path = utils.download_catalog(
            URL_ALL_VIDEO,
            '%s_all_video.xml' % params.channel_name,
        )
        replay_xml = open(file_path).read()

        xml_elements = ET.XML(replay_xml)

        programs = xml_elements.findall("{http://www.sitemaps.org/schemas/sitemap/0.9}url")

        for program in programs:

            url_site = program.findtext(
                "{http://www.sitemaps.org/schemas/sitemap/0.9}loc").encode('utf-8')
            check_string = '%s/replay/' % params.channel_name
            if url_site.count(check_string) > 0:

                # Title
                title = url_site.rsplit('/', 1)[1].replace("-", " ").upper()

                video_node = program.findall(
                    "{http://www.google.com/schemas/sitemap-video/1.1}video")[0]

                # Duration
                duration = 0

                # Image
                img = ''
                img_node = video_node.find(
                    "{http://www.google.com/schemas/sitemap-video/1.1}thumbnail_loc")
                img = img_node.text.encode('utf-8')

                # Url Video
                url = ''
                url_node = video_node.find(
                    "{http://www.google.com/schemas/sitemap-video/1.1}content_loc")
                url = url_node.text.encode('utf-8')

                # Plot
                plot = ''
                plot_node = video_node.find(
                    "{http://www.google.com/schemas/sitemap-video/1.1}description")
                if plot_node.text:
                    plot = plot_node.text.encode('utf-8')

                # Date
                value_date = ''
                value_date_node = video_node.find(
                    "{http://www.google.com/schemas/sitemap-video/1.1}publication_date")
                value_date = value_date_node.text.encode('utf-8')
                date = value_date.split('T')[0].split('-')
                day = date[2]
                mounth = date[1]
                year = date[0]
                date = '.'.join((day, mounth, year))
                aired = '-'.join((year, mounth, day))

                info = {
                    'video': {
                        'title': title,
                        'plot': plot,
                        'duration': duration,
                        'aired': aired,
                        'date': date,
                        'year': year,
                        'mediatype': 'tvshow'
                    }
                }

                context_menu = []
                download_video = (
                    _('Download'),
                    'XBMC.RunPlugin(' + common.PLUGIN.get_url(
                        action='download_video',
                        url_video=url_site) + ')'
                )
                context_menu.append(download_video)

                videos.append({
                    'label': title,
                    'fanart': img,
                    'thumb': img,
                    'url': common.PLUGIN.get_url(
                        action='channel_entry',
                        next='play_r',
                        url_video=url
                    ),
                    'is_playable': True,
                    'info': info,
                    'context_menu': context_menu
                })

    else:
        file_path = utils.download_catalog(
            URL_REPLAY_API % params.channel_name,
            '%s_replay.xml' % params.channel_name,
        )
        replay_xml = open(file_path).read()

        xml_elements = ET.XML(replay_xml)

        programs = xml_elements.findall("program")

        for program in programs:
            if params.state_video == 'Toutes les videos':

                # Title
                title = program.findtext("title").encode('utf-8') + " - " + \
                    program.findtext("subtitle").encode('utf-8')

                # Duration
                duration = 0
                if program.findtext("duration"):
                    try:
                        duration = int(program.findtext("duration")) * 60
                    except ValueError:
                        pass      # or whatever

                # Image
                img = program.find("photos").findtext("photo")

                # Url Video
                url = '' #program.find("offres").find("offre").find("videos").findtext("video)
                for i in program.find("offres").findall("offre"):

                    date_value = i.get("startdate")
                    date_value_list = date_value.split(' ')[0].split('-')
                    day = date_value_list[2]
                    mounth = date_value_list[1]
                    year = date_value_list[0]

                    date = '.'.join((day, mounth, year))
                    aired = '-'.join((year, mounth, day))

                    for j in i.find("videos").findall("video"):
                        url = j.text.encode('utf-8')

                # Plot
                plot = ''
                for i in program.find("stories").findall("story"):
                    if int(i.get("maxlength")) == 680:
                        plot = i.text.encode('utf-8')

                info = {
                    'video': {
                        'title': title,
                        'plot': plot,
                        'duration': duration,
                        'aired': aired,
                        'date': date,
                        'year': year,
                        'mediatype': 'tvshow'
                    }
                }

                context_menu = []
                download_video = (
                    _('Download'),
                    'XBMC.RunPlugin(' + common.PLUGIN.get_url(
                        action='download_video',
                        url_video=url) + ')'
                )
                context_menu.append(download_video)

                videos.append({
                    'label': title,
                    'fanart': img,
                    'thumb': img,
                    'url': common.PLUGIN.get_url(
                        action='channel_entry',
                        next='play_r',
                        url_video=url
                    ),
                    'is_playable': True,
                    'info': info,
                    'context_menu': context_menu
                })

            elif params.id_program == program.get("IDSERIE"):

                # Title
                title = program.findtext("title").encode('utf-8') + " - " + \
                    program.findtext("subtitle").encode('utf-8')

                # Duration
                duration = 0
                if program.findtext("duration"):
                    try:
                        duration = int(program.findtext("duration")) * 60
                    except ValueError:
                        pass      # or whatever

                # Image
                img = program.find("photos").findtext("photo")

                # Url Video
                url = '' #program.find("offres").find("offre").find("videos").findtext("video)
                for i in program.find("offres").findall("offre"):

                    date_value = i.get("startdate")
                    date_value_list = date_value.split(' ')[0].split('-')
                    day = date_value_list[2]
                    mounth = date_value_list[1]
                    year = date_value_list[0]

                    date = '.'.join((day, mounth, year))
                    aired = '-'.join((year, mounth, day))

                    for j in i.find("videos").findall("video"):
                        url = j.text.encode('utf-8')

                # Plot
                plot = ''
                for i in program.find("stories").findall("story"):
                    if int(i.get("maxlength")) == 680:
                        plot = i.text.encode('utf-8')

                info = {
                    'video': {
                        'title': title,
                        'plot': plot,
                        'duration': duration,
                        'aired': aired,
                        'date': date,
                        'year': year,
                        'mediatype': 'tvshow'
                    }
                }

                context_menu = []
                download_video = (
                    _('Download'),
                    'XBMC.RunPlugin(' + common.PLUGIN.get_url(
                        action='download_video',
                        url_video=url) + ')'
                )
                context_menu.append(download_video)

                videos.append({
                    'label': title,
                    'fanart': img,
                    'thumb': img,
                    'url': common.PLUGIN.get_url(
                        action='channel_entry',
                        next='play_r',
                        url_video=url
                    ),
                    'is_playable': True,
                    'info': info
                    # 'context_menu': context_menu
                })

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
        content='tvshows')

@common.PLUGIN.cached(common.CACHE_TIME)
def list_live(params):
    """Build live listing"""
    lives = []

    title = ''
    plot = ''
    duration = 0
    img = ''
    url_live = ''

    session_requests = requests.session()
    result = session_requests.get(URL_COMPTE_LOGIN)

    token_form_login = re.compile(
        r'name=\"login_form\[_token\]\" value=\"(.*?)\"').findall(result.text)[0]

    # Build PAYLOAD
    payload = {
        "login_form[email]": common.PLUGIN.get_setting(
            params.channel_id.rsplit('.', 1)[0] + '.login'),
        "login_form[password]": common.PLUGIN.get_setting(
            params.channel_id.rsplit('.', 1)[0] + '.password'),
        "login_form[_token]": token_form_login
    }

    # LOGIN
    result_2 = session_requests.post(
        URL_COMPTE_LOGIN, data = payload, headers = dict(referer = URL_COMPTE_LOGIN))

    # GET page with url_live with the session logged
    result_3 = session_requests.get(
        URL_LIVE_WITH_TOKEN % (params.channel_name),
        headers=dict(
            referer=URL_LIVE_WITH_TOKEN % (params.channel_name)))

    root_soup = bs(result_3.text, 'html.parser')
    live_soup = root_soup.find('div', class_="player")

    url_live_json = live_soup.get('data-options')
    url_live_json_jsonparser = json.loads(url_live_json)

    url_live = url_live_json_jsonparser["file"]

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
            url_live=url_live,
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
        # Just One format of each video (no need of QUALITY)
        return params.url_video
    elif params.next == 'play_l':
        return params.url_live
