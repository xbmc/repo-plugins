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

import json
from resources.lib import utils
from resources.lib import common

channelCatalog = 'http://pluzz.webservices.francetelevisions.fr/' \
                 'pluzz/liste/type/replay/nb/10000/chaine/%s'

showInfo = 'http://webservices.francetelevisions.fr/tools/getInfosOeuvre/v2/' \
           '?idDiffusion=%s&catalogue=Pluzz'

imgURL = 'http://refonte.webservices.francetelevisions.fr%s'

categories = {"france2": "France 2",
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
              "culture": "Culture"}


def channel_entry(params):
    if 'list_shows' in params.next:
        return list_shows(params)
    elif 'list_videos' in params.next:
        return list_videos(params)
    elif 'play' in params.next:
        return get_video_URL(params)


@common.plugin.cached(common.cache_time)
def list_shows(params):
    shows = []
    uniqueItem = dict()

    realChannel = params.channel_name
    if params.channel_name == 'la_1ere':
        realChannel = 'la_1ere_reunion%2C' \
                      'la_1ere_guyane%2C' \
                      'la_1ere_polynesie%2C' \
                      'la_1ere_martinique%2C' \
                      'la_1ere_mayotte%2C' \
                      'la_1ere_nouvellecaledonie%2C' \
                      'la_1ere_guadeloupe%2C' \
                      'la_1ere_wallisetfutuna%2C' \
                      'la_1ere_saintpierreetmiquelon'

    url_json = channelCatalog % (realChannel)
    filePath = utils.download_catalog(
        url_json,
        '%s.json' % (params.channel_name))
    filPrgm = open(filePath).read()
    jsonParser = json.loads(filPrgm)
    emissions = jsonParser['reponse']['emissions']

    if params.next == 'list_shows_1':
        for emission in emissions:
            rubrique = emission['rubrique'].encode('utf-8')
            if rubrique not in uniqueItem:
                uniqueItem[rubrique] = rubrique
                rubrique_title = change_to_nicer_name(rubrique)

                shows.append({
                    'label': rubrique_title,
                    'url': common.plugin.get_url(
                        action='channel_entry',
                        rubrique=rubrique,
                        next='list_shows_2'
                    )
                })

        sort_methods = (
            common.sp.xbmcplugin.SORT_METHOD_UNSORTED,
            common.sp.xbmcplugin.SORT_METHOD_LABEL
        )

        shows = common.plugin.create_listing(
            shows,
            sort_methods=sort_methods
        )

    elif params.next == 'list_shows_2':
        for emission in emissions:
            rubrique = emission['rubrique'].encode('utf-8')
            if rubrique == params.rubrique:
                titre_programme = emission['titre_programme'].encode('utf-8')
                if titre_programme != '':
                    id_programme = emission['id_programme'].encode('utf-8')
                    if id_programme == '':
                        id_programme = emission['id_emission'].encode('utf-8')
                    if id_programme not in uniqueItem:
                        uniqueItem[id_programme] = id_programme
                        icon = imgURL % (emission['image_large'])
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
                            'url': common.plugin.get_url(
                                action='channel_entry',
                                next='list_videos_1',
                                id_programme=id_programme,
                            ),
                            'info': info
                        })

        sort_methods = (
            common.sp.xbmcplugin.SORT_METHOD_UNSORTED,
            common.sp.xbmcplugin.SORT_METHOD_LABEL
        )

        shows = common.plugin.create_listing(
            shows,
            content='tvshows',
            sort_methods=sort_methods
        )

    return shows


@common.plugin.cached(common.cache_time)
def change_to_nicer_name(original_name):
    if original_name in categories:
        return categories[original_name]
    return original_name


@common.plugin.cached(common.cache_time)
def list_videos(params):
    videos = []
    filePath = utils.download_catalog(
        channelCatalog % (params.channel_name),
        '%s.json' % (params.channel_name)
    )
    filPrgm = open(filePath).read()
    jsonParser = json.loads(filPrgm)
    emissions = jsonParser['reponse']['emissions']
    for emission in emissions:
        id_programme = emission['id_programme'].encode('utf-8')
        if id_programme == '':
            id_programme = emission['id_emission'].encode('utf-8')
        if id_programme == params.id_programme:
            title = ''
            plot = ''
            duration = 0
            date = ''
            genre = ''
            id_diffusion = emission['id_diffusion']
            filPrgm = utils.get_webcontent(
                showInfo % (emission['id_diffusion']))
            if(filPrgm != ''):
                jsonParserShow = json.loads(filPrgm)
                if jsonParserShow['synopsis']:
                    plot = jsonParserShow['synopsis'].encode('utf-8')
                if jsonParserShow['diffusion']['date_debut']:
                    date = jsonParserShow['diffusion']['date_debut']
                    date = date.encode('utf-8')
                if jsonParserShow['real_duration']:
                    duration = int(jsonParserShow['real_duration'])
                if jsonParserShow['titre']:
                    title = jsonParserShow['titre'].encode('utf-8')
                if jsonParserShow['sous_titre']:
                    title = ' '.join((
                        title,
                        '- [I]',
                        jsonParserShow['sous_titre'].encode('utf-8'),
                        '[/I]'))

                if jsonParserShow['genre'] != '':
                    genre = \
                        jsonParserShow['genre'].encode('utf-8')

                year = int(date[6:10])
                day = date[:2]
                month = date[3:5]
                date = '.'.join((day, month, str(year)))
                aired = '-'.join((str(year), month, day))
                # date : string (%d.%m.%Y / 01.01.2009)
                # aired : string (2008-12-07)
                image = imgURL % (jsonParserShow['image'])
                info = {
                    'video': {
                        'title': title,
                        'plot': plot,
                        'aired': aired,
                        'date': date,
                        'duration': duration,
                        'year': year,
                        'genre': genre
                    }
                }

                videos.append({
                    'label': title,
                    'thumb': image,
                    'url': common.plugin.get_url(
                        action='channel_entry',
                        next='play',
                        id_diffusion=id_diffusion
                    ),
                    'is_playable': True,
                    'info': info
                })

    sort_methods = (
        common.sp.xbmcplugin.SORT_METHOD_DATE,
        common.sp.xbmcplugin.SORT_METHOD_DURATION,
        common.sp.xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE,
        common.sp.xbmcplugin.SORT_METHOD_UNSORTED
    )
    return common.plugin.create_listing(
        videos,
        sort_methods=sort_methods,
        content='tvshows')


@common.plugin.cached(common.cache_time)
def get_video_URL(params):
        filPrgm = utils.get_webcontent(showInfo % (params.id_diffusion))
        jsonParser = json.loads(filPrgm)
        url_HD = ''
        url_SD = ''
        for video in jsonParser['videos']:
            if video['format'] == 'hls_v5_os':
                url_HD = video['url']
            if video['format'] == 'm3u8-download':
                url_SD = video['url']

        disered_quality = common.plugin.get_setting(
            params.channel_id + '.quality')

        if disered_quality == 'HD' and url_HD is not None:
            return url_HD
        else:
            return url_SD
