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

# The unicode_literals import only has
# an effect on Python 2.
# It makes string literals as unicode like in Python 3
from __future__ import unicode_literals

from codequick import Route, Resolver, Listitem, utils, Script

from resources.lib.labels import LABELS
from resources.lib import web_utils
from resources.lib import resolver_proxy
import resources.lib.cq_utils as cqu

import json
import urlquick


'''
Channels:
    * La 1ère (JT, Météo, Live TV)

TO DO: Add Emissions

'''

URL_ROOT = 'http://la1ere.francetvinfo.fr'

URL_LIVES_JSON = URL_ROOT + '/webservices/mobile/live.json'

URL_JT_JSON = URL_ROOT + '/webservices/mobile/newscast.json?region=%s'
# region


LIVE_LA1ERE_REGIONS = {
    # New values
    "Guadeloupe": "guadeloupe",
    "Guyane": "guyane",
    "Martinique": "martinique",
    "Mayotte": "mayotte",
    "Nouvelle Calédonie": "nouvellecaledonie",
    "Polynésie": "polynesie",
    "Réunion": "reunion",
    "St-Pierre et Miquelon": "saintpierremiquelon",
    "Wallis et Futuna": "wallisfutuna",
    "Outre-mer": "1ere",
    # Fix possible bug after names changed (not used anymore)
    # "Guadeloupe 1ère": "guadeloupe",
    # "Guyane 1ère": "guyane",
    # "Martinique 1ère": "martinique",
    # "Mayotte 1ère": "mayotte",
    # "Nouvelle Calédonie 1ère": "nouvellecaledonie",
    # "Polynésie 1ère": "polynesie",
    # "Réunion 1ère": "reunion",
    # "St-Pierre et Miquelon 1ère": "saintpierremiquelon",
    # "Wallis et Futuna 1ère": "wallisfutuna"
}

CORRECT_MONTH = {
    'Janvier': '01',
    'Février': '02',
    'Mars': '03',
    'Avril': '04',
    'Mai': '05',
    'Juin': '06',
    'Juillet': '07',
    'Août': '08',
    'Septembre': '09',
    'Octobre': '10',
    'Novembre': '11',
    'Décembre': '12'
}


def replay_entry(plugin, item_id):
    """
    First executed function after replay_bridge
    """
    return list_programs(plugin, item_id)


@Route.register
def list_programs(plugin, item_id):
    """
    Build categories listing
    - Tous les programmes
    - Séries
    - Informations
    - ...
    """
    region = utils.ensure_unicode(Script.setting['la_1ere.region'])
    region = LIVE_LA1ERE_REGIONS[region]
    resp = urlquick.get(URL_JT_JSON % region)
    json_parser = json.loads(resp.text).keys()

    for list_jt_name in json_parser:
        if list_jt_name != 'mea':
            item = Listitem()
            item.label = list_jt_name
            item.set_callback(
                list_videos,
                item_id=item_id,
                list_jt_name=list_jt_name)
            yield item


@Route.register
def list_videos(plugin, item_id, list_jt_name):

    region = utils.ensure_unicode(Script.setting['la_1ere.region'])
    region = LIVE_LA1ERE_REGIONS[region]
    resp = urlquick.get(URL_JT_JSON % region)
    json_parser = json.loads(resp.text)

    for video_datas in json_parser[list_jt_name]:
        video_title = video_datas["titre"] + ' - ' + video_datas["date"]
        video_image = video_datas["url_image"]
        id_diffusion = video_datas["id"]
        date_value = video_datas["date"].split(' ')
        day = date_value[1]
        try:
            month = CORRECT_MONTH[date_value[2]]
        except Exception:
            month = '00'
        year = date_value[3]
        date_value = '-'.join((year, month, day))

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = video_image
        item.info.date(date_value, '%Y-%m-%d')

        item.context.script(
            get_video_url,
            plugin.localize(LABELS['Download']),
            item_id=item_id,
            id_diffusion=id_diffusion,
            video_label=LABELS[item_id] + ' - ' + item.label,
            download_mode=True)

        item.set_callback(
            get_video_url,
            item_id=item_id,
            id_diffusion=id_diffusion,
            item_dict=cqu.item2dict(item))
        yield item


@Resolver.register
def get_video_url(
        plugin, item_id, id_diffusion, item_dict=None, download_mode=False, video_label=None):

    return resolver_proxy.get_francetv_video_stream(
        plugin, id_diffusion, item_dict, download_mode, video_label)


def live_entry(plugin, item_id, item_dict):
    return get_live_url(plugin, item_id, item_id.upper(), item_dict)


@Resolver.register
def get_live_url(plugin, item_id, video_id, item_dict):

    resp = urlquick.get(
        URL_LIVES_JSON,
        headers={'User-Agent': web_utils.get_random_ua},
        max_age=-1)
    json_parser = json.loads(resp.text)

    region = utils.ensure_unicode(Script.setting['la_1ere.region'])
    id_sivideo = json_parser[LIVE_LA1ERE_REGIONS[region]]["id_sivideo"]
    return resolver_proxy.get_francetv_live_stream(
        plugin, id_sivideo.split('@')[0])
