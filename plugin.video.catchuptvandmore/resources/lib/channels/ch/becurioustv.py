# -*- coding: utf-8 -*-
# Copyright: (c) 2018, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import re

from codequick import Listitem, Resolver, Route
import urlquick

from resources.lib import resolver_proxy, web_utils
from resources.lib.menu_utils import item_post_treatment


# TO DO
# Add more button
# test videos to see if there is other video hoster

URL_ROOT = 'https://becurious.ch'

URL_VIDEOS = URL_ROOT + '/?infinity=scrolling'


@Route.register
def list_categories(plugin, item_id, **kwargs):
    """
    Build categories listing
    - Tous les programmes
    - Séries
    - Informations
    - ...
    """
    resp = urlquick.get(URL_ROOT,
                        headers={'User-Agent': web_utils.get_random_ua()})
    root = resp.parse("ul", attrs={"class": "sub-menu"})

    for category_datas in root.iterfind(".//li"):
        category_title = category_datas.find('.//a').text
        category_url = category_datas.find('.//a').get('href')

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
    root = resp.parse()

    for video_datas in root.iterfind(".//article"):
        video_title = video_datas.find('.//a').get('title')
        video_url = video_datas.find('.//a').get('href')
        video_image = video_datas.find('.//img').get('src')

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = item.art['landscape'] = video_image

        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_url=video_url)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_url,
                  download_mode=False,
                  **kwargs):

    resp = urlquick.get(video_url)
    root = resp.parse()
    stream_datas = root.find('.//iframe').get('src')

    # Case Youtube
    if 'youtube' in stream_datas:
        video_id = re.compile('www.youtube.com/embed/(.*?)[\?\"\&]').findall(
            stream_datas)[0]
        return resolver_proxy.get_stream_youtube(plugin, video_id,
                                                 download_mode)
    # Case Vimeo
    if 'vimeo' in stream_datas:
        video_id = re.compile('player.vimeo.com/video/(.*?)[\?\"]').findall(
            stream_datas)[0]
        return resolver_proxy.get_stream_vimeo(plugin, video_id, download_mode)

    # Add Notification
    return False
