# -*- coding: utf-8 -*-
# Copyright: (c) 2019, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
from builtins import str
import json
import re
import requests

from codequick import Listitem, Resolver, Route
import htmlement

from resources.lib import download
from resources.lib.menu_utils import item_post_treatment

URL_ROOT = 'https://live.philharmoniedeparis.fr'

URL_REPLAYS = URL_ROOT + '/misc/AjaxListVideo.ashx?/Concerts/%s'

URL_STREAM = URL_ROOT + '/otoPlayer/config.ashx?id=%s'


@Route.register
def website_root(plugin, item_id, **kwargs):
    """Add modes in the listing"""
#    Build categories listing
#    - Tous les programmes
#    - Séries
#    - Informations
#    - ...
    item = Listitem()
    item.label = plugin.localize(30701)
    item.set_callback(list_videos, item_id=item_id, page='1')
    item_post_treatment(item)
    yield item


@Route.register
def list_videos(plugin, item_id, page, **kwargs):
    """Add modes in the listing"""

    resp = requests.get(URL_REPLAYS % page)
    parser = htmlement.HTMLement()
    parser.feed(resp.text)
    root = parser.close()

    for video_datas in root.iterfind(".//li"):
        if 'concert' in video_datas.get('class'):
            video_title = video_datas.find('.//a').get('title')
            video_image = URL_ROOT + re.compile(r'url\((.*?)\)').findall(
                video_datas.find(".//div[@class='imgContainer']").get('style'))[0]
            video_id = re.compile(r'concert\/(.*?)\/').findall(
                video_datas.find('.//a').get('href'))[0]

            item = Listitem()
            item.label = video_title
            item.art['thumb'] = item.art['landscape'] = video_image

            item.set_callback(
                get_video_url,
                item_id=item_id,
                video_id=video_id)
            item_post_treatment(item, is_playable=True, is_downloadable=True)
            yield item

    yield Listitem.next_page(item_id=item_id, page=str(int(page) + 1))


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_id,
                  download_mode=False,
                  **kwargs):
    """Get video URL and start video player"""

    resp = requests.get(URL_STREAM % video_id)
    json_parser = json.loads(resp.text)
    final_url = URL_ROOT + json_parser["files"]["desktop"]["file"]

    if download_mode:
        return download.download_video(final_url)
    return final_url
