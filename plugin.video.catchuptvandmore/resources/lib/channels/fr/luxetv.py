# -*- coding: utf-8 -*-
# Copyright: (c) 2019, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
from builtins import str
import json
import re

from codequick import Listitem, Resolver, Route
import urlquick

from resources.lib import resolver_proxy
from resources.lib.menu_utils import item_post_treatment


# TO DO

URL_ROOT = 'https://luxe.tv/'


@Route.register
def list_categories(plugin, item_id, **kwargs):
    """
    Build categories listing
    - ...
    """
    resp = urlquick.get(URL_ROOT)
    root = resp.parse("div", attrs={"id": "menu_right_replay"})

    for category_datas in root.iterfind(".//a"):
        category_title = category_datas.text
        category_url = category_datas.get('href')

        item = Listitem()
        item.label = category_title
        item.set_callback(list_videos,
                          item_id=item_id,
                          category_url=category_url)
        item_post_treatment(item)
        yield item


@Route.register
def list_videos(plugin, item_id, category_url, **kwargs):

    resp = urlquick.get(category_url)
    json_datas = re.compile(r'\] \= (.*?)\}\;').findall(resp.text)[0]
    json_parser = json.loads(json_datas + '}')

    for video_datas in json_parser["pages"]["default"]["1"]:
        video_id = str(video_datas)

        video_title = json_parser["video_set"][video_id]["name"]
        video_plot = json_parser["video_set"][video_id]["description"]
        video_image = json_parser["video_set"][video_id]["thumbnail_large"]

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = item.art['landscape'] = video_image
        item.info['plot'] = video_plot

        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_id=video_id,
                          referer=category_url)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_id,
                  download_mode=False,
                  referer=None,
                  **kwargs):

    return resolver_proxy.get_stream_vimeo(plugin, video_id, download_mode,
                                           referer)
