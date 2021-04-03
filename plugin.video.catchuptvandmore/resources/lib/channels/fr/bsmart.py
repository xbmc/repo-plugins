# -*- coding: utf-8 -*-
# Copyright: (c) 2019, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import json
import re

from codequick import Listitem, Resolver, Route, Script
import urlquick

from resources.lib import resolver_proxy, web_utils
from resources.lib.menu_utils import item_post_treatment


URL_ROOT = "https://www.bsmart.fr"

URL_LIVE_DATAS = URL_ROOT + "/static/js/bundle.%s.js"

URL_API = 'https://api.bsmart.fr/api'

CATEGORIES_BSMART = {
    '/programs/': Script.localize(20343),  # TV shows
    '/videos/': Script.localize(3)  # Videos
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
    for category_context, category_title in list(CATEGORIES_BSMART.items(
    )):
        category_url = URL_API + category_context
        item = Listitem()
        if 'videos' in category_context:
            next_value = 'list_videos'
        else:
            next_value = 'list_programs'
        item.label = category_title
        item.set_callback(eval(next_value),
                          item_id=item_id,
                          next_url=category_url,
                          page='1')
        item_post_treatment(item)
        yield item


@Route.register
def list_programs(plugin, item_id, next_url, page, **kwargs):

    resp = urlquick.get(next_url)
    json_parser = json.loads(resp.text)

    for program_datas in json_parser["results"]:
        program_title = program_datas["title"]
        program_image = ''
        if 'banners' in program_datas:
            program_image = program_datas["banners"]["vertical"]["x1000"]
        program_plot = program_datas["description"]
        program_url = URL_API + '/program/' + program_datas["slug"]

        item = Listitem()
        item.label = program_title
        item.art['thumb'] = item.art['landscape'] = program_image
        item.info['plot'] = program_plot

        item.set_callback(list_videos_program,
                          item_id=item_id,
                          next_url=program_url)
        item_post_treatment(item)
        yield item


@Route.register
def list_videos_program(plugin, item_id, next_url, **kwargs):

    resp = urlquick.get(next_url)
    json_parser = json.loads(resp.text)

    for video_datas in json_parser["videos"]:
        video_title = video_datas["program"]["title"] + ' - ' + video_datas["title"]
        if 'dailymotion' in video_datas["providers"]:
            video_image = ''
            if 'thumb' in video_datas["providers"]["dailymotion"]:
                video_image = video_datas["providers"]["dailymotion"]["thumb"]
            video_id = video_datas["providers"]["dailymotion"]["id"]

            item = Listitem()
            item.label = video_title
            item.art['thumb'] = item.art['landscape'] = video_image

            item.set_callback(get_video_url,
                              item_id=item_id,
                              video_id=video_id)
            item_post_treatment(item, is_playable=True, is_downloadable=True)
            yield item


@Route.register
def list_videos(plugin, item_id, next_url, page, **kwargs):

    resp = urlquick.get(next_url + '?page=%s' % page)
    json_parser = json.loads(resp.text)

    for video_datas in json_parser["results"]:
        video_title = video_datas["program"]["title"] + ' - ' + video_datas["title"]
        if 'dailymotion' in video_datas["providers"]:
            video_image = ''
            if 'thumb' in video_datas["providers"]["dailymotion"]:
                video_image = video_datas["providers"]["dailymotion"]["thumb"]
            video_id = video_datas["providers"]["dailymotion"]["id"]

            item = Listitem()
            item.label = video_title
            item.art['thumb'] = item.art['landscape'] = video_image

            item.set_callback(get_video_url,
                              item_id=item_id,
                              video_id=video_id)
            item_post_treatment(item, is_playable=True, is_downloadable=True)
            yield item

    # More videos...
    yield Listitem.next_page(item_id=item_id,
                             next_url=next_url,
                             page=str(int(page) + 1))


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_id,
                  download_mode=False,
                  **kwargs):

    return resolver_proxy.get_stream_dailymotion(plugin,
                                                 video_id,
                                                 download_mode)


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    resp = urlquick.get(
        URL_ROOT, headers={"User-Agent": web_utils.get_random_ua()}, max_age=-1)
    live_id = re.compile(r'dailymotion.com/embed/video/(.*?)[\?\"]').findall(resp.text)[0]
    return resolver_proxy.get_stream_dailymotion(plugin,
                                                 live_id,
                                                 False)
