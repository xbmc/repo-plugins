# -*- coding: utf-8 -*-
"""
    Catch-up TV & More
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

import os
import time
import datetime
import requests
import threading
import xml.etree.ElementTree as ET
from resources.lib import skeleton
from resources.lib import common
from resources.lib import utils

XMLTV_FILEPATH = os.path.join(common.ADDON_DATA, 'xmltv_fr.xml')


LIVE_FR3_REGIONS = {
    "Alpes": "C1921.api.telerama.fr",
    "Alsace": "C1922.api.telerama.fr",
    "Aquitaine": "C1923.api.telerama.fr",
    "Auvergne": "C1924.api.telerama.fr",
    "Basse-Normandie": "C1925.api.telerama.fr",
    "Bourgogne": "C1926.api.telerama.fr",
    "Bretagne": "C1927.api.telerama.fr",
    "Centre-Val de Loire": "C1928.api.telerama.fr",
    "Chapagne-Ardenne": "C1929.api.telerama.fr",
    "Corse": "C308.api.telerama.fr",
    "Côte d'Azur": "C1931.api.telerama.fr",
    "Franche-Compté": "C1932.api.telerama.fr",
    "Haute-Normandie": "C1933.api.telerama.fr",
    "Languedoc-Roussillon": "C1934.api.telerama.fr",
    "Limousin": "C1935.api.telerama.fr",
    "Lorraine": "C1936.api.telerama.fr",
    "Midi-Pyrénées": "C1937.api.telerama.fr",
    "Nord-Pas-de-Calais": "C1938.api.telerama.fr",
    "Paris Île-de-France": "C1939.api.telerama.fr",
    "Pays de la Loire": "C1940.api.telerama.fr",
    "Picardie": "C1941.api.telerama.fr",
    "Poitou-Charentes": "C1942.api.telerama.fr",
    "Provence-Alpes": "C1943.api.telerama.fr",
    "Rhône-Alpes": "C1944.api.telerama.fr"
}

LIVE_LA_1ERE = {
    "Guadeloupe 1ère": "C329.api.telerama.fr",
    "Guyane 1ère": "C260.api.telerama.fr",
    "Martinique 1ère": "C328.api.telerama.fr",
    "Mayotte 1ère": '',
    "Nouvelle Calédonie 1ère": "C240.api.telerama.fr",
    "Polynésie 1ère": "C459.api.telerama.fr",
    "Réunion 1ère": "C245.api.telerama.fr",
    "St-Pierre et Miquelon 1ère": '',
    "Wallis et Futuna 1ère": ''
}

XMLTV_CHANNEL_ID = {
    'tf1': 'C192.api.telerama.fr',
    'france2': 'C4.api.telerama.fr',
    'france3': 'C80.api.telerama.fr',
    'france5': 'C47.api.telerama.fr',
    'canalplus': 'C34.api.telerama.fr',
    'c8': 'C445.api.telerama.fr',
    'tmc': 'C195.api.telerama.fr',
    'tfx': 'C446.api.telerama.fr',
    'nrj12': 'C444.api.telerama.fr',
    'france4': 'C78.api.telerama.fr',
    'bfmtv': 'C481.api.telerama.fr',
    'cnews': 'C226.api.telerama.fr',
    'cstar': 'C458.api.telerama.fr',
    'gulli': 'C482.api.telerama.fr',
    'franceo': 'C160.api.telerama.fr',
    'tf1-series-films': 'C1404.api.telerama.fr',
    'lequipe': 'C1401.api.telerama.fr',
    'numero23': 'C1402.api.telerama.fr',
    'cherie25': 'C1399.api.telerama.fr',
    'la_1ere': LIVE_LA_1ERE[common.PLUGIN.get_setting(
        'la_1ere.region')],
    'franceinfo': 'C2111.api.telerama.fr',
    'bfmbusiness': 'C1073.api.telerama.fr',
    'rmc': 'C546.api.telerama.fr',
    'lci': 'C112.api.telerama.fr',
    'lcp': 'C234.api.telerama.fr',
    'rmcdecouverte': 'C1400.api.telerama.fr',
    'publicsenat': '',
    'francetvsport': 'multiple_streams',
    'gong': '',
    'france3regions': LIVE_FR3_REGIONS[common.PLUGIN.get_setting(
        'france3.region')],
    'bfmparis': ''
}


def download_xmltv():
    if os.path.exists(XMLTV_FILEPATH):
        mtime = os.stat(XMLTV_FILEPATH).st_mtime
        dl_file = (time.time() - mtime > 3600)
    else:
        dl_file = True
    if dl_file:
        r = requests.get("https://repo.cecchettosylvain.fr/xmltv/xmltv_fr.xml")
        with open(XMLTV_FILEPATH, 'wb') as f:
            f.write(r.content)


def download_xmltv_in_background():
    download_thread = threading.Thread(target=download_xmltv)
    download_thread.start()
    return


@common.PLUGIN.mem_cached(2)
def build_live_tv_menu(params):
    # First we parse the xmltv guide
    channels_xmltv = {}
    pgrms_xmltv = {}
    # current_time = int(time.strftime('%Y%m%d%H%M%S'))
    current_time = int(datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S'))
    if os.path.exists(XMLTV_FILEPATH):
        tree = ET.parse(XMLTV_FILEPATH)
        root = tree.getroot()
        for channel in root.findall('channel'):
            channels_xmltv[channel.get('id')] = channel
        for pgrm in root.findall('programme'):
            pgrm_channel = pgrm.get('channel')
            if pgrm_channel in pgrms_xmltv:
                continue
            pgrm_start_s = pgrm.get('start')
            pgrm_start = int(pgrm_start_s.split()[0])
            pgrm_stop_s = pgrm.get('stop')
            pgrm_stop = int(pgrm_stop_s.split()[0])
            if current_time >= pgrm_start and \
                    current_time <= pgrm_stop:
                pgrms_xmltv[pgrm_channel] = pgrm

    # We sort not hidden channels
    menu = []
    folder_path = eval(params.item_path)
    for channel in eval(params.item_skeleton):
        channel_name = channel[0]
        # If channel isn't disable
        if common.PLUGIN.get_setting(channel_name):
            # Get order value in settings file
            channel_order = common.PLUGIN.get_setting(channel_name + '.order')
            channel_path = list(folder_path)
            channel_path.append(skeleton.CHANNELS[channel_name])

            item = (channel_order, channel_name, channel_path)
            menu.append(item)

    menu = sorted(menu, key=lambda x: x[0])

    listing = []
    for index, (channel_order, channel_name, channel_path) in enumerate(menu):
        params['module_path'] = str(channel_path)
        params['module_name'] = channel_name
        params['channel_label'] = skeleton.LABELS[channel_name]

        # Legacy fix (il faudrait remplacer channel_name par
        # module_name dans tous les .py des chaines)
        params['channel_name'] = params.module_name

        item = {}
        # Build context menu (Move up, move down, ...)
        context_menu = []

        item_down = (
            common.GETTEXT('Move down'),
            'XBMC.RunPlugin(' + common.PLUGIN.get_url(
                action='move',
                direction='down',
                item_id_order=channel_name + '.order',
                displayed_items=menu) + ')'
        )
        item_up = (
            common.GETTEXT('Move up'),
            'XBMC.RunPlugin(' + common.PLUGIN.get_url(
                action='move',
                direction='up',
                item_id_order=channel_name + '.order',
                displayed_items=menu) + ')'
        )

        if index == 0:
            context_menu.append(item_down)
        elif index == len(menu) - 1:
            context_menu.append(item_up)
        else:
            context_menu.append(item_up)
            context_menu.append(item_down)

        hide = (
            common.GETTEXT('Hide'),
            'XBMC.RunPlugin(' + common.PLUGIN.get_url(
                action='hide',
                item_id=channel_name) + ')'
        )
        context_menu.append(hide)

        image = None
        plot = None
        aspect = None
        year = None
        rating = None
        duration = None
        cast = []
        director = None
        writer = None
        plotoutline = None
        episode = None
        season = None
        icon = None

        # Is this channel exists in XMLTV grab infos
        channel_xmltv_id = XMLTV_CHANNEL_ID[params.module_name]
        if 'api.telerama.fr' in channel_xmltv_id and \
                channel_xmltv_id in pgrms_xmltv:
            title_channel = channels_xmltv[channel_xmltv_id].find(
                'display-name').text
            icon = channels_xmltv[channel_xmltv_id].find(
                'icon').get('src')
            pgrm = pgrms_xmltv[channel_xmltv_id]
            pgrm_name = pgrm.find('title').text
            title = title_channel + " - [I]" + pgrm_name + "[/I]"

            plot_object = pgrm.find('desc')
            if plot_object is not None:
                plot = plot_object.text

            sub_title_object = pgrm.find('sub-title')
            if sub_title_object is not None:
                if plot is None:
                    plot = sub_title_object.text
                else:
                    plot = sub_title_object.text + "[CR]" + plot

            if plot is not None:
                plot = plot.replace('<P>', '[CR]')
                plot = plot.replace('</P>;', '[CR]')
                plot = plot.replace('</I>;', '[/I]')
                plot = plot.replace('<I>', '[I]')

            image_object = pgrm.find('icon')
            if image_object is not None:
                image = image_object.get('src')

            aspect_object = pgrm.find('video').find('aspect')
            if aspect_object is not None:
                num = float(aspect_object.text.split(':')[0])
                den = float(aspect_object.text.split(':')[1])
                aspect = num / den

            year_object = pgrm.find('date')
            if year_object is not None:
                year = int(year_object.text)

            rating_object = pgrm.find('star-rating')
            if rating_object is not None:
                rating_object = rating_object.find('value')
                if rating_object is not None:
                    rating = float(rating_object.text.split(
                        '/')[0]) * 2.0

            length_object = pgrm.find('length')
            if length_object is not None:
                if length_object.get('units') == 'minutes':
                    duration = int(length_object.text) * 60
                elif length_object.get('units') == 'hours':
                    duration = int(length_object.text) * 3600

            credits_object = pgrm.find('credits')
            if credits_object is not None:
                for credit in credits_object.findall('actor'):
                    cast.append(credit.text)
                for credit in credits_object.findall('writer'):
                    if writer is not None:
                        writer = writer + ' - ' + credit.text
                    else:
                        writer = credit.text
                for credit in credits_object.findall('presenter'):
                    cast.append(credit.text)
                for credit in credits_object.findall('director'):
                    if director is not None:
                        director = director + ' - ' + credit.text
                    else:
                        director = credit.text
                for credit in credits_object.findall('composer'):
                    cast.append(credit.text)

            episode_num_object = pgrm.find('episode-num')
            if episode_num_object is not None:
                season_s = episode_num_object.text.split('.')[0]
                if season_s != '':
                    season = int(season_s) + 1
                episode_s = episode_num_object.text.split('.')[1]
                if episode_s != '':
                    episode = int(episode_s) + 1

        # Else, just get the title form skeleton.py
        else:
            try:
                title = common.GETTEXT(skeleton.LABELS[params.module_name])
            except Exception:
                title = skeleton.LABELS[params.module_name]

        info = {
            'video': {
                'title': title,
                'plot': plot,
                # 'aired': aired,
                # 'date': date,
                'duration': duration,
                'year': year,
                'rating': rating,
                'cast': cast,
                'director': director,
                'writer': writer,
                'plotoutline': plotoutline,
                'episode': episode,
                'season': season
            }
        }

        stream_info = {
            'video': {
                'aspect': aspect
            }
        }

        # If the channel has multiples streams like France TV Sport
        is_playable = True
        if XMLTV_CHANNEL_ID[params.module_name] == 'multiple_streams':
            is_playable = False

        if icon is None or \
                icon == 'http://television.telerama.fr/':
            item_path_media = list(channel_path)
            item_path_media.pop()
            item_path_media.append(channel_name)
            media_item_path = common.sp.xbmc.translatePath(
                common.sp.os.path.join(
                    common.MEDIA_PATH,
                    *(item_path_media)
                )
            )

            media_item_path = media_item_path.decode(
                "utf-8").encode(common.FILESYSTEM_CODING)
            icon = media_item_path + '.png'

        listing.append({
            'label': title,
            'fanart': image,
            'thumb': icon,
            'url': common.PLUGIN.get_url(
                module_path=params.module_path,
                module_name=params.module_name,
                action='start_live_tv_stream'
            ),
            'is_playable': is_playable,
            'context_menu': context_menu,
            'info': info,
            'stream_info': stream_info,
        })

    return common.PLUGIN.create_listing(
        listing,
        sort_methods=(
            common.sp.xbmcplugin.SORT_METHOD_UNSORTED,
            common.sp.xbmcplugin.SORT_METHOD_LABEL
        ),
        category=common.get_window_title(),
        content='tvshows'
    )







