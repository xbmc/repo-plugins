# -*- coding: utf-8 -*-
# Copyright: (c) JUL1EN094, SPM, SylvainCecchetto
# Copyright: (c) 2016, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import json
import re

from kodi_six import xbmcgui
from codequick import Listitem, Resolver, Route, Script, utils
import urlquick

from resources.lib import resolver_proxy, web_utils
from resources.lib.menu_utils import item_post_treatment

# Channels:
#     * France 3 Régions (JT, Météo, Live TV)
# TODO: Add Emissions

URL_ROOT = 'https://france3-regions.francetvinfo.fr'

URL_PROGRAMMES = URL_ROOT + '/programmes'

URL_EMISSIONS = URL_ROOT + '/%s/emissions'

GENERIC_HEADERS = {'User-Agent': web_utils.get_random_ua()}

LIVE_FR3_REGIONS = {
    "Alpes": "alpes",
    "Alsace": "alsace",
    "Aquitaine": "aquitaine",
    "Auvergne": "auvergne",
    "Basse-Normandie": "basse-normandie",
    "Bourgogne": "bourgogne",
    "Bretagne": "bretagne",
    "Centre-Val de Loire": "centre",
    "Chapagne-Ardenne": "champagne-ardenne",
    "Corse": "corse",
    "Côte d'Azur": "cote-d-azur",
    "Franche-Comté": "franche-comte",
    "Haute-Normandie": "haute-normandie",
    "Languedoc-Roussillon": "languedoc-roussillon",
    "Limousin": "limousin",
    "Lorraine": "lorraine",
    "Midi-Pyrénées": "midi-pyrenees",
    "Nord-Pas-de-Calais": "nord-pas-de-calais",
    "Paris Île-de-France": "paris-ile-de-france",
    "Pays de la Loire": "pays-de-la-loire",
    "Picardie": "picardie",
    "Poitou-Charentes": "poitou-charentes",
    "Provence-Alpes": "provence-alpes",
    "Rhône-Alpes": "rhone-alpes",
    "Nouvelle-Aquitaine": "nouvelle-aquitaine"
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
    region = utils.ensure_unicode(Script.setting['france3regions.language'])
    region = LIVE_FR3_REGIONS[region]
    resp = urlquick.get(URL_EMISSIONS % region)
    root = resp.parse()

    for program_datas in root.iterfind(
            ".//div[@class='little-column-style--content col-sm-6 col-md-4 mobile-toggler-replace']"
    ):
        program_title = program_datas.find('.//h2').text
        program_plot = program_datas.find(
            ".//div[@class='column-style--text hidden-xs']").text
        program_image = program_datas.find('.//img').get('data-srcset')
        program_url = program_datas.find('.//a').get('href')

        item = Listitem()
        item.label = program_title
        item.art['thumb'] = item.art['landscape'] = program_image
        item.info['plot'] = program_plot
        item.set_callback(list_videos,
                          item_id=item_id,
                          program_url=program_url)
        item_post_treatment(item)
        yield item


@Route.register
def list_videos(plugin, item_id, program_url, **kwargs):

    resp = urlquick.get(program_url)
    root = resp.parse()

    for video_datas in root.iterfind(
            ".//a[@class='slider-inline-style--content video_mosaic']"):
        video_title = video_datas.get('title')
        video_plot = video_datas.get('description')
        if video_datas.find('.//img').get('data-srcset'):
            video_image = video_datas.find('.//img').get('data-srcset')
        else:
            video_image = video_datas.find('.//img').get('src')
        id_diffusion = re.compile(r'video\/(.*?)\@Regions').findall(
            video_datas.get('href'))[0]

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = item.art['landscape'] = video_image
        item.info['plot'] = video_plot

        date_value = ''
        if video_datas.find(
                ".//p[@class='slider-inline-style--text text-light m-t-0']"
        ).text is not None:
            date_value = video_datas.find(
                ".//p[@class='slider-inline-style--text text-light m-t-0']"
            ).text.split(' du ')[1]
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
    resp = urlquick.get(URL_PROGRAMMES, headers=GENERIC_HEADERS, max_age=-1)
    root = resp.parse()
    region = []
    url_region = []
    for place in root.iterfind(".//li[@class='program_home__regionList__item']"):
        available_region = place.find('.//a').get('href')
        url_region.append(available_region)
        region.append(place.find('.//span').text.strip())

    choice = url_region[xbmcgui.Dialog().select(Script.localize(30158), region)]
    resp = urlquick.get(choice, headers=GENERIC_HEADERS, max_age=-1)
    root = resp.parse()

    region = []
    url_region = []
    for old in root.iterfind(".//li[@class='direct-item ']"):
        url_region.append(URL_ROOT + old.find(".//a").get('href'))
        place = re.compile(r'France 3 (.*?)$').findall(old.find('.//img').get('alt'))[0]
        region.append(place)

    if len(region) > 1:
        choice = url_region[xbmcgui.Dialog().select(Script.localize(30182), region)]
    else:
        choice = url_region[0]

    resp = urlquick.get(choice, headers=GENERIC_HEADERS, max_age=-1)
    root = resp.parse()
    video_id = root.find('.//div[@class="magneto"]').get('data-id')

    return resolver_proxy.get_francetv_live_stream(plugin, broadcast_id=video_id)
