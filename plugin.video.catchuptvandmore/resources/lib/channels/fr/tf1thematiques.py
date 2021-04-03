# -*- coding: utf-8 -*-
# Copyright: (c) 2017, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More
from __future__ import unicode_literals
from builtins import str
import re

from codequick import Listitem, Resolver, Route
import urlquick

from resources.lib import resolver_proxy, web_utils
from resources.lib.menu_utils import item_post_treatment


# TODO
# Move WAT to resolver.py (merge with mytf1 code)

URL_ROOT = 'https://www.%s.fr'
# ChannelName

URL_VIDEOS = 'https://www.%s.fr/videos'
# PageId


@Route.register
def list_categories(plugin, item_id, **kwargs):
    """
    Build categories listing
    - Tous les programmes
    - Séries
    - Informations
    - ...
    """
    item = Listitem()
    item.label = plugin.localize(30701)
    if item_id == 'histoire':
        item.set_callback(list_videos, item_id=item_id, page='0')
    else:
        item.set_callback(list_videos, item_id=item_id, page='1')
    item_post_treatment(item)
    yield item


@Route.register
def list_videos(plugin, item_id, page, **kwargs):

    resp = urlquick.get(URL_VIDEOS % item_id)
    if item_id == 'tvbreizh':
        resp = urlquick.get(URL_VIDEOS % item_id)
    else:
        resp = urlquick.get(URL_VIDEOS % item_id + '?page=%s' % page)
    root = resp.parse("div", attrs={"class": "view-content"})

    for video_datas in root.iterfind("./div"):
        video_title = video_datas.find(".//span[@class='field-content']").find(
            './/a').text
        video_plot = ''
        if video_datas.find(".//div[@class='field-resume']") is not None:
            video_plot = video_datas.find(
                ".//div[@class='field-resume']").text.strip()
        video_image = URL_ROOT % item_id + \
            video_datas.find('.//img').get('src')
        video_url = URL_ROOT % item_id + '/' + \
            video_datas.find('.//a').get('href')

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = item.art['landscape'] = video_image
        item.info['plot'] = video_plot

        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_url=video_url)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item

    if 'tvbreizh' not in item_id:
        yield Listitem.next_page(item_id=item_id, page=str(int(page) + 1))


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_url,
                  download_mode=False,
                  **kwargs):

    resp = urlquick.get(video_url,
                        headers={'User-Agent': web_utils.get_random_ua()},
                        max_age=-1)
    video_id = re.compile(r'player.vimeo.com/video/(.*?)[\?\"]').findall(
        resp.text)[0]
    return resolver_proxy.get_stream_vimeo(plugin, video_id, download_mode)
