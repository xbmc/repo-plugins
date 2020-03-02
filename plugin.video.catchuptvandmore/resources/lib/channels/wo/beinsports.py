# -*- coding: utf-8 -*-
"""
    Catch-up TV & More
    Copyright (C) 2018  SylvainCecchetto

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

from resources.lib.labels import LABELS
from resources.lib import web_utils
from resources.lib import resolver_proxy
from resources.lib.menu_utils import item_post_treatment

import json
import urlquick

# TO DO
#

# https://gist.github.com/sergeimikhan/1e90f28b8129335274b9
URL_API_ROOT = 'http://api.beinsports.com'

URL_INFO_SITES = URL_API_ROOT + '/sites'

URL_CATEGORIES = URL_API_ROOT + '/dropdowns?site=%s'
# siteId

URL_VIDEOS = URL_API_ROOT + '/contents?itemsPerPage=30&type=3&site=%s&page=%s&taxonomy%%5B%%5D=%s&order%%5BpublishedAt%%5D=DESC'

# siteId, page


def replay_entry(plugin, item_id, **kwargs):
    """
    First executed function after replay_bridge
    """
    return list_sites(plugin, item_id)


@Route.register
def list_sites(plugin, item_id, **kwargs):
    """
    Build categories listing
    - Tous les programmes
    - Séries
    - Informations
    - ...
    """
    resp = urlquick.get(URL_INFO_SITES)
    json_parser = json.loads(resp.text)

    for site_datas in json_parser['hydra:member']:

        site_title = site_datas["name"] + ' - Timezone : ' + site_datas["timezone"]
        site_id = site_datas["@id"].replace('/sites/', '')

        item = Listitem()
        item.label = site_title
        item.set_callback(list_categories, item_id=item_id, site_id=site_id)
        item_post_treatment(item)
        yield item


@Route.register
def list_categories(plugin, item_id, site_id, **kwargs):

    resp = urlquick.get(URL_CATEGORIES % site_id)
    json_parser = json.loads(resp.text)

    for category_datas in json_parser['hydra:member']:
        if category_datas["name"] is not None:
            category_title = category_datas["name"]
            category_reference = category_datas["reference"]

            item = Listitem()
            item.label = category_title
            item.set_callback(
                list_sub_categories,
                item_id=item_id,
                site_id=site_id,
                category_reference=category_reference)
            item_post_treatment(item)
            yield item


@Route.register
def list_sub_categories(plugin, item_id, site_id, category_reference,
                        **kwargs):

    resp = urlquick.get(URL_CATEGORIES % site_id)
    json_parser = json.loads(resp.text)

    for category_datas in json_parser['hydra:member']:
        if category_datas["name"] is not None:
            if category_reference in category_datas["reference"]:
                for sub_category_datas in category_datas["dropdownEntries"]:
                    sub_category_title = sub_category_datas["taxonomy"]["name"]
                    sub_category_id = sub_category_datas["taxonomy"][
                        "@id"].replace('/taxonomies/', '')

                    item = Listitem()
                    item.label = sub_category_title
                    item.set_callback(
                        list_videos,
                        item_id=item_id,
                        site_id=site_id,
                        sub_category_id=sub_category_id,
                        page='1')
                    item_post_treatment(item)
                    yield item


@Route.register
def list_videos(plugin, item_id, site_id, sub_category_id, page, **kwargs):

    resp = urlquick.get(URL_VIDEOS % (site_id, page, sub_category_id))
    json_parser = json.loads(resp.text)

    for list_videos_datas in json_parser['hydra:member']:
        for video_datas in list_videos_datas['media']:
            video_title = list_videos_datas['headline']
            video_image = video_datas['media']['context']['thumbnail_url']
            video_duration = video_datas['media']['context']['duration']
            video_id = video_datas['media']['context']['private_id']

            item = Listitem()
            item.label = video_title
            item.art['thumb'] = video_image
            item.info['duration'] = video_duration

            item.set_callback(
                get_video_url,
                item_id=item_id,
                video_id=video_id)
            item_post_treatment(item, is_playable=True, is_downloadable=True)
            yield item

    if 'hydra:nextPage' in json_parser:
        yield Listitem.next_page(
            item_id=item_id,
            category_url=URL_API_ROOT + json_parser["hydra:nextPage"])


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_id,
                  download_mode=False,
                  **kwargs):

    return resolver_proxy.get_stream_dailymotion(plugin, video_id,
                                                 download_mode)
