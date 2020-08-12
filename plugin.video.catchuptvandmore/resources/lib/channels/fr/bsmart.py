# -*- coding: utf-8 -*-
"""
    Catch-up TV & More
    Copyright (C) 2019  SylvainCecchetto

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

import json
import re
import urlquick

# TODO

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
        if 'Vidéos' in category_title:
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
        program_image = program_datas["banner"]
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
        video_image = video_datas["asset"]["dailymotion"]["thumb"]
        video_id = video_datas["asset"]["dailymotion"]["id"]

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
        video_image = video_datas["asset"]["dailymotion"]["thumb"]
        video_id = video_datas["asset"]["dailymotion"]["id"]

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
    js_id = re.compile(r'js\/bundle\.(.*?)\.js').findall(resp.text)[0]
    resp2 = urlquick.get(
        URL_LIVE_DATAS % js_id, headers={"User-Agent": web_utils.get_random_ua()}, max_age=-1)
    live_id = re.compile(r'\(Fi\,\{id\:\"(.*?)\"').findall(resp2.text)[1]
    return resolver_proxy.get_stream_dailymotion(plugin,
                                                 live_id,
                                                 False)
