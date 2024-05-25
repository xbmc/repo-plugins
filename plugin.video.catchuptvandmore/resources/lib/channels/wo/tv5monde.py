# -*- coding: utf-8 -*-
# Copyright: (c) 2017, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals

import json
import re
from builtins import str

import urlquick
# noinspection PyUnresolvedReferences
from codequick import Listitem, Resolver, Route, Script
from resources.lib import download, web_utils, resolver_proxy
from resources.lib.menu_utils import item_post_treatment

# TODO Rework filter for all videos

URL_TV5MONDE_LIVE = 'http://live.tv5monde.com/'

URL_TV5MONDE_ROOT = 'https://revoir.tv5monde.com'

M3U8_NOT_FBS = 'https://ott.tv5monde.com/Content/HLS/Live/channel(europe)/variant.m3u8'

LIST_LIVE_TV5MONDE = {'tv5mondefbs': 'fbs', 'tv5mondeinfo': 'infoplus'}

LIVETYPE = {
    "FBS": "0",
    "NOT_FBS": "1"
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
    resp = urlquick.get(URL_TV5MONDE_ROOT + '/toutes-les-emissions',
                        headers={'User-Agent': web_utils.get_random_ua()})
    root = resp.parse()
    category_title = root.find(".//nav[@class='footer__emissions footer-content']").find(
        ".//div[@class='footer__title']").find('.//a').text.strip()
    item = Listitem()
    item.label = category_title
    item.set_callback(list_programs, item_id=item_id)
    item_post_treatment(item)
    yield item

    category_title = 'Toutes les vidéos'
    item = Listitem()
    item.label = category_title
    item.set_callback(list_videos_category, item_id=item_id, page='1')
    item_post_treatment(item)
    yield item


@Route.register
def list_programs(plugin, item_id, **kwargs):
    """
    Build programs listing
    - Les feux de l'amour
    - ...
    """
    resp = urlquick.get(URL_TV5MONDE_ROOT,
                        headers={'User-Agent': web_utils.get_random_ua()})
    root = resp.parse("nav", attrs={"class": "footer__emissions footer-content"})

    for program_datas in root.iterfind(".//li"):
        program_title = program_datas.find('.//a').text.strip()
        program_url = URL_TV5MONDE_ROOT + program_datas.find('.//a').get(
            'href')

        item = Listitem()
        item.label = program_title
        item.set_callback(list_videos,
                          item_id=item_id,
                          program_url=program_url,
                          page='1')
        item_post_treatment(item)
        yield item


@Route.register
def list_videos(plugin, item_id, program_url, page, **kwargs):
    resp = urlquick.get(program_url + '?page=%s' % page,
                        headers={'User-Agent': web_utils.get_random_ua()})
    root = resp.parse()

    for video_datas in root.iterfind(".//div[@class='bloc-episode-content']"):
        if video_datas.find('.//h3') is not None:
            video_title = video_datas.find('.//h2').text.strip() + ' - ' + video_datas.find('.//h3').text.strip()
        else:
            video_title = video_datas.find('.//h2').text.strip()
        if 'http' in video_datas.find('.//img').get('src'):
            video_image = video_datas.find('.//img').get('src')
        else:
            video_image = URL_TV5MONDE_ROOT + video_datas.find('.//img').get(
                'src')
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
                             program_url=program_url,
                             page=str(int(page) + 1))


@Route.register
def list_videos_category(plugin, item_id, page, **kwargs):
    resp = urlquick.get(URL_TV5MONDE_ROOT +
                        '/toutes-les-videos?page=%s' % page,
                        headers={'User-Agent': web_utils.get_random_ua()})
    root = resp.parse()

    for video_datas in root.iterfind(".//div[@class='bloc-episode-content']"):
        if video_datas.find('.//h3') is not None:
            video_title = video_datas.find('.//h2').text.strip() + ' - ' + video_datas.find('.//h3').text.strip()
        else:
            video_title = video_datas.find('.//h2').text.strip()
        if 'http' in video_datas.find('.//img').get('src'):
            video_image = video_datas.find('.//img').get('src')
        else:
            video_image = URL_TV5MONDE_ROOT + video_datas.find('.//img').get(
                'src')
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
    resp = urlquick.get(video_url,
                        headers={'User-Agent': web_utils.get_random_ua()},
                        max_age=-1)
    video_json = re.compile('data-broadcast=\'(.*?)\'').findall(resp.text)[0]
    json_parser = json.loads(video_json)
    try:
        final_video_url = json_parser["files"][0]["url"]
    except Exception:
        final_video_url = json_parser[0]["url"]

    if download_mode:
        return download.download_video(final_video_url)

    return final_video_url


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
                        headers={'User-Agent': web_utils.get_random_ua()},
                        max_age=-1)
    live_json = re.compile(r'data-broadcast=\'(.*?)\'').findall(resp.text)[0]
    json_parser = json.loads(live_json)

    return resolver_proxy.get_stream_with_quality(plugin, video_url=json_parser[0]["url"], manifest_type="hls")
