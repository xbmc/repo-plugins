# -*- coding: utf-8 -*-
# Copyright: (c) 2017, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals

import json
import re
from builtins import str

try:
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode

import urlquick
# noinspection PyUnresolvedReferences
from codequick import Listitem, Resolver, Route, Script
from resources.lib import download, web_utils, resolver_proxy
from resources.lib.menu_utils import item_post_treatment

# TODO Rework filter for all videos

URL_TV5MONDE_LIVE = 'http://live.tv5monde.com/'

URL_TV5MONDE_ROOT = 'https://www.tv5monde.com'

URL_TV5MONDE_API = 'https://api.tv5monde.com/player/asset/%s/resolve?condenseKS=true'
M3U8_NOT_FBS = 'https://ott.tv5monde.com/Content/HLS/Live/channel(europe)/variant.m3u8'

URL_LICENCE_KEY = '%s|Content-Type=&User-Agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0|R{SSM}|'

LIST_LIVE_TV5MONDE = {'tv5mondefbs': 'fbs', 'tv5mondeinfo': 'infoplus'}

LIVETYPE = {
    "FBS": "0",
    "NOT_FBS": "1"
}

GENERIC_HEADERS = {
    'User-Agent': web_utils.get_random_windows_ua(),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3',
    'Connection': 'keep-alive',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Sec-GPC': '1',
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
    resp = urlquick.get(URL_TV5MONDE_ROOT + '/tv',
                        headers=GENERIC_HEADERS,
                        max_age=-1)

    root = resp.parse("footer", attrs={"role": "footer-content"})
    for category_datas in root.iterfind(".//li"):
        category_title = category_datas.find('.//a').text.strip()
        category_url = URL_TV5MONDE_ROOT + category_datas.find('.//a').get('href')

        item = Listitem()
        item.label = category_title
        item.set_callback(list_programs,
                          item_id=item_id,
                          category_url=category_url,
                          page='1')
        item_post_treatment(item)
        yield item


@Route.register
def list_programs(plugin, item_id, category_url, page, **kwargs):
    """
    Build programs listing
    - Les feux de l'amour
    - ...
    """
    resp = urlquick.get(category_url + '?page=%s' % page,
                        headers=GENERIC_HEADERS,
                        max_age=-1)

    root = resp.parse("main", attrs={"role": "main-content"})
    for program_datas in root.iterfind(".//li"):
        if 'http' in program_datas.find('.//a').get('href'):
            program_url = program_datas.find('.//a').get('href')
        else:
            program_url = URL_TV5MONDE_ROOT + program_datas.find('.//a').get('href')
        try:
            if 'http' in program_datas.find('.//img').get('src'):
                program_title = program_datas.find('.//img').get('alt')
                program_image = program_datas.find('.//img').get('src')
            else:
                program_title = program_datas.find('.//img').get('alt')
                program_image = URL_TV5MONDE_ROOT + program_datas.find('.//img').get('src')
        except Exception:
            continue

        if program_datas.find('.//p[@class="thumbnail-titre-fiche-mere"]') is not None:
            program_title = program_datas.find('.//p[@class="thumbnail-titre-fiche-mere"]').text.strip()

        item = Listitem()
        item.label = program_title
        item.art['thumb'] = item.art['landscape'] = item.art["fanart"] = program_image
        item.set_callback(list_videos,
                          item_id=item_id,
                          program_url=program_url,
                          page='1')
        item_post_treatment(item)
        yield item

    yield Listitem.next_page(item_id=item_id,
                             category_url=category_url,
                             page=str(int(page) + 1))


@Route.register
def list_videos(plugin, item_id, program_url, page, **kwargs):
    resp = urlquick.get(program_url + '?page=%s' % page,
                        headers=GENERIC_HEADERS,
                        max_age=-1)
    root = resp.parse("main", attrs={"role": "main-content"})
    if root.findall(".//div[@class='video-wrapper']"):
        video_plot = video_image = ''
        video_title = root.find(".//h1").text.strip()
        if root.find('.//p[@class="text"]') is not None:
            video_plot = root.find('.//p[@class="text"]').text.strip()
            video_image = root.find('.//div[@class="video_player_loader"]').get('data-image')

        item = Listitem()
        item.label = video_title
        if len(video_image) > 0:
            item.art['thumb'] = item.art['landscape'] = item.art["fanart"] = video_image
        if len(video_plot) > 0:
            item.info['plot'] = video_plot
        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_url=program_url)
        yield item
        return

    for video_datas in root.iterfind(".//li"):
        if 'http' in video_datas.find('.//a').get('href'):
            video_url = video_datas.find('.//a').get('href')
        else:
            video_url = URL_TV5MONDE_ROOT + video_datas.find('.//a').get('href')
        try:
            if 'http' in video_datas.find('.//img').get('src'):
                video_title = video_datas.find('.//img').get('alt')
                video_image = video_datas.find('.//img').get('src')
            else:
                video_title = video_datas.find('.//img').get('alt')
                video_image = URL_TV5MONDE_ROOT + video_datas.find('.//img').get('src')
        except Exception:
            continue

        video_title2 = video_plot = ''
        if video_datas.find('.//p[@class="thumbnail-titre-episode"]') is not None:
            video_title2 = video_datas.find('.//p[@class="thumbnail-titre-episode"]').text.strip()
        if video_datas.find('.//p[@class="thumbnail-description thumbnail-resume-court"]') is not None:
            video_plot = video_datas.find('.//p[@class="thumbnail-description thumbnail-resume-court"]').text.strip()

        item = Listitem()
        if len(video_title2) == 0:
            item.label = video_title
        else:
            item.label = video_title + ' - ' + video_title2
        if len(video_plot) > 0:
            item.info['plot'] = video_plot
        item.art['thumb'] = item.art['landscape'] = item.art["fanart"] = video_image
        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_url=video_url)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item

    yield Listitem.next_page(item_id=item_id,
                             program_url=program_url,
                             page=str(int(page) + 1))


@Route.register
def list_videos_category(plugin, item_id, page, **kwargs):
    resp = urlquick.get(URL_TV5MONDE_ROOT +
                        '/toutes-les-videos?page=%s' % page,
                        headers=GENERIC_HEADERS,
                        max_age=-1)
    root = resp.parse()
    for video_datas in root.iterfind(".//div[@class='bloc-episode-content']"):
        if video_datas.find('.//h3') is not None:
            video_title = video_datas.find('.//h2').text.strip() + ' - ' + video_datas.find('.//h3').text.strip()
        else:
            video_title = video_datas.find('.//h2').text.strip()
        if 'http' in video_datas.find('.//img').get('src'):
            video_image = video_datas.find('.//img').get('src')
        else:
            video_image = URL_TV5MONDE_ROOT + video_datas.find('.//img').get('src')
        video_url = URL_TV5MONDE_ROOT + video_datas.find('.//a').get('href')

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = item.art['landscape'] = video_image
        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_url=video_url)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item

    yield Listitem.next_page(item_id=item_id,
                             page=str(int(page) + 1))


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_url,
                  download_mode=False,
                  **kwargs):
    resp = urlquick.get(video_url, headers=GENERIC_HEADERS, max_age=-1)
    video_json = re.compile('data-broadcast=\'(.*?)\'').findall(resp.text)[0]
    json_parser = json.loads(video_json)
    try:
        api_url = json_parser["files"][0]["url"]
        api_token = json_parser["files"][0]["token"]
    except Exception:
        api_url = json_parser[0]["url"]
        api_token = json_parser[0]["token"]

    headers = GENERIC_HEADERS.copy()
    headers.update({'Authorization': 'Bearer ' + api_token})
    resp = urlquick.get(URL_TV5MONDE_API % api_url,
                        headers=headers,
                        max_age=-1)

    json_parser = resp.json()

    final_video_url = None
    license_url = license_key = None
    for video_datas in json_parser:
        if 'dash' in video_datas['type']:
            final_video_url = video_datas['url']
            if 'drm' in video_datas:
                license_url = video_datas['drm']['keySystems']['widevine']['license']
            break

    if license_url is not None:
        license_key = URL_LICENCE_KEY % license_url
    else:
        license_key = None

    return resolver_proxy.get_stream_with_quality(
        plugin, video_url=final_video_url, manifest_type='mpd',
        license_url=license_key)


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    region = Script.setting['tv5monde.region']
    if region == LIVETYPE['NOT_FBS']:
        return resolver_proxy.get_stream_with_quality(plugin, video_url=M3U8_NOT_FBS, manifest_type="hls")

    live_id = ''
    for channel_name, live_id_value in list(LIST_LIVE_TV5MONDE.items()):
        if item_id == channel_name:
            live_id = live_id_value
    resp = urlquick.get(URL_TV5MONDE_LIVE + '%s.html' % live_id,
                        headers=GENERIC_HEADERS,
                        max_age=-1)
    live_json = re.compile(r'data-broadcast=\'(.*?)\'').findall(resp.text)[0]
    json_parser = json.loads(live_json)

    return resolver_proxy.get_stream_with_quality(plugin, video_url=json_parser[0]["url"], manifest_type="hls")
