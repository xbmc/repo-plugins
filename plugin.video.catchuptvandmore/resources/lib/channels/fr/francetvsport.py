# -*- coding: utf-8 -*-
"""
    Catch-up TV & More
    Original work (C) JUL1EN094, SPM, SylvainCecchetto
    Copyright (C) 2016  SylvainCecchetto

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

from builtins import str
from codequick import Route, Resolver, Listitem, utils, Script

from resources.lib.labels import LABELS
from resources.lib import web_utils
from resources.lib import resolver_proxy
from resources.lib.menu_utils import item_post_treatment
from resources.lib.kodi_utils import get_selected_item_art, get_selected_item_label, get_selected_item_info

import re
import json
import time
import urlquick
'''
Channels:
    * France TV Sport
'''

URL_ROOT_SPORT = 'https://sport.francetvinfo.fr'

URL_FRANCETV_SPORT = 'https://api-sport-events.webservices.' \
                     'francetelevisions.fr/%s'


def replay_entry(plugin, item_id, **kwargs):
    """
    First executed function after replay_bridge
    """
    return list_categories(plugin, item_id)


@Route.register
def list_categories(plugin, item_id, **kwargs):
    """
    Build categories listing
    - Tous les programmes
    - Séries
    - Informations
    - ...
    """
    category_title = 'Videos'
    item = Listitem()
    item.label = category_title
    item.set_callback(list_videos, item_id=item_id, mode='videos', page='1')
    item_post_treatment(item)
    yield item

    category_title = 'Replay'
    item = Listitem()
    item.label = category_title
    item.set_callback(list_videos, item_id=item_id, mode='replay', page='1')
    item_post_treatment(item)
    yield item


@Route.register
def list_videos(plugin, item_id, mode, page, **kwargs):

    resp = urlquick.get(URL_FRANCETV_SPORT % mode + '?page=%s' % page)
    json_parser = json.loads(resp.text)

    for video_datas in json_parser["page"]["flux"]:
        video_title = video_datas["title"]
        video_image = ''
        if 'image' in video_datas:
            video_image = video_datas["image"]["large_16_9"]
        video_duration = 0
        if 'duration' in video_datas:
            video_duration = int(video_datas["duration"])
        video_url = URL_ROOT_SPORT + video_datas["url"]
        date_value = time.strftime('%Y-%m-%d',
                                   time.localtime(video_datas["updated"]))

        item = Listitem()
        item.label = video_title
        item.info['duration'] = video_duration
        item.art['thumb'] = item.art['landscape'] = video_image
        item.info.date(date_value, '%Y-%m-%d')

        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_url=video_url)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item

    yield Listitem.next_page(item_id=item_id,
                             mode=mode,
                             page=str(int(page) + 1))


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_url,
                  download_mode=False,
                  **kwargs):

    resp = urlquick.get(video_url)
    id_diffusion = ''
    list_id_diffusion = re.compile(r'data-video="(.*?)"').findall(resp.text)
    for id_diffusion_value in list_id_diffusion:
        id_diffusion = id_diffusion_value
        break

    return resolver_proxy.get_francetv_video_stream(plugin, id_diffusion,
                                                    download_mode)


def multi_live_entry(plugin, item_id, **kwargs):
    """
    First executed function after replay_bridge
    """
    return list_lives(plugin, item_id)


@Route.register
def list_lives(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_FRANCETV_SPORT % 'directs', max_age=-1)
    json_parser = json.loads(resp.text)

    if 'lives' in json_parser["page"]:
        for live_datas in json_parser["page"]["lives"]:
            live_title = live_datas["title"]
            live_image = ''
            if 'image' in live_datas:
                live_image = live_datas["image"]["large_16_9"]
            id_diffusion = live_datas["sivideo-id"]
            try:
                live_date_plot = time.strftime(
                    '%d/%m/%Y %H:%M', time.localtime(live_datas["start"]))
                date_value = time.strftime('%Y-%m-%d',
                                           time.localtime(live_datas["start"]))
            except Exception:
                live_date_plot = ''
                date_value = ''
            live_plot = 'Live starts at ' + live_date_plot

            item = Listitem()
            item.label = live_title
            item.art['thumb'] = item.art['landscape'] = live_image
            item.info['plot'] = live_plot
            item.info.date(date_value, '%Y-%m-%d')
            item.set_callback(get_live_url,
                              item_id=item_id,
                              id_diffusion=id_diffusion)
            yield item

    for live_datas in json_parser["page"]["upcoming-lives"]:
        live_title = 'Prochainement - ' + live_datas["title"]
        try:
            live_image = live_datas["image"]["large_16_9"]
        except KeyError:
            live_image = ''
        try:
            live_date_plot = time.strftime('%d/%m/%Y %H:%M',
                                           time.localtime(live_datas["start"]))
            date_value = time.strftime('%Y-%m-%d',
                                       time.localtime(live_datas["start"]))
        except Exception:
            live_date_plot = ''
            date_value = ''
        live_plot = 'Live starts at ' + live_date_plot

        item = Listitem()
        item.label = live_title
        item.art['thumb'] = item.art['landscape'] = live_image
        item.info['plot'] = live_plot
        item.info.date(date_value, '%Y-%m-%d')
        yield item


@Resolver.register
def get_live_url(plugin, item_id, id_diffusion, **kwargs):

    return resolver_proxy.get_francetv_live_stream(plugin, id_diffusion)
