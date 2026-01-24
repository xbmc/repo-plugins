# -*- coding: utf-8 -*-
# Copyright: (c) 2017, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import json
import re
import xml.etree.ElementTree as ET

from codequick import Listitem, Resolver, Route, Script
import urlquick

from resources.lib import download, web_utils, resolver_proxy
from resources.lib.menu_utils import item_post_treatment


# TO DO
# QUality Mode

URL_TV5MAF_ROOT = 'https://afrique.tv5monde.com'
URL_TV5MAF_PLAYER = 'https://api.tv5monde.com/player/asset/%s/resolve?condenseKS=true'
URL_LICENCE_KEY = '%s|Content-Type=&User-Agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0|R{SSM}|'

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
    resp = urlquick.get(URL_TV5MAF_ROOT + '/videos', headers=GENERIC_HEADERS, max_age=-1)
    root = resp.parse()

    for category_datas in root.iterfind(".//div[@class='view-header']"):
        if category_datas.find(".//h2") is not None:
            category_title = category_datas.find(".//h2").text
            if category_datas.find('.//a') is not None:
                category_url = URL_TV5MAF_ROOT + category_datas.find('.//a').get('href')
                item = Listitem()
                item.label = category_title
                item.set_callback(list_programs,
                                  item_id=item_id,
                                  category_url=category_url)
                item_post_treatment(item)
                yield item


@Route.register
def list_programs(plugin, item_id, category_url, **kwargs):
    """
    Build programs listing
    - Les feux de l'amour
    - ...
    """
    resp = urlquick.get(category_url, headers=GENERIC_HEADERS, max_age=-1)
    root = resp.parse()

    for program_datas in root.iterfind(".//div[@class='views-row']"):
        if program_datas.find('.//h2') is not None:
            program_title = program_datas.find('.//h2').text
            if 'http' in program_datas.find('.//a').get('href'):
                program_url = program_datas.find('.//a').get('href')
            else:
                program_url = URL_TV5MAF_ROOT + program_datas.find('.//a').get('href')
            if 'http' in program_datas.find('.//img').get('src'):
                program_image = program_datas.find('.//img').get('src')
            else:
                program_image = URL_TV5MAF_ROOT + program_datas.find('.//img').get('src')

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
    resp = urlquick.get(program_url, headers=GENERIC_HEADERS, max_age=-1)
    root = resp.parse()

    if root.find(".//nav[@class='title-season']") is None:
        video_datas = root.find(".//main[@class='layout-3col__full']")
        video_title = video_datas.find('.//h1').text.strip()
        video_image = ''
        videos_image = re.compile(r'image\" content=\"(.*?)\"').findall(resp.text)
        if len(videos_image) > 0:
            video_image = videos_image[0]
        else:
            video_image = ''

        if len(video_image) > 0:
            item = Listitem()
            item.label = video_title
            item.art['thumb'] = item.art['landscape'] = item.art["fanart"] = video_image
            item.set_callback(get_video_url,
                              item_id=item_id,
                              video_url=program_url)
            item_post_treatment(item, is_playable=True, is_downloadable=False)
            yield item
        else:
            item = Listitem()
            item.label = Script.localize(30896)
            yield item
    else:
        root_season = resp.parse("div", attrs={"class": "group-footer-content"})
        raw_season = ET.tostring(root_season, encoding='utf-8').decode()
        seasons = list(set(re.findall(r'div class="season-(\d+?) views-row"', raw_season)))
        for season in seasons:
            season_title = 'Saison ' + season
            videos_datas = root.findall(".//div[@class='season-" + season + " views-row']")
            is_season = False
            for video_datas in videos_datas:
                if video_datas.find('.//h2') is not None:
                    is_season = True
            if is_season:
                item = Listitem()
                item.label = season_title
                item.set_callback(list_videos_by_season,
                                  item_id=item_id,
                                  season=season,
                                  season_datas=videos_datas)
                item_post_treatment(item)
                yield item


@Route.register
def list_videos_by_season(plugin, item_id, season, season_datas, **kwargs):
    for video_datas in season_datas:
        if video_datas.find('.//h2') is not None:
            video_title = video_datas.find('.//h2').text
            video_image = ''
            if video_datas.find('.//img') is not None:
                if 'http' in video_datas.find('.//img').get('src'):
                    video_image = video_datas.find('.//img').get('src')
                else:
                    video_image = URL_TV5MAF_ROOT + video_datas.find('.//img').get('src')
            if 'http' in video_datas.find('.//a').get('href'):
                video_url = video_datas.find('.//a').get('href')
            else:
                video_url = URL_TV5MAF_ROOT + video_datas.find('.//a').get('href')

            item = Listitem()
            item.label = video_title
            item.art['thumb'] = item.art['landscape'] = item.art["fanart"] = video_image
            item.set_callback(get_video_url,
                              item_id=item_id,
                              video_url=video_url)
            item_post_treatment(item,
                                is_playable=True,
                                is_downloadable=True)
            yield item


@Route.register
def list_videos_season(plugin, item_id, season_url, **kwargs):
    resp = urlquick.get(season_url, headers=GENERIC_HEADERS, max_age=-1)
    root = resp.parse()

    for video_datas in root.iterfind(
            ".//div[@class='season-1 views-row']"):
        # TODO Season value
        if video_datas.find('.//h2') is not None:
            video_title = video_datas.find('.//h2').text
            if 'http' in video_datas.find('.//img').get('src'):
                video_image = video_datas.find('.//img').get('src')
            else:
                video_image = URL_TV5MAF_ROOT + video_datas.find('.//img').get('src')
            if 'http' in video_datas.find('.//a').get('href'):
                video_url = video_datas.find('.//a').get('href')
            else:
                video_url = URL_TV5MAF_ROOT + video_datas.find('.//a').get('href')

            item = Listitem()
            item.label = video_title
            item.art['thumb'] = item.art['landscape'] = item.art["fanart"] = video_image
            item.set_callback(get_video_url,
                              item_id=item_id,
                              video_url=video_url)
            item_post_treatment(item, is_playable=True, is_downloadable=True)
            yield item


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_url,
                  download_mode=False,
                  **kwargs):
    resp = urlquick.get(video_url, headers=GENERIC_HEADERS, max_age=-1)
    video_json = re.compile('data-broadcast=\'(.*?)\'').findall(resp.text)[0]
    json_parser = json.loads(video_json)
    video_url = json_parser[0]["url"]
    video_token = json_parser[0]["token"]

    headers = GENERIC_HEADERS.copy()
    headers.update({'Authorization': 'Bearer ' + video_token})
    resp = urlquick.get(URL_TV5MAF_PLAYER % video_url, headers=headers, max_age=-1)
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
