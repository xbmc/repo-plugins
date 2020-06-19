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


from resources.lib import web_utils
from resources.lib import resolver_proxy
from resources.lib.menu_utils import item_post_treatment
from resources.lib.kodi_utils import get_selected_item_art, get_selected_item_label, get_selected_item_info

import json
import re
import urlquick
'''
Channels:
    * La 1ère (JT, Météo, Live TV)

TO DO: Add Emissions

'''

URL_ROOT = 'http://la1ere.francetvinfo.fr'

URL_LIVES_JSON = URL_ROOT + '/webservices/mobile/live.json'

URL_EMISSIONS = URL_ROOT + '/%s/emissions'
# region

LIVE_LA1ERE_REGIONS = {
    "Guadeloupe": "guadeloupe",
    "Guyane": "guyane",
    "Martinique": "martinique",
    "Mayotte": "mayotte",
    "Nouvelle Calédonie": "nouvellecaledonie",
    "Polynésie": "polynesie",
    "Réunion": "reunion",
    "St-Pierre et Miquelon": "saintpierremiquelon",
    "Wallis et Futuna": "wallisfutuna",
    "Outre-mer": ""
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


def replay_entry(plugin, item_id, **kwargs):
    """
    First executed function after replay_bridge
    """
    return list_programs(plugin, item_id)


@Route.register
def list_programs(plugin, item_id, **kwargs):
    """
    Build categories listing
    - Tous les programmes
    - Séries
    - Informations
    - ...
    """
    region = utils.ensure_unicode(Script.setting['la_1ere.language'])
    region = LIVE_LA1ERE_REGIONS[region]
    resp = urlquick.get(URL_EMISSIONS % region)
    root = resp.parse()

    for program_datas in root.iterfind(".//div[@class='block-fr3-content']"):
        program_title = program_datas.find('.//a').get('title')
        program_image = ''
        if program_datas.find('.//img') is not None:
            program_image = program_datas.find('.//img').get('src')
        if 'http' in program_datas.find('.//a').get('href'):
            program_url = program_datas.find('.//a').get('href')
        else:
            program_url = URL_ROOT + program_datas.find('.//a').get('href')

        item = Listitem()
        item.label = program_title
        item.art['thumb'] = item.art['landscape'] = program_image
        item.set_callback(list_videos,
                          item_id=item_id,
                          program_url=program_url)
        item_post_treatment(item)
        yield item


@Route.register
def list_videos(plugin, item_id, program_url, **kwargs):

    resp = urlquick.get(program_url)
    root = resp.parse()

    for video_datas in root.iterfind(".//a[@class='video_mosaic']"):
        video_title = video_datas.get('title')
        video_plot = video_datas.get('description')
        video_image = video_datas.find('.//img').get('src')
        id_diffusion = re.compile(r'video\/(.*?)\@Regions').findall(
            video_datas.get('href'))[0]
        video_duration = 0
        if video_datas.find(".//p[@class='length']").text is not None:
            duration_values = video_datas.find(
                ".//p[@class='length']").text.split(' : ')[1].split(':')
            video_duration = int(duration_values[0]) * 3600 + int(
                duration_values[1]) * 60 + int(duration_values[2])

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = item.art['landscape'] = video_image
        item.info['plot'] = video_plot
        item.info['duration'] = video_duration

        date_value = ''
        if video_datas.find(".//p[@class='date']").text is not None:
            date_value = video_datas.find(".//p[@class='date']").text.split(
                ' : ')[1]
            item.info.date(date_value, '%d/%m/%Y')

        item.set_callback(get_video_url,
                          item_id=item_id,
                          id_diffusion=id_diffusion)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  id_diffusion,
                  download_mode=False,
                  **kwargs):

    return resolver_proxy.get_francetv_video_stream(plugin, id_diffusion,
                                                    download_mode)


def live_entry(plugin, item_id, **kwargs):
    return get_live_url(plugin, item_id, item_id.upper())


@Resolver.register
def get_live_url(plugin, item_id, video_id, **kwargs):
    final_region = kwargs.get('language', Script.setting['la_1ere.language'])

    resp = urlquick.get(URL_LIVES_JSON,
                        headers={'User-Agent': web_utils.get_random_ua()},
                        max_age=-1)
    json_parser = json.loads(resp.text)

    region = utils.ensure_unicode(final_region)
    id_sivideo = json_parser[LIVE_LA1ERE_REGIONS[region]]["id_sivideo"]
    return resolver_proxy.get_francetv_live_stream(plugin,
                                                   id_sivideo.split('@')[0])
