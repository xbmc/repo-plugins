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

import json
import urlquick

# TO DO
#

# https://gist.github.com/sergeimikhan/1e90f28b8129335274b9
URL_API_ROOT = 'http://api.beinsports.com'

URL_VIDEOS = URL_API_ROOT + '/contents?itemsPerPage=30&type=3&site=%s&page=%s&order%%5BpublishedAt%%5D=DESC'
# site, page


def replay_entry(plugin, item_id):
    """
    First executed function after replay_bridge
    """
    return list_categories(plugin, item_id)


@Route.register
def list_categories(plugin, item_id):
    """
    Build categories listing
    - Tous les programmes
    - Séries
    - Informations
    - ...
    """
    desired_language = Script.setting['beinsports.language']

    if desired_language == 'FR':
        sites = ['2', '5']
    elif desired_language == 'AU':
        sites = ['1']
    elif desired_language == 'AR':
        sites = ['3']
    elif desired_language == 'EN':
        sites = ['4']
    elif desired_language == 'US':
        sites = ['6']
    elif desired_language == 'ES':
        sites = ['7']
    elif desired_language == 'NZ':
        sites = ['8']
    elif desired_language == 'HK':
        sites = ['10']
    elif desired_language == 'PH':
        sites = ['11']
    elif desired_language == 'TH':
        sites = ['12', '15']
    elif desired_language == 'ID':
        sites = ['13', '14']
    elif desired_language == 'MY':
        sites = ['16']

    for siteid in sites:
        category_title = 'Videos %s (%s)' % (desired_language, siteid)
        category_url = URL_VIDEOS % (siteid, '1')

        item = Listitem()
        item.label = category_title
        item.set_callback(
            list_videos,
            item_id=item_id,
            category_url=category_url)
        yield item


@Route.register
def list_videos(plugin, item_id, category_url):

    resp = urlquick.get(category_url)
    json_parser = json.loads(resp.text)

    for video_datas in json_parser['hydra:member']:
        video_title = video_datas['headline']
        video_id = video_datas['media'][0]['media']['context']['private_id']
        video_image = video_datas['media'][0]['media']['context']['thumbnail_url']

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = video_image

        item.context.script(
            get_video_url,
            plugin.localize(LABELS['Download']),
            item_id=item_id,
            video_id=video_id,
            video_label=LABELS[item_id] + ' - ' + item.label,
            download_mode=True)

        item.set_callback(
            get_video_url,
            item_id=item_id,
            video_id=video_id)
        yield item

    yield Listitem.next_page(
        item_id=item_id,
        category_url=URL_API_ROOT + json_parser["hydra:nextPage"])


@Resolver.register
def get_video_url(
        plugin, item_id, video_id, download_mode=False, video_label=None):

    return resolver_proxy.get_stream_dailymotion(
        plugin,
        video_id,
        download_mode,
        video_label)
