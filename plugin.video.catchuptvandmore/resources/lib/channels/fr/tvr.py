# -*- coding: utf-8 -*-
# Copyright: (c) 2019, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import re
from builtins import str
import json

from codequick import Listitem, Resolver, Route, Script
import urlquick
from kodi_six import xbmcgui
from resources.lib.addon_utils import Quality

from resources.lib import resolver_proxy, web_utils
from resources.lib.menu_utils import item_post_treatment


# TODO
# Add Replay

URL_ROOT = "https://www.tvr.bzh"

URL_LIVE = URL_ROOT + '/direct'

URL_REPLAY = URL_ROOT + '/replay/%s'

GENERIC_HEADERS = {"User-Agent": web_utils.get_random_ua()}

URL_VIDEO = 'https://www.ultimedia.com/deliver/video?video=%s&topic=generic'


CATEGORIES_EDUCATION = {
    'Culture': URL_REPLAY % 'culture',
    'Divertissement': URL_REPLAY % 'divertissement',
    'Documentaire-Fiction': URL_REPLAY % 'documentaire-fiction',
    'Economie': URL_REPLAY % 'economie',
    'Infos': URL_REPLAY % 'infos',
    'Langues régionales': URL_REPLAY % 'langues-régionales',
    'Musique': URL_REPLAY % 'musique',
    'Portraits et rencontres': URL_REPLAY % 'portraits-et-rencontres',
    'Reportages': URL_REPLAY % 'reportages',
    'Sport': URL_REPLAY % 'sport',
}


@Route.register
def list_categories(plugin, item_id, **kwargs):
    """
    Build categories listing
    - Tous les programmes
    - Séries
    - Informations
    - ...
    """
    for category_title, category_url in list(CATEGORIES_EDUCATION.items()):

        item = Listitem()
        item.label = category_title
        item.set_callback(list_contents,
                          item_id=item_id,
                          category_url=category_url,
                          page='1')
        item_post_treatment(item)
        yield item


@Route.register
def list_contents(plugin, item_id, category_url, page, **kwargs):
    """
    Build programs listing
    - Les feux de l'amour
    - ...
    """
    resp = urlquick.get(category_url + '?p=%s' % page, headers=GENERIC_HEADERS, max_age=-1)
    root = resp.parse()

    for program_datas in root.iterfind(".//div[@class='c-card c-card--link c-card--fav']"):

        program_title = program_datas.find(".//span[@class='c-card__title']").text
        program_image = URL_ROOT + program_datas.find(".//img").get('data-src')
        program_url = URL_ROOT + program_datas.find(".//a").get('href')
        program_info = program_datas.find(".//span[@class='c-card__text']").text

        item = Listitem()
        item.label = program_title
        item.art['thumb'] = item.art['landscape'] = program_image
        item.info['plot'] = program_info
        item.set_callback(get_video_url, item_id=item_id, next_url=program_url)
        item_post_treatment(item)
        yield item

    yield Listitem.next_page(item_id=item_id, category_url=category_url, page=str(int(page) + 1))


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  next_url,
                  download_mode=False,
                  **kwargs):

    resp = urlquick.get(next_url, headers=GENERIC_HEADERS, max_age=-1)
    for possibility in resp.parse().findall('.//iframe'):
        if possibility.get('allowfullscreen'):
            final_page = 'https:' + possibility.get('src')

    resp2 = urlquick.get(final_page, headers=GENERIC_HEADERS, max_age=-1)
    video_id = re.compile(r'video\":{\"id\":\"(.*?)\"').findall(resp2.text)

    resp3 = urlquick.get(URL_VIDEO % video_id, headers=GENERIC_HEADERS, max_age=-1)
    json_parser = json.loads(resp3.text)

    urls = []
    definition = []
    for source in json_parser['jwconf']['playlist'][0]['sources']:
        urls.append(source['file'])
        definition.append(source.get('label').replace('mp4_', '') + 'p')

    quality = Script.setting.get_string('quality')
    if quality == Quality['WORST']:
        video_url = urls[len(urls) - 1]
    elif quality == Quality['BEST'] or quality == Quality['DEFAULT']:
        video_url = urls[0]
    else:
        video_url = urls[xbmcgui.Dialog().select(Script.localize(30180), definition)]

    return video_url


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_LIVE, headers={"User-Agent": web_utils.get_random_ua()}, max_age=-1)
    video_url = re.compile(r'data-source\=\"(.*?)\"').findall(resp.text)[0]

    return resolver_proxy.get_stream_with_quality(plugin, video_url, manifest_type="hls")
