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

# Liste A à Z
# Si FR3 ou FR1 : Régions


import json
from resources.lib import utils
from resources.lib import common
import ast

channel_catalog = 'http://pluzz.webservices.francetelevisions.fr/' \
                  'pluzz/liste/type/replay/nb/10000/chaine/%s'
# channel_catalog = 'https://pluzz.webservices.francetelevisions.fr/' \
#                   'mobile/liste/type/replay/chaine/%s/nb/20/debut/%s'
# page inc: 20

show_info = 'http://webservices.francetelevisions.fr/tools/' \
            'getInfosOeuvre/v2/?idDiffusion=%s&catalogue=Pluzz'

url_img = 'http://refonte.webservices.francetelevisions.fr%s'

url_search = 'https://pluzz.webservices.francetelevisions.fr/' \
             'mobile/recherche/nb/20/tri/date/requete/%s/debut/%s'

url_alpha = 'https://pluzz.webservices.francetelevisions.fr/' \
            'mobile/liste/type/replay/tri/alpha/sens/%s/nb/100/' \
            'debut/%s/lastof/1'
# sens: asc or desc
# page inc: 100

categories_display = {
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
    "saintpierreetmiquelon": "St-Pierre et Miquelon 1ère",
    "wallisetfutuna": "Wallis et Futuna 1ère",
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

categories = {
    'Toutes catégories': 'https://pluzz.webservices.francetelevisions.fr/'
    'mobile/liste/type/replay/chaine/%s/nb/20/debut/%s',
    'Info': 'https://pluzz.webservices.francetelevisions.fr/'
    'mobile/liste/type/replay/rubrique/info/nb/20/debut/%s',
    'Documentaire': 'https://pluzz.webservices.francetelevisions.fr/'
    'mobile/liste/type/replay/rubrique/documentaire/nb/20/debut/%s',
    'Série & Fiction': 'https://pluzz.webservices.francetelevisions.fr/'
    'mobile/liste/type/replay/rubrique/seriefiction/nb/20/debut/%s',
    'Magazine': 'https://pluzz.webservices.francetelevisions.fr/'
    'mobile/liste/type/replay/rubrique/magazine/nb/20/debut/%s',
    'Culture': 'https://pluzz.webservices.francetelevisions.fr/'
    'mobile/liste/type/replay/rubrique/culture/nb/20/debut/%s',
    'Jeunesse': 'https://pluzz.webservices.francetelevisions.fr/'
    'mobile/liste/type/replay/rubrique/jeunesse/nb/20/debut/%s',
    'Divertissement': 'https://pluzz.webservices.francetelevisions.fr/'
    'mobile/liste/type/replay/rubrique/divertissement/nb/20/debut/%s',
    'Sport': 'https://pluzz.webservices.francetelevisions.fr/'
    'mobile/liste/type/replay/rubrique/sport/nb/20/debut/%s',
    'Jeu': 'https://pluzz.webservices.francetelevisions.fr/'
    'mobile/liste/type/replay/rubrique/jeu/nb/20/debut/%s',
    'Version multilingue (VM)': 'https://pluzz.webservices.francetelevisions.fr/'
    'mobile/liste/filtre/multilingue/type/replay/nb/20/debut/%s',
    'Sous-titrés': 'https://pluzz.webservices.francetelevisions.fr/'
    'mobile/liste/filtre/soustitrage/type/replay/nb/20/debut/%s',
    'Audiodescription (AD)': 'https://pluzz.webservices.francetelevisions.fr/'
    'mobile/liste/filtre/audiodescription/type/replay/nb/20/debut/%s',
    'Tous publics': 'https://pluzz.webservices.francetelevisions.fr/'
    'mobile/liste/type/replay/filtre/touspublics/nb/20/debut/%s'
}


def channel_entry(params):
    if 'list_shows' in params.next:
        return list_shows(params)
    elif 'list_videos' in params.next:
        return list_videos(params)
    elif 'play' in params.next:
        return get_video_URL(params)
    elif 'search' in params.next:
        return search(params)


@common.plugin.cached(common.cache_time)
def change_to_nicer_name(original_name):
    if original_name in categories_display:
        return categories_display[original_name]
    return original_name


@common.plugin.cached(common.cache_time)
def list_shows(params):
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
        url_json = channel_catalog % (real_channel)
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
                    'url': common.plugin.get_url(
                        action='channel_entry',
                        rubrique=rubrique,
                        next='list_shows_2_cat',
                        window_title=rubrique_title
                    )
                })

        # Last videos
        shows.append({
            'label': common.addon.get_localized_string(30104),
            'url': common.plugin.get_url(
                action='channel_entry',
                next='list_shows_last',
                page='0',
                window_title=common.addon.get_localized_string(30104)
            )
        })

        # Search
        shows.append({
            'label': common.addon.get_localized_string(30103),
            'url': common.plugin.get_url(
                action='channel_entry',
                next='search',
                page='0',
                window_title=common.addon.get_localized_string(30103)
            )
        })

        # from A to Z
        shows.append({
            'label': common.addon.get_localized_string(30105),
            'url': common.plugin.get_url(
                action='channel_entry',
                next='list_shows_from_a_to_z',
                window_title=common.addon.get_localized_string(30105)
            )
        })

    # level 1
    elif 'list_shows_from_a_to_z' in params.next:
        shows.append({
            'label': common.addon.get_localized_string(30106),
            'url': common.plugin.get_url(
                action='channel_entry',
                next='list_shows_2_from_a_to_z_categories',
                page='0',
                url=url_alpha % ('asc', '%s'),
                sens='asc',
                rubrique='no_rubrique',
                window_title=params.window_title
            )
        })
        shows.append({
            'label': common.addon.get_localized_string(30107),
            'url': common.plugin.get_url(
                action='channel_entry',
                next='list_shows_2_from_a_to_z_categories',
                page='0',
                url=url_alpha % ('desc', '%s'),
                sens='desc',
                rubrique='no_rubrique',
                window_title=params.window_title
            )
        })

    # level 1
    elif 'list_shows_last' in params.next:
        for title, url in categories.iteritems():
            if 'Toutes catégories' in title:
                url = url % (params.channel_name, '%s')
            shows.append({
                'label': title,
                'url': common.plugin.get_url(
                    action='channel_entry',
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
            url_json = channel_catalog % (real_channel)
            file_path = utils.download_catalog(
                url_json,
                '%s.json' % (
                    params.channel_name))
        elif 'list_shows_2_from_a_to_z_categories' in params.next:
            url_json = url_alpha % (params.sens, params.page)
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
                        icon = url_img % (emission['image_large'])
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
                            'url': common.plugin.get_url(
                                action='channel_entry',
                                next='list_videos_1',
                                id_programme=id_programme,
                                search=False,
                                page='0',
                                window_title=titre_programme,
                                fanart=icon
                            ),
                            'info': info
                        })
        if params.next == 'list_shows_2_from_a_to_z_categories':
            # More videos...
            shows.append({
                'label': common.addon.get_localized_string(30100),
                'url': common.plugin.get_url(
                    action='channel_entry',
                    next='list_shows_2_from_a_to_z_categories',
                    sens=params.sens,
                    page=str(int(params.page) + 100),
                    window_title=params.window_title,
                    rubrique='no_rubrique',
                    update_listing=True,
                    previous_listing=str(shows)
                )
            })

    return common.plugin.create_listing(
        shows,
        sort_methods=(
            common.sp.xbmcplugin.SORT_METHOD_UNSORTED,
            common.sp.xbmcplugin.SORT_METHOD_LABEL
        ),
        update_listing='update_listing' in params,
    )


@common.plugin.cached(common.cache_time)
def list_videos(params):
    videos = []
    if 'previous_listing' in params:
        videos = ast.literal_eval(params['previous_listing'])

    if 'search' in params.next:
        file_path = utils.download_catalog(
            url_search % (params.query, params.page),
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
            channel_catalog % params.channel_name,
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
                show_info % (emission['id_diffusion']))
            if(file_prgm != ''):
                json_parserShow = json.loads(file_prgm)
                if json_parserShow['synopsis']:
                    plot = json_parserShow['synopsis'].encode('utf-8')
                if json_parserShow['diffusion']['date_debut']:
                    date = json_parserShow['diffusion']['date_debut']
                    date = date.encode('utf-8')
                if json_parserShow['real_duration']:
                    duration = int(json_parserShow['real_duration'])
                if json_parserShow['titre']:
                    title = json_parserShow['titre'].encode('utf-8')
                if json_parserShow['sous_titre']:
                    title = ' '.join((
                        title,
                        '- [I]',
                        json_parserShow['sous_titre'].encode('utf-8'),
                        '[/I]'))

                if json_parserShow['genre'] != '':
                    genre = \
                        json_parserShow['genre'].encode('utf-8')

                episode = 0
                if 'episode' in json_parserShow:
                    episode = json_parserShow['episode']

                season = 0
                if 'saison' in json_parserShow:
                    season = json_parserShow['saison']

                cast = []
                director = ''
                personnes = json_parserShow['personnes']
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
                            'utf-8') + ' ' + personne['prenom'].encode('utf-8')

                year = int(date[6:10])
                day = date[:2]
                month = date[3:5]
                date = '.'.join((day, month, str(year)))
                aired = '-'.join((str(year), month, day))
                # date : string (%d.%m.%Y / 01.01.2009)
                # aired : string (2008-12-07)

                # image = url_img % (json_parserShow['image'])
                image = json_parserShow['image_secure']

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

                videos.append({
                    'label': title,
                    'fanart': image,
                    'thumb': image,
                    'url': common.plugin.get_url(
                        action='channel_entry',
                        next='play',
                        id_diffusion=id_diffusion
                    ),
                    'is_playable': True,
                    'info': info
                })

    if 'search' in params.next:
        # More videos...
        videos.append({
            'label': common.addon.get_localized_string(30100),
            'url': common.plugin.get_url(
                action='channel_entry',
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
            'label': common.addon.get_localized_string(30100),
            'url': common.plugin.get_url(
                action='channel_entry',
                url=params.url,
                next=params.next,
                page=str(int(params.page) + 20),
                title=params.title,
                window_title=params.window_title,
                update_listing=True,
                previous_listing=str(videos)
            )

        })

    return common.plugin.create_listing(
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
    )


@common.plugin.cached(common.cache_time)
def get_video_URL(params):
        file_prgm = utils.get_webcontent(show_info % (params.id_diffusion))
        json_parser = json.loads(file_prgm)
        url_HD = ''
        url_SD = ''
        for video in json_parser['videos']:
            if video['format'] == 'hls_v5_os':
                url_HD = video['url']
            if video['format'] == 'm3u8-download':
                url_SD = video['url']

        desired_quality = common.plugin.get_setting(
            params.channel_id + '.quality')

        if desired_quality == 'HD' and url_HD is not None:
            return url_HD
        else:
            return url_SD


def search(params):
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
