# -*- coding: utf-8 -*-
# Copyright: (c) JUL1EN094, SPM, SylvainCecchetto
# Copyright: (c) 2016, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import json
import re

# noinspection PyUnresolvedReferences
from codequick import Listitem, Resolver, Route, Script, utils
import urlquick

from resources.lib import resolver_proxy, web_utils
from resources.lib.menu_utils import item_post_treatment

# Channels:
#     * La 1ère (JT, Météo, Live TV)
# TODO: Add Emissions


URL_ROOT = 'https://la1ere.francetvinfo.fr'

URL_LIVE = 'https://www.france.tv/la1ere/%s/direct.html'

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


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    final_region = LIVE_LA1ERE_REGIONS[utils.ensure_unicode(Script.setting['la_1ere.language'])]
    resp = urlquick.get(URL_LIVE % final_region, headers={'User-Agent': web_utils.get_random_ua()}, max_age=-1)
    broadcast_id = re.compile(r'videoId\"\:\"(.*?)\"', re.DOTALL).findall(resp.text)[0]

    return resolver_proxy.get_francetv_live_stream(plugin, broadcast_id)
