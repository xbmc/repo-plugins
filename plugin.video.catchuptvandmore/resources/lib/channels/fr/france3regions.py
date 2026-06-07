# -*- coding: utf-8 -*-
# Copyright: (c) JUL1EN094, SPM, SylvainCecchetto
# Copyright: (c) 2016, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import json
import re
import xml.etree.ElementTree as ET

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

URL_EMISSIONS = URL_ROOT + '/%s/programmes'

GENERIC_HEADERS = {'User-Agent': web_utils.get_random_windows_ua()}

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
    resp = urlquick.get(URL_PROGRAMMES)
    root = resp.parse()

    for programs_datas in root.iterfind(".//li[@class='program_home__regionList__item']"):
        program_title = programs_datas.find('.//span').text.strip()
        program_url = programs_datas.find('.//a').get('href')
        if 'http' in programs_datas.find('.//img').get('src'):
            program_img = programs_datas.find('.//img').get('src')
        else:
            program_img = URL_ROOT + programs_datas.find('.//img').get('src')

        item = Listitem()
        item.label = program_title
        item.art['thumb'] = item.art['landscape'] = program_img
        item.set_callback(list_regions,
                          item_id=item_id,
                          program_url=program_url)
        item_post_treatment(item)
        yield item


@Route.register
def list_regions(plugin, item_id, program_url, **kwargs):
    """
    Build categories listing
    - Tous les programmes
    - Séries
    - Informations
    - ...
    """
    # region = utils.ensure_unicode(Script.setting['france3regions.language'])
    # region = LIVE_FR3_REGIONS[region]
    # resp = urlquick.get(URL_EMISSIONS % region)
    resp = urlquick.get(program_url)
    root = resp.parse()

    for program_datas in root.iterfind(".//div[@class='slider ']"):
        program_title = program_datas.find('.//h2').text.strip()
        program_id = program_datas.find('.//h2').get('id')

        item = Listitem()
        item.label = program_title
        item.set_callback(list_categories,
                          item_id=item_id,
                          program_url=program_url,
                          program_id=program_id)
        item_post_treatment(item)
        yield item


@Route.register
def list_categories(plugin, item_id, program_url, program_id, **kwargs):
    resp = urlquick.get(program_url)
    root = resp.parse()

    for programs_datas in root.iterfind(".//div[@class='slider ']"):
        if program_id == programs_datas.find('.//h2').get('id'):
            for video_datas in programs_datas.iterfind(".//li"):
                categories_url = video_datas.find('.//a').get('href')
                if len(categories_url) == 0:
                    continue
                diffusion_id = URL_ROOT + categories_url
                if video_datas.find('.//span') is not None:
                    video_title = video_datas.find('.//span').text.strip()
                else:
                    video_title = video_datas.find(".//div[2][@class='slider__programs__video__title--program']")

                video_image = ''
                if video_datas.find('.//img') is not None:
                    if 'http' in video_datas.find('.//img').get('data-src'):
                        video_image = video_datas.find('.//img').get('data-src')
                    else:
                        video_image = URL_ROOT + video_datas.find('.//img').get('data-src')

                item = Listitem()
                item.label = video_title
                item.art['thumb'] = item.art['landscape'] = video_image
                item.set_callback(list_videos,
                                  item_id=item_id,
                                  diffusion_id=diffusion_id)
                item_post_treatment(item, is_playable=True, is_downloadable=True)
                yield item


@Route.register
def list_videos(plugin, item_id, diffusion_id, **kwargs):
    resp = urlquick.get(diffusion_id, headers=GENERIC_HEADERS, max_age=-1)
    # root = resp.parse()
    try:
        root = resp.parse("div", attrs={"class": "content__header"})
    except RuntimeError:
        yield None
        return

    if root is not None:
        diffusion_id = diffusion_id
        program_title = root.find('.//div[@class="content__header__data__text__description"]').text.strip()
        program_image = root.find('.//img').get('src')
        duration_tag = ET.tostring(root, encoding='utf-8').decode()
        program_duration = re.findall(r'.* (\d+?) min', duration_tag)[0]

        item = Listitem()
        item.label = program_title
        item.art['thumb'] = item.art['landscape'] = program_image
        if len(program_duration) > 0:
            item.info['duration'] = program_duration
        item.set_callback(get_video_url,
                          item_id=item_id,
                          diffusion_id=diffusion_id)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item

    try:
        root = resp.parse("div", attrs={"class": "content__replays"})
    except RuntimeError:
        yield None
        return

    if root.find(".//li[@class='program_list__list__item']") is not None:
        for programs_datas in root.iterfind(".//li[@class='program_list__list__item']"):
            program_title = programs_datas.find('.//a').get('alt').strip()
            if 'http' in programs_datas.find('.//a').get('href'):
                diffusion_id = programs_datas.find('.//a').get('href')
            else:
                diffusion_id = URL_ROOT + programs_datas.find('.//a').get('href')

            if 'http' in programs_datas.find('.//img').get('data-src'):
                program_image = programs_datas.find('.//img').get('data-src')
            else:
                program_image = URL_ROOT + programs_datas.find('.//img').get('data-src')

            duration_tag = programs_datas.find('.//div[@class="program_list__list__item__data__diffusion"]').text.strip()
            program_duration = re.findall(r'.* (\d+?)min', duration_tag)[0]

            item = Listitem()
            item.label = program_title
            item.art['thumb'] = item.art['landscape'] = program_image
            if len(program_duration) > 0:
                item.info['duration'] = program_duration
            item.set_callback(get_video_url,
                              item_id=item_id,
                              diffusion_id=diffusion_id)
            item_post_treatment(item, is_playable=True, is_downloadable=True)
            yield item

    if root.find(".//li[@class='program_list__list__item hidden']") is not None:
        for programs_datas in root.iterfind(".//li[@class='program_list__list__item hidden']"):
            program_title = programs_datas.find('.//a').get('alt').strip()
            if 'http' in programs_datas.find('.//a').get('href'):
                diffusion_id = programs_datas.find('.//a').get('href')
            else:
                diffusion_id = URL_ROOT + programs_datas.find('.//a').get('href')

            if 'http' in programs_datas.find('.//img').get('data-src'):
                program_image = programs_datas.find('.//img').get('data-src')
            else:
                program_image = URL_ROOT + programs_datas.find('.//img').get('data-src')

            duration_tag = programs_datas.find('.//div[@class="program_list__list__item__data__diffusion"]').text.strip()
            program_duration = re.findall(r'.* (\d+?)min', duration_tag)[0]

            item = Listitem()
            item.label = program_title
            item.art['thumb'] = item.art['landscape'] = program_image
            if len(program_duration) > 0:
                item.info['duration'] = program_duration
            item.set_callback(get_video_url,
                              item_id=item_id,
                              diffusion_id=diffusion_id)
            item_post_treatment(item, is_playable=True, is_downloadable=True)
            yield item


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  diffusion_id,
                  download_mode=False,
                  **kwargs):
    resp = urlquick.get(diffusion_id, headers=GENERIC_HEADERS, max_age=-1)
    root = resp.parse()
    video_id = root.find('.//figure[@class="magneto"]').get('data-id')

    return resolver_proxy.get_francetv_video_stream(plugin, video_id,
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
        if old.find('.//img') is not None:
            place = re.compile(r'France 3 (.*?)$').findall(old.find('.//img').get('alt'))[0]
            region.append(place)

    if len(region) > 1:
        choice = url_region[xbmcgui.Dialog().select(Script.localize(30182), region)]
    else:
        choice = url_region[0]

    resp = urlquick.get(choice, headers=GENERIC_HEADERS, max_age=-1)
    root = resp.parse()
    video_id = root.find('.//figure[@class="magneto"]').get('data-id')

    return resolver_proxy.get_francetv_live_stream(plugin, broadcast_id=video_id)
