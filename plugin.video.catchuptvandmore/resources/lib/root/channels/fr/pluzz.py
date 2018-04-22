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

import ast
import json
import re
import time
from bs4 import BeautifulSoup as bs
from resources.lib import utils
from resources.lib import resolver
from resources.lib import common


CHANNEL_CATALOG = 'http://pluzz.webservices.francetelevisions.fr/' \
                  'pluzz/liste/type/replay/nb/10000/chaine/%s'

CHANNEL_LIVE = 'http://pluzz.webservices.francetelevisions.fr/' \
               'pluzz/liste/type/live/nb/10000/chaine/%s'

# CHANNEL_CATALOG = 'https://pluzz.webservices.francetelevisions.fr/' \
#                   'mobile/liste/type/replay/chaine/%s/nb/20/debut/%s'
# page inc: 20

SHOW_INFO = 'http://webservices.francetelevisions.fr/tools/' \
            'getInfosOeuvre/v2/?idDiffusion=%s'

LIVE_INFO = 'http://webservices.francetelevisions.fr/tools/' \
            'getInfosOeuvre/v2/?idDiffusion=SIM_%s'

HDFAUTH_URL = 'http://hdfauth.francetv.fr/esi/TA?format=json&url=%s'

URL_IMG = 'http://refonte.webservices.francetelevisions.fr%s'

URL_SEARCH = 'https://pluzz.webservices.francetelevisions.fr/' \
             'mobile/recherche/nb/20/tri/date/requete/%s/debut/%s'

URL_ALPHA = 'https://pluzz.webservices.francetelevisions.fr/' \
            'mobile/liste/type/replay/tri/alpha/sens/%s/nb/100/' \
            'debut/%s/lastof/1'
# sens: asc or desc
# page inc: 100

URL_ROOT_SPORT = 'https://sport.francetvinfo.fr'

URL_FRANCETV_SPORT = 'https://api-sport-events.webservices.' \
                     'francetelevisions.fr/%s'
# RootMode

URL_ROOT_NOUVELLES_ECRITURES = 'http://%s.nouvelles-ecritures.francetv.fr'
# channel name

URL_ROOT_EDUCATION = 'http://education.francetv.fr'

URL_VIDEO_DATA_EDUCTATION = URL_ROOT_EDUCATION + '/video/%s/sisters'
# TitleVideo

URL_SERIE_DATA_EDUCTION = URL_ROOT_EDUCATION + '/programme/%s/section?page=%s'
# TitleSerie, page

CATEGORIES_DISPLAY = {
    "france2": "France 2",
    "france3": "France 3",
    "france4": "France 4",
    "france5": "France 5",
    "franceo": "France Ô",
    "guadeloupe": "Guadeloupe 1ère",
    "guyane": "Guyane 1ère",
    "martinique": "Martinique 1ère",
    "mayotte": "Mayotte 1ère",
    "nouvellecaledonie": "Nouvelle Calédonie 1ère",
    "polynesie": "Polynésie 1ère",
    "reunion": "Réunion 1ère",
    "saintpierremiquelon": "St-Pierre et Miquelon 1ère",
    "wallisfutuna": "Wallis et Futuna 1ère",
    "sport": "Sport",
    "info": "Info",
    "documentaire": "Documentaire",
    "seriefiction": "Série & fiction",
    "magazine": "Magazine",
    "jeunesse": "Jeunesse",
    "divertissement": "Divertissement",
    "jeu": "Jeu",
    "culture": "Culture"
}

LIVE_LA_1ERE = {
    "Guadeloupe 1ère": "guadeloupe",
    "Guyane 1ère": "guyane",
    "Martinique 1ère": "martinique",
    "Mayotte 1ère": "mayotte",
    "Nouvelle Calédonie 1ère": "nouvellecaledonie",
    "Polynésie 1ère": "polynesie",
    "Réunion 1ère": "reunion",
    "St-Pierre et Miquelon 1ère": "spm",
    "Wallis et Futuna 1ère": "wallis"
}

LIVE_FR3_REGIONS = {
    "Alpes": "alpes",
    "Alsace": "alsace",
    "Aquitaine": "aquitaine",
    "Auvergne": "auvergne",
    "Basse-Normandie": "basse_normandie",
    "Bourgogne": "bourgogne",
    "Bretagne": "bretagne",
    "Centre-Val de Loire": "centre",
    "Chapagne-Ardenne": "champagne_ardenne",
    "Corse": "corse",
    "Côte d'Azur": "cote_dazur",
    "Franche-Compté": "franche_comte",
    "Haute-Normandie": "haute_normandie",
    "Languedoc-Roussillon": "languedoc_roussillon",
    "Limousin": "limousin",
    "Lorraine": "lorraine",
    "Midi-Pyrénées": "midi_pyrenees",
    "Nord-Pas-de-Calais": "nord_pas_de_calais",
    "Paris Île-de-France": "paris_ile_de_france",
    "Pays de la Loire": "pays_de_la_loire",
    "Picardie": "picardie",
    "Poitou-Charentes": "poitou_charentes",
    "Provence-Alpes": "provence_alpes",
    "Rhône-Alpes": "rhone_alpes"
}

CATEGORIES_EDUCATION = {
    'Séries': URL_ROOT_EDUCATION + '/recherche?q=&type=series&page=%s',
    'Vidéos': URL_ROOT_EDUCATION + '/recherche?q=&type=video&page=%s'
}


CATEGORIES = {
    'Toutes catégories': 'https://pluzz.webservices.francetelevisions.fr/'
                         'mobile/liste/type/replay/chaine/%s/nb/20/debut/%s',
    'Info': 'https://pluzz.webservices.francetelevisions.fr/'
            'mobile/liste/type/replay/rubrique/info/nb/20/debut/%s',
    'Documentaire': 'https://pluzz.webservices.francetelevisions.fr/'
                    'mobile/liste/type/replay/rubrique/documentaire/'
                    'nb/20/debut/%s',
    'Série & Fiction': 'https://pluzz.webservices.francetelevisions.fr/'
                       'mobile/liste/type/replay/rubrique/seriefiction/nb/'
                       '20/debut/%s',
    'Magazine': 'https://pluzz.webservices.francetelevisions.fr/'
                'mobile/liste/type/replay/rubrique/magazine/nb/20/debut/%s',
    'Culture': 'https://pluzz.webservices.francetelevisions.fr/'
               'mobile/liste/type/replay/rubrique/culture/nb/20/debut/%s',
    'Jeunesse': 'https://pluzz.webservices.francetelevisions.fr/'
                'mobile/liste/type/replay/rubrique/jeunesse/nb/20/debut/%s',
    'Divertissement': 'https://pluzz.webservices.francetelevisions.fr/'
                      'mobile/liste/type/replay/rubrique/divertissement/nb/'
                      '20/debut/%s',
    'Sport': 'https://pluzz.webservices.francetelevisions.fr/'
             'mobile/liste/type/replay/rubrique/sport/nb/20/debut/%s',
    'Jeu': 'https://pluzz.webservices.francetelevisions.fr/'
           'mobile/liste/type/replay/rubrique/jeu/nb/20/debut/%s',
    'Version multilingue (VM)': 'https://pluzz.webservices.'
                                'francetelevisions.fr/'
                                'mobile/liste/filtre/multilingue/type/'
                                'replay/nb/20/debut/%s',
    'Sous-titrés': 'https://pluzz.webservices.francetelevisions.fr/'
                   'mobile/liste/filtre/soustitrage/type/replay/nb/'
                   '20/debut/%s',
    'Audiodescription (AD)': 'https://pluzz.webservices.francetelevisions.fr/'
                             'mobile/liste/filtre/audiodescription/type/replay'
                             '/nb/20/debut/%s',
    'Tous publics': 'https://pluzz.webservices.francetelevisions.fr/'
                    'mobile/liste/type/replay/filtre/touspublics'
                    '/nb/20/debut/%s'
}


def channel_entry(params):
    """Entry function of the module"""
    if 'replay_entry' == params.next:
        return root(params)
    elif 'list_shows' in params.next:
        return list_shows(params)
    elif 'list_videos' in params.next:
        return list_videos(params)
    elif 'play' in params.next:
        return get_video_url(params)
    elif 'search' in params.next:
        return search(params)
    return None


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def change_to_nicer_name(original_name):
    """Convert id name to label name"""
    if original_name in CATEGORIES_DISPLAY:
        return CATEGORIES_DISPLAY[original_name]
    return original_name


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def root(params):
    mode = 'replay'
    if params.channel_name == 'francetvsport':
        next_replay = 'list_shows_ftvsport'
    elif params.channel_name == 'studio-4' or \
            params.channel_name == 'irl':
        next_replay = 'list_shows_necritures_1'
    elif params.channel_name == 'francetveducation':
        next_replay = 'list_shows_education_1'
    else:
        next_replay = 'list_shows_1'

    params['next'] = next_replay
    params['page'] = '1'
    params['mode'] = mode
    params['module_name'] = params.module_name
    params['module_path'] = params.module_path
    return channel_entry(params)


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def list_shows(params):
    """Build categories listing"""
    shows = []
    if 'previous_listing' in params:
        shows = ast.literal_eval(params['previous_listing'])

    unique_item = dict()

    real_channel = params.channel_name
    if params.channel_name == 'la_1ere':
        real_channel = 'la_1ere_reunion%2C' \
                       'la_1ere_guyane%2C' \
                       'la_1ere_polynesie%2C' \
                       'la_1ere_martinique%2C' \
                       'la_1ere_mayotte%2C' \
                       'la_1ere_nouvellecaledonie%2C' \
                       'la_1ere_guadeloupe%2C' \
                       'la_1ere_wallisetfutuna%2C' \
                       'la_1ere_saintpierreetmiquelon'

    # Level 0
    if params.next == 'list_shows_1':

        url_json = CHANNEL_CATALOG % (real_channel)
        file_path = utils.download_catalog(
            url_json,
            '%s.json' % (
                params.channel_name))
        file_prgm = open(file_path).read()
        json_parser = json.loads(file_prgm)
        emissions = json_parser['reponse']['emissions']
        for emission in emissions:
            rubrique = emission['rubrique'].encode('utf-8')
            if rubrique not in unique_item:
                unique_item[rubrique] = rubrique
                rubrique_title = change_to_nicer_name(rubrique)

                shows.append({
                    'label': rubrique_title,
                    'url': common.PLUGIN.get_url(
                        module_path=params.module_path,
                        module_name=params.module_name,
                        action='replay_entry',
                        rubrique=rubrique,
                        next='list_shows_2_cat',
                        window_title=rubrique_title
                    )
                })

        # Last videos
        shows.append({
            'label': common.ADDON.get_localized_string(30704),
            'url': common.PLUGIN.get_url(
                module_path=params.module_path,
                module_name=params.module_name,
                action='replay_entry',
                next='list_shows_last',
                page='0',
                window_title=common.ADDON.get_localized_string(30704)
            )
        })

        # Search
        shows.append({
            'label': common.ADDON.get_localized_string(30703),
            'url': common.PLUGIN.get_url(
                module_path=params.module_path,
                module_name=params.module_name,
                action='replay_entry',
                next='search',
                page='0',
                window_title=common.ADDON.get_localized_string(30703)
            )
        })

        # from A to Z
        shows.append({
            'label': common.ADDON.get_localized_string(30705),
            'url': common.PLUGIN.get_url(
                module_path=params.module_path,
                module_name=params.module_name,
                action='replay_entry',
                next='list_shows_from_a_to_z',
                window_title=common.ADDON.get_localized_string(30705)
            )
        })

    # level 1
    elif 'list_shows_from_a_to_z' in params.next:
        shows.append({
            'label': common.ADDON.get_localized_string(30706),
            'url': common.PLUGIN.get_url(
                module_path=params.module_path,
                module_name=params.module_name,
                action='replay_entry',
                next='list_shows_2_from_a_to_z_CATEGORIES',
                page='0',
                url=URL_ALPHA % ('asc', '%s'),
                sens='asc',
                rubrique='no_rubrique',
                window_title=params.window_title
            )
        })
        shows.append({
            'label': common.ADDON.get_localized_string(30707),
            'url': common.PLUGIN.get_url(
                module_path=params.module_path,
                module_name=params.module_name,
                action='replay_entry',
                next='list_shows_2_from_a_to_z_CATEGORIES',
                page='0',
                url=URL_ALPHA % ('desc', '%s'),
                sens='desc',
                rubrique='no_rubrique',
                window_title=params.window_title
            )
        })

    # level 1
    elif 'list_shows_last' in params.next:
        for title, url in CATEGORIES.iteritems():
            if 'Toutes catégories' in title:
                url = url % (params.channel_name, '%s')
            shows.append({
                'label': title,
                'url': common.PLUGIN.get_url(
                    module_path=params.module_path,
                    module_name=params.module_name,
                    action='replay_entry',
                    next='list_videos_last',
                    page='0',
                    url=url,
                    title=title,
                    window_title=title
                )
            })

    # level 1 or 2
    elif 'list_shows_2' in params.next:
        if 'list_shows_2_cat' in params.next:
            url_json = CHANNEL_CATALOG % (real_channel)
            file_path = utils.download_catalog(
                url_json,
                '%s.json' % (
                    params.channel_name))
        elif 'list_shows_2_from_a_to_z_CATEGORIES' in params.next:
            url_json = URL_ALPHA % (params.sens, params.page)
            file_path = utils.download_catalog(
                url_json,
                '%s_%s_%s_alpha.json' % (
                    params.channel_name,
                    params.sens,
                    params.page))

        file_prgm = open(file_path).read()
        json_parser = json.loads(file_prgm)
        emissions = json_parser['reponse']['emissions']
        for emission in emissions:
            rubrique = emission['rubrique'].encode('utf-8')
            chaine_id = emission['chaine_id'].encode('utf-8')
            if ('from_a_to_z' in params.next and
                    chaine_id == params.channel_name) or \
                    rubrique == params.rubrique:
                titre_programme = emission['titre_programme'].encode('utf-8')
                if titre_programme != '':
                    id_programme = emission['id_programme'].encode('utf-8')
                    if id_programme == '':
                        id_programme = emission['id_emission'].encode('utf-8')
                    if id_programme not in unique_item:
                        unique_item[id_programme] = id_programme
                        icon = URL_IMG % (emission['image_large'])
                        genre = emission['genre']
                        accroche_programme = emission['accroche_programme']

                        info = {
                            'video': {
                                'title': titre_programme,
                                'plot': accroche_programme,
                                'genre': genre
                            }
                        }
                        shows.append({
                            'label': titre_programme,
                            'thumb': icon,
                            'fanart': icon,
                            'url': common.PLUGIN.get_url(
                                module_path=params.module_path,
                                module_name=params.module_name,
                                action='replay_entry',
                                next='list_videos_1',
                                id_programme=id_programme,
                                search=False,
                                page='0',
                                window_title=titre_programme,
                                fanart=icon
                            ),
                            'info': info
                        })
        if params.next == 'list_shows_2_from_a_to_z_CATEGORIES':
            # More videos...
            shows.append({
                'label': common.ADDON.get_localized_string(30700),
                'url': common.PLUGIN.get_url(
                    module_path=params.module_path,
                    module_name=params.module_name,
                    action='replay_entry',
                    next='list_shows_2_from_a_to_z_CATEGORIES',
                    sens=params.sens,
                    page=str(int(params.page) + 100),
                    window_title=params.window_title,
                    rubrique='no_rubrique',
                    update_listing=True,
                    previous_listing=str(shows)
                )
            })

    elif 'list_shows_necritures_1' in params.next:
        categories_html = utils.get_webcontent(
            URL_ROOT_NOUVELLES_ECRITURES % params.channel_name)
        categories_soup = bs(categories_html, 'html.parser')
        categories = categories_soup.find_all(
            'li', class_='genre-item')

        for category in categories:

            category_title = category.find('a').get_text().strip()
            category_data_panel = category.get('data-panel')

            shows.append({
                'label': category_title,
                'url': common.PLUGIN.get_url(
                    module_path=params.module_path,
                    module_name=params.module_name,
                    action='replay_entry',
                    category_data_panel=category_data_panel,
                    title=category_title,
                    next='list_shows_necritures_2',
                    window_title=category_title
                )
            })

    elif 'list_shows_necritures_2' in params.next:

        shows_html = utils.get_webcontent(
            URL_ROOT_NOUVELLES_ECRITURES % params.channel_name)
        shows_soup = bs(shows_html, 'html.parser')
        class_panel_value = 'panel %s' % params.category_data_panel
        list_shows_necritures = shows_soup.find(
            'div', class_=class_panel_value).find_all('li')

        for show_data in list_shows_necritures:

            show_url = URL_ROOT_NOUVELLES_ECRITURES % params.channel_name + \
                show_data.find('a').get('href')
            show_title = show_data.find('a').get_text().strip()
            show_image = show_data.find('a').get('data-img')

            shows.append({
                'label': show_title,
                'thumb': show_image,
                'url': common.PLUGIN.get_url(
                    module_path=params.module_path,
                    module_name=params.module_name,
                    action='replay_entry',
                    show_url=show_url,
                    title=show_title,
                    next='list_videos_necritures_1',
                    window_title=show_title
                )
            })

    elif 'list_shows_education_1' in params.next:

        for category_title, category_url in CATEGORIES_EDUCATION.iteritems():

            if category_title == 'Séries':
                next_value = 'list_shows_education_2'
            else:
                next_value = 'list_videos_education_1'

            shows.append({
                'label': category_title,
                'url': common.PLUGIN.get_url(
                    module_path=params.module_path,
                    module_name=params.module_name,
                    action='replay_entry',
                    category_url=category_url,
                    title=category_title,
                    page='1',
                    next=next_value,
                    window_title=category_title
                )
            })

    elif 'list_shows_education_2' in params.next:

        shows_html = utils.get_webcontent(
            params.category_url % params.page)
        shows_soup = bs(shows_html, 'html.parser')
        list_shows_education = shows_soup.find_all(
            'div', class_='col-xs-3 ')

        for show_data in list_shows_education:

            show_data_name = show_data.find(
                'div', class_='ftve-thumbnail ').get('data-contenu')
            show_title = show_data.find('h4').find(
                'a').get('title')
            show_image = show_data.find(
                'div', class_='thumbnail-img lazy').get('data-original')

            shows.append({
                'label': show_title,
                'thumb': show_image,
                'url': common.PLUGIN.get_url(
                    module_path=params.module_path,
                    module_name=params.module_name,
                    action='replay_entry',
                    show_data_name=show_data_name,
                    page='1',
                    title=show_title,
                    next='list_videos_education_2',
                    window_title=show_title
                )
            })

        # More programs...
        shows.append({
            'label': common.ADDON.get_localized_string(30708),
            'url': common.PLUGIN.get_url(
                module_path=params.module_path,
                module_name=params.module_name,
                action='replay_entry',
                next='list_shows_education_2',
                category_url=params.category_url,
                page=str(int(params.page) + 1),
                update_listing=True,
                previous_listing=str(shows)
            )
        })
    
    elif 'list_shows_ftvsport' in params.next:

        show_title = 'Videos'
        shows.append({
            'label': show_title,
            'url': common.PLUGIN.get_url(
                module_path=params.module_path,
                module_name=params.module_name,
                action='replay_entry',
                page='1',
                mode='videos',
                title=show_title,
                next='list_videos_ftvsport',
                window_title=show_title
            )
        })

        show_title = 'Replay'
        shows.append({
            'label': show_title,
            'url': common.PLUGIN.get_url(
                module_path=params.module_path,
                module_name=params.module_name,
                action='replay_entry',
                page='1',
                mode='replay',
                title=show_title,
                next='list_videos_ftvsport',
                window_title=show_title
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

    if params.next == 'list_videos_ftvsport':

        list_videos_html = utils.get_webcontent(
            URL_FRANCETV_SPORT % (params.mode) + \
                '?page=%s' % (params.page))
        list_videos_parserjson = json.loads(list_videos_html)

        for video in list_videos_parserjson["page"]["flux"]:

            title = video["title"]
            image = video["image"]["large_16_9"]
            duration = 0
            if 'duration' in video:
                duration = int(video["duration"])
            url_sport = URL_ROOT_SPORT + video["url"]
            html_sport = utils.get_webcontent(url_sport)
            id_diffusion = re.compile(
                r'data-video="(.*?)"').findall(html_sport)[0]

            info = {
                'video': {
                    'title': title,
                    # 'plot': plot,
                    # 'aired': aired,
                    # 'date': date,
                    'duration': duration,
                    # 'year': year,
                }
            }

            download_video = (
                common.GETTEXT('Download'),
                'XBMC.RunPlugin(' + common.PLUGIN.get_url(
                    action='download_video',
                    module_path=params.module_path,
                    module_name=params.module_name,
                    id_diffusion=id_diffusion) + ')'
            )
            context_menu = []
            context_menu.append(download_video)

            videos.append({
                'label': title,
                'fanart': image,
                'thumb': image,
                'url': common.PLUGIN.get_url(
                    module_path=params.module_path,
                    module_name=params.module_name,
                    action='replay_entry',
                    next='play_r',
                    id_diffusion=id_diffusion
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
                action='replay_entry',
                mode=params.mode,
                next=params.next,
                page=str(int(params.page) + 1),
                title=params.title,
                window_title=params.window_title,
                update_listing=True,
                previous_listing=str(videos)
            )
        })

    elif params.next == 'list_videos_education_1':

        list_videos_html = utils.get_webcontent(
            params.category_url % (params.page))
        list_videos_soup = bs(list_videos_html, 'html.parser')
        list_videos_datas = list_videos_soup.find_all(
            "div", class_="col-xs-3 ")

        for video_data in list_videos_datas:

            title = video_data.find('h4').find(
                'a').get('title')
            image = video_data.find(
                'div', class_='thumbnail-img lazy').get('data-original')
            duration = 0
            data_video_title = video_data.find(
                'div', class_='ftve-thumbnail ').get('data-contenu')
            html_video_data = utils.get_webcontent(
                URL_VIDEO_DATA_EDUCTATION % data_video_title)
            id_diffusion = re.compile(
                r'videos.francetv.fr\/video\/(.*?)\@'
            ).findall(html_video_data)[0]

            info = {
                'video': {
                    'title': title,
                    # 'plot': plot,
                    # 'aired': aired,
                    # 'date': date,
                    'duration': duration,
                    # 'year': year,
                }
            }

            download_video = (
                common.GETTEXT('Download'),
                'XBMC.RunPlugin(' + common.PLUGIN.get_url(
                    action='download_video',
                    module_path=params.module_path,
                    module_name=params.module_name,
                    id_diffusion=id_diffusion) + ')'
            )
            context_menu = []
            context_menu.append(download_video)

            videos.append({
                'label': title,
                'fanart': image,
                'thumb': image,
                'url': common.PLUGIN.get_url(
                    module_path=params.module_path,
                    module_name=params.module_name,
                    action='replay_entry',
                    next='play_r',
                    id_diffusion=id_diffusion
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
                action='replay_entry',
                category_url=params.category_url,
                next=params.next,
                page=str(int(params.page) + 1),
                title=params.title,
                window_title=params.window_title,
                update_listing=True,
                previous_listing=str(videos)
            )
        })

    elif params.next == 'list_videos_education_2':

        list_videos_html = utils.get_webcontent(
            URL_SERIE_DATA_EDUCTION % (params.show_data_name, params.page))
        list_videos_soup = bs(list_videos_html, 'html.parser')
        list_videos_datas = list_videos_soup.find(
            'div', class_='content-section').find_all(
                'div', class_='col-xs-3 ')

        for video_data in list_videos_datas:

            title = video_data.find('h4').find(
                'a').get('title')
            image = video_data.find(
                'div', class_='thumbnail-img lazy').get('data-original')
            duration = 0
            data_video_title = video_data.find(
                'div', class_='ftve-thumbnail ').get('data-contenu')
            html_video_data = utils.get_webcontent(
                URL_VIDEO_DATA_EDUCTATION % data_video_title)
            id_diffusion = re.compile(
                r'videos.francetv.fr\/video\/(.*?)\@').findall(
                html_video_data)[0]

            info = {
                'video': {
                    'title': title,
                    # 'plot': plot,
                    # 'aired': aired,
                    # 'date': date,
                    'duration': duration,
                    # 'year': year,
                }
            }

            download_video = (
                common.GETTEXT('Download'),
                'XBMC.RunPlugin(' + common.PLUGIN.get_url(
                    action='download_video',
                    module_path=params.module_path,
                    module_name=params.module_name,
                    id_diffusion=id_diffusion) + ')'
            )
            context_menu = []
            context_menu.append(download_video)

            videos.append({
                'label': title,
                'fanart': image,
                'thumb': image,
                'url': common.PLUGIN.get_url(
                    module_path=params.module_path,
                    module_name=params.module_name,
                    action='replay_entry',
                    next='play_r',
                    id_diffusion=id_diffusion
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
                action='replay_entry',
                show_data_name=params.show_data_name,
                next='list_videos_education_2',
                page=str(int(params.page) + 1),
                title=params.title,
                window_title=params.window_title,
                update_listing=True,
                previous_listing=str(videos)
            )
        })

    elif params.next == 'list_videos_necritures_1':

        replay_episodes_html = utils.get_webcontent(
            params.show_url)
        replay_episodes_soup = bs(replay_episodes_html, 'html.parser')
        episodes = replay_episodes_soup.find_all(
            "li", class_="push type-episode")
        episodes += replay_episodes_soup.find_all(
            "li", class_="push type-episode active")

        for episode in episodes:
            if episode.find('div', class_='description'):
                video_title = episode.find(
                    'div', class_='title').get_text().strip() + ' - ' + \
                    episode.find(
                        'div', class_='description').get_text().strip()
            else:
                video_title = episode.find(
                    'div', class_='title').get_text().strip()
            video_url = URL_ROOT_NOUVELLES_ECRITURES % params.channel_name + \
                episode.find('a').get('href')
            if episode.find('img'):
                video_img = episode.find('img').get('src')
            else:
                video_img = ''
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
                    action='replay_entry',
                    next='play_r',
                    video_url=video_url
                ),
                'is_playable': True,
                'info': info,
                'context_menu': context_menu
            })

    else:

        if 'search' in params.next:
            file_path = utils.download_catalog(
                URL_SEARCH % (params.query, params.page),
                '%s_%s_search.json' % (params.channel_name, params.query),
                force_dl=True
            )

        elif 'last' in params.next:
            file_path = utils.download_catalog(
                params.url % params.page,
                '%s_%s_%s_last.json' % (
                    params.channel_name,
                    params.page,
                    params.title)
            )

        elif 'from_a_to_z' in params.next:
            file_path = utils.download_catalog(
                params.url % params.page,
                '%s_%s_%s_last.json' % (
                    params.channel_name,
                    params.page,
                    params.sens)
            )

        else:
            file_path = utils.download_catalog(
                CHANNEL_CATALOG % params.channel_name,
                '%s.json' % params.channel_name
            )
        file_prgm = open(file_path).read()
        json_parser = json.loads(file_prgm)
        emissions = json_parser['reponse']['emissions']

        for emission in emissions:
            id_programme = emission['id_programme'].encode('utf-8')
            if id_programme == '':
                id_programme = emission['id_emission'].encode('utf-8')
            if 'search' in params.next \
                    or 'last' in params.next \
                    or 'from_a_to_z' in params.next \
                    or id_programme == params.id_programme:
                title = ''
                plot = ''
                duration = 0
                date = ''
                genre = ''
                id_diffusion = emission['id_diffusion']
                chaine_id = emission['chaine_id'].encode('utf-8')

                # If we are in search or alpha or last videos cases,
                # only add channel's shows
                if 'search' in params.next or\
                        'from_a_to_z' in params.next or\
                        'last' in params.next:
                    if chaine_id != params.channel_name:
                        continue

                file_prgm = utils.get_webcontent(
                    SHOW_INFO % (emission['id_diffusion']))
                if(file_prgm != ''):
                    json_parser_show = json.loads(file_prgm)
                    if json_parser_show['synopsis']:
                        plot = json_parser_show['synopsis'].encode('utf-8')
                    if json_parser_show['diffusion']['date_debut']:
                        date = json_parser_show['diffusion']['date_debut']
                        date = date.encode('utf-8')
                    if json_parser_show['real_duration']:
                        duration = int(json_parser_show['real_duration'])
                    if json_parser_show['titre']:
                        title = json_parser_show['titre'].encode('utf-8')
                    if json_parser_show['sous_titre']:
                        title = ' '.join((
                            title,
                            '- [I]',
                            json_parser_show['sous_titre'].encode('utf-8'),
                            '[/I]'))

                    if json_parser_show['genre'] != '':
                        genre = \
                            json_parser_show['genre'].encode('utf-8')

                    episode = 0
                    if 'episode' in json_parser_show:
                        episode = json_parser_show['episode']

                    season = 0
                    if 'saison' in json_parser_show:
                        season = json_parser_show['saison']

                    cast = []
                    director = ''
                    personnes = json_parser_show['personnes']
                    for personne in personnes:
                        fonctions = ' '.join(
                            x.encode('utf-8') for x in personne['fonctions'])
                        if 'Acteur' in fonctions:
                            cast.append(
                                personne['nom'].encode(
                                    'utf-8') + ' ' + personne['prenom'].encode(
                                        'utf-8'))
                        elif 'Réalisateur' in fonctions:
                            director = personne['nom'].encode(
                                'utf-8') + ' ' + \
                                personne['prenom'].encode('utf-8')

                    year = int(date[6:10])
                    day = date[:2]
                    month = date[3:5]
                    date = '.'.join((day, month, str(year)))
                    aired = '-'.join((str(year), month, day))
                    # date: string (%d.%m.%Y / 01.01.2009)
                    # aired: string (2008-12-07)

                    # image = URL_IMG % (json_parserShow['image'])
                    image = json_parser_show['image_secure']

                    info = {
                        'video': {
                            'title': title,
                            'plot': plot,
                            'aired': aired,
                            'date': date,
                            'duration': duration,
                            'year': year,
                            'genre': genre,
                            'mediatype': 'tvshow',
                            'season': season,
                            'episode': episode,
                            'cast': cast,
                            'director': director
                        }
                    }

                    download_video = (
                        common.GETTEXT('Download'),
                        'XBMC.RunPlugin(' + common.PLUGIN.get_url(
                            action='download_video',
                            module_path=params.module_path,
                            module_name=params.module_name,
                            id_diffusion=id_diffusion) + ')'
                    )
                    context_menu = []
                    context_menu.append(download_video)

                    videos.append({
                        'label': title,
                        'fanart': image,
                        'thumb': image,
                        'url': common.PLUGIN.get_url(
                            module_path=params.module_path,
                            module_name=params.module_name,
                            action='replay_entry',
                            next='play_r',
                            id_diffusion=id_diffusion
                        ),
                        'is_playable': True,
                        'info': info,
                        'context_menu': context_menu
                    })

        if 'search' in params.next:
            # More videos...
            videos.append({
                'label': common.ADDON.get_localized_string(30700),
                'url': common.PLUGIN.get_url(
                    module_path=params.module_path,
                    module_name=params.module_name,
                    action='replay_entry',
                    next='list_videos_search',
                    query=params.query,
                    page=str(int(params.page) + 20),
                    window_title=params.window_title,
                    update_listing=True,
                    previous_listing=str(videos)
                )
            })

        elif 'last' in params.next:
            # More videos...
            videos.append({
                'label': common.ADDON.get_localized_string(30700),
                'url': common.PLUGIN.get_url(
                    module_path=params.module_path,
                    module_name=params.module_name,
                    action='replay_entry',
                    url=params.url,
                    next=params.next,
                    page=str(int(params.page) + 20),
                    title=params.title,
                    window_title=params.window_title,
                    update_listing=True,
                    previous_listing=str(videos)
                )
            })

    return common.PLUGIN.create_listing(
        videos,
        sort_methods=(
            common.sp.xbmcplugin.SORT_METHOD_UNSORTED,
            common.sp.xbmcplugin.SORT_METHOD_DATE,
            common.sp.xbmcplugin.SORT_METHOD_DURATION,
            common.sp.xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE,
            common.sp.xbmcplugin.SORT_METHOD_EPISODE

        ),
        content='tvshows',
        update_listing='update_listing' in params,
        category=common.get_window_title()
    )


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def start_live_tv_stream(params):
    lives = []

    if params.channel_name == 'francetvsport':
        title = ''
        plot = ''
        duration = 0

        list_lives = utils.get_webcontent(
            URL_FRANCETV_SPORT % 'directs')
        list_lives_parserjson = json.loads(list_lives)

        if 'lives' in list_lives_parserjson["page"]:

            for live in list_lives_parserjson["page"]["lives"]:
                title = live["title"]
                image = live["image"]["large_16_9"]
                id_diffusion = live["sivideo-id"]

                try:
                    value_date = time.strftime(
                        '%d/%m/%Y %H:%M', time.localtime(live["start"]))
                except Exception:
                    value_date = ''
                plot = 'Live starts at ' + value_date

                info = {
                    'video': {
                        'title': title,
                        'plot': plot,
                        # 'aired': aired,
                        # 'date': date,
                        'duration': duration,
                        # 'year': year,
                    }
                }

                lives.append({
                    'label': title,
                    'fanart': image,
                    'thumb': image,
                    'url': common.PLUGIN.get_url(
                        module_path=params.module_path,
                        module_name=params.module_name,
                        action='start_live_tv_stream',
                        next='play_l',
                        id_diffusion=id_diffusion
                    ),
                    'is_playable': True,
                    'info': info
                })

        for live in list_lives_parserjson["page"]["upcoming-lives"]:

            title = live["title"]
            try:
                image = live["image"]["large_16_9"]
            except KeyError:
                image = ''
            # id_diffusion = live["sivideo-id"]

            try:
                value_date = time.strftime(
                    '%d/%m/%Y %H:%M', time.localtime(live["start"]))
            except Exception:
                value_date = ''
            plot = 'Live starts at ' + value_date

            info = {
                'video': {
                    'title': title,
                    'plot': plot,
                    # 'aired': aired,
                    # 'date': date,
                    'duration': duration,
                    # 'year': year,
                }
            }

            lives.append({
                'label': title,
                'fanart': image,
                'thumb': image,
                'url': common.PLUGIN.get_url(
                    module_path=params.module_path,
                    module_name=params.module_name,
                    action='start_live_tv_stream',
                    next='play_l'
                ),
                'is_playable': False,
                'info': info
            })

    elif params.channel_name == 'franceinfo':
        params['next'] = 'play_l'
        return get_video_url(params)

    elif params.channel_name == 'la_1ere':
        params['next'] = 'play_l'
        params['id_stream'] = LIVE_LA_1ERE[common.PLUGIN.get_setting(
            'la_1ere.region')]
        return get_video_url(params)

    elif params.channel_name == 'france3regions':
        params['next'] = 'play_l'
        params['id_stream'] = LIVE_FR3_REGIONS[common.PLUGIN.get_setting(
            'france3.region')]
        return get_video_url(params)

    else:
        params['next'] = 'play_l'
        return get_video_url(params)

    return lives


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def get_video_url(params):
    """Get video URL and start video player"""

    desired_quality = common.PLUGIN.get_setting('quality')

    if params.next == 'play_r' or params.next == 'download_video':
        if params.channel_name == 'studio-4' or params.channel_name == 'irl':

            video_html = utils.get_webcontent(
                params.video_url)
            video_soup = bs(video_html, 'html.parser')
            video_data = video_soup.find(
                'div', class_='player-wrapper')

            if video_data.find('a', class_='video_link'):
                id_diffusion = video_data.find(
                    'a', class_='video_link').get(
                        'href').split('video/')[1].split('@')[0]
                file_prgm = utils.get_webcontent(SHOW_INFO % id_diffusion)
                json_parser = json.loads(file_prgm)

                url_selected = ''

                if desired_quality == "DIALOG":
                    all_datas_videos_quality = []
                    all_datas_videos_path = []

                    for video in json_parser['videos']:
                        if video['format'] == 'hls_v5_os' or \
                                video['format'] == 'm3u8-download':
                            if video['format'] == 'hls_v5_os':
                                all_datas_videos_quality.append("HD")
                            else:
                                all_datas_videos_quality.append("SD")
                            all_datas_videos_path.append(video['url'])

                    seleted_item = common.sp.xbmcgui.Dialog().select(
                        common.GETTEXT('Choose video quality'),
                        all_datas_videos_quality)

                    if seleted_item == -1:
                        return None

                    url_selected = all_datas_videos_path[seleted_item]

                elif desired_quality == "BEST":
                    for video in json_parser['videos']:
                        if video['format'] == 'hls_v5_os':
                            url_selected = video['url']
                else:
                    for video in json_parser['videos']:
                        if video['format'] == 'm3u8-download':
                            url_selected = video['url']

                return url_selected

            else:
                url_video_resolver = video_data.find('iframe').get('src')
                # Case Youtube
                if 'youtube' in url_video_resolver:
                    video_id = url_video_resolver.split(
                        'youtube.com/embed/')[1]
                    if params.next == 'download_video':
                        return resolver.get_stream_youtube(
                            video_id, True)
                    else:
                        return resolver.get_stream_youtube(
                            video_id, False)
                # Case DailyMotion
                elif 'dailymotion' in url_video_resolver:
                    video_id = url_video_resolver.split(
                        'dailymotion.com/embed/video/')[1]
                    if params.next == 'download_video':
                        return resolver.get_stream_dailymotion(
                            video_id, True)
                    else:
                        return resolver.get_stream_dailymotion(
                            video_id, False)
                else:
                    return None
        else:

            file_prgm = utils.get_webcontent(SHOW_INFO % (params.id_diffusion))
            json_parser = json.loads(file_prgm)

            url_selected = ''

            if desired_quality == "DIALOG":
                all_datas_videos_quality = []
                all_datas_videos_path = []

                for video in json_parser['videos']:
                    if video['format'] == 'hls_v5_os' or \
                            video['format'] == 'm3u8-download':
                        if video['format'] == 'hls_v5_os':
                            all_datas_videos_quality.append("HD")
                        else:
                            all_datas_videos_quality.append("SD")
                        all_datas_videos_path.append(
                            (video['url'], video['drm']))

                seleted_item = common.sp.xbmcgui.Dialog().select(
                    common.GETTEXT('Choose video quality'),
                    all_datas_videos_quality)

                if seleted_item == -1:
                    return None

                url_selected = all_datas_videos_path[seleted_item][0]
                drm = all_datas_videos_path[seleted_item][1]

            elif desired_quality == "BEST":
                for video in json_parser['videos']:
                    if video['format'] == 'hls_v5_os':
                        url_selected = video['url']
                        drm = video['drm']
            else:
                for video in json_parser['videos']:
                    if video['format'] == 'm3u8-download':
                        url_selected = video['url']
                        drm = video['drm']

            if drm:
                utils.send_notification(
                    common.ADDON.get_localized_string(30702))
                return None
            else:
                return url_selected

    elif params.next == 'play_l':

        if params.channel_name == 'la_1ere' or \
                params.channel_name == 'france3regions':
            file_prgm = utils.get_webcontent(
                LIVE_INFO % (params.id_stream))
        elif params.channel_name == 'francetvsport':
            file_prgm = utils.get_webcontent(
                SHOW_INFO % (params.id_diffusion))
        else:
            file_prgm = utils.get_webcontent(
                LIVE_INFO % (params.channel_name))

        json_parser = json.loads(file_prgm)

        url_hls_v1 = ''
        url_hls_v5 = ''
        url_hls = ''

        for video in json_parser['videos']:
            if 'format' in video:
                if 'hls_v1_os' in video['format'] and \
                        video['geoblocage'] is not None:
                    url_hls_v1 = video['url']
                if 'hls_v5_os' in video['format'] and \
                        video['geoblocage'] is not None:
                    url_hls_v5 = video['url']
                if 'hls' in video['format']:
                    url_hls = video['url']

        final_url = ''

        # Case France 3 Région
        if url_hls_v1 == '' and url_hls_v5 == '':
            final_url = url_hls
        # Case Jarvis
        if common.sp.xbmc.__version__ == '2.24.0' \
                and url_hls_v1 != '':
            final_url = url_hls_v1
        # Case Krypton, Leia, ...
        if final_url == '' and url_hls_v5 != '':
            final_url = url_hls_v5
        elif final_url == '':
            final_url = url_hls_v1

        file_prgm2 = utils.get_webcontent(HDFAUTH_URL % (final_url))
        json_parser2 = json.loads(file_prgm2)

        return json_parser2['url']


def search(params):
    """Show keyboard to search a program"""
    keyboard = common.sp.xbmc.Keyboard(
        default='',
        title='',
        hidden=False)
    keyboard.doModal()
    if keyboard.isConfirmed():
        query = keyboard.getText()
        params['next'] = 'list_videos_search'
        params['page'] = '0'
        params['query'] = query
        return list_videos(params)

    else:
        return None
