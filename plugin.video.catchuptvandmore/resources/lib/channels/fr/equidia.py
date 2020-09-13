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
from datetime import date

from codequick import Route, Resolver, Listitem, utils, Script

from resources.lib import web_utils
from resources.lib import download
from resources.lib.menu_utils import item_post_treatment

import json
import re
import urlquick

# TODO

URL_ROOT = 'https://www.equidia.fr'

URL_API = "https://equidia-vodce-players.hexaglobe.net"

URL_LIVE_DATAS = URL_API + '/mf_data/%s.json'

URL_API_SEARCH = "https://api.equidia.fr/api/public"

URL_IMAGE = URL_API_SEARCH + '/media/article_header/%s'
# ImageId

URL_REPLAY_DATAS = 'https://api.equidia.fr/api/public/videos-store/player/%s'
# VideoId

CATEGORIES_VIDEOS_EQUIDIA = {
    '/search/emissions': Script.localize(20343),  # TV shows
    '/search/courses': Script.localize(30726)  # Races
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
    for category_context, category_title in list(CATEGORIES_VIDEOS_EQUIDIA.items(
    )):
        category_url = URL_API_SEARCH + category_context
        item = Listitem()
        if 'Courses' in category_title:
            next_value = 'list_videos_courses'
        else:
            next_value = 'list_videos_emissions'
        item.label = category_title
        item.set_callback(eval(next_value),
                          item_id=item_id,
                          category_url=category_url,
                          page='0')
        item_post_treatment(item)
        yield item


@Route.register
def list_videos_emissions(plugin, item_id, category_url, page, **kwargs):

    params = {
        'range': '[%s,%s]' % (page, str(int(page) + 11))
    }
    resp = urlquick.post(category_url, params=params)
    json_parser = json.loads(resp.text)

    for video_datas in json_parser["results"]:
        video_title = video_datas["name"]
        video_image = URL_IMAGE % video_datas["episode"]["media"]["slug"]
        video_url = URL_ROOT + '/programmes/' + \
            video_datas["program"]["slug"] + '/' + video_datas["episode"]["slug"]

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = item.art['landscape'] = video_image

        item.set_callback(get_video_emission_url,
                          item_id=item_id,
                          video_url=video_url)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item

    # More videos...
    yield Listitem.next_page(item_id=item_id,
                             category_url=category_url,
                             page=str(int(page) + 12))


@Route.register
def list_videos_courses(plugin, item_id, category_url, page, **kwargs):

    params = {
        'range': '[%s,%s]' % (page, str(int(page) + 11))
    }
    resp = urlquick.post(category_url, params=params)
    json_parser = json.loads(resp.text)

    for video_datas in json_parser["results"]:
        video_title = 'R%s - C%s - %s' % (
            video_datas["reunion"]["num_reunion"], video_datas["num_course_pmu"], video_datas["libcourt_prix_course"])
        video_image = URL_IMAGE % video_datas["photo"]["slug"]
        video_url = URL_ROOT + '/courses/%s/R%s/C%s' % (
            video_datas["reunion"]["date_reunion"], video_datas["reunion"]["num_reunion"], video_datas["num_course_pmu"])

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = item.art['landscape'] = video_image

        item.set_callback(get_video_course_url,
                          item_id=item_id,
                          video_url=video_url)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item

    # More videos...
    yield Listitem.next_page(item_id=item_id,
                             category_url=category_url,
                             page=str(int(page) + 12))


@Resolver.register
def get_video_emission_url(plugin,
                           item_id,
                           video_url,
                           download_mode=False,
                           **kwargs):

    resp = urlquick.get(video_url,
                        headers={'User-Agent': web_utils.get_random_ua()},
                        max_age=-1)
    video_id = re.compile(r'name_no_extention\"\:\"(.*?)[\?\"]').findall(
        resp.text)[0]
    resp2 = urlquick.get(URL_REPLAY_DATAS % video_id, max_age=-1)
    json_parser2 = json.loads(resp2.text)
    resp3 = urlquick.get(json_parser2["video_url"], max_age=-1)
    json_parser3 = json.loads(resp3.text)
    if download_mode:
        return download.download_video(json_parser3["master"])
    return json_parser3["master"]


@Resolver.register
def get_video_course_url(plugin,
                         item_id,
                         video_url,
                         download_mode=False,
                         **kwargs):

    resp = urlquick.get(video_url,
                        headers={'User-Agent': web_utils.get_random_ua()},
                        max_age=-1)
    video_id = re.compile(r'video_course_nom\"\:\"(.*?)[\?\"]').findall(
        resp.text)[0]
    resp2 = urlquick.get(URL_REPLAY_DATAS % video_id, max_age=-1)
    json_parser2 = json.loads(resp2.text)
    resp3 = urlquick.get(json_parser2["video_url"], max_age=-1)
    json_parser3 = json.loads(resp3.text)
    if download_mode:
        return download.download_video(json_parser3["master"])
    return json_parser3["master"]


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    # Get date of Today
    today = date.today()
    today_value = today.strftime("%Y%m%d")
    resp = urlquick.get(
        URL_LIVE_DATAS % today_value, headers={"User-Agent": web_utils.get_random_ua()}, max_age=-1)
    json_parser = json.loads(resp.text)
    url_stream_datas = ''
    for stream_datas in json_parser:
        if 'EQUIDIA' in stream_datas['title']:
            url_stream_datas = stream_datas["streamUrl"]
    resp2 = urlquick.get(
        url_stream_datas, headers={"User-Agent": web_utils.get_random_ua()}, max_age=-1)
    json_parser2 = json.loads(resp2.text)
    return json_parser2["primary"]
