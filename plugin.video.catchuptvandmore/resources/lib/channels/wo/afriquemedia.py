# -*- coding: utf-8 -*-
# Copyright: (c) 2018, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
from builtins import str
import re

from codequick import Listitem, Resolver, Route
import urlquick

from resources.lib import resolver_proxy
from resources.lib.menu_utils import item_post_treatment


URL_ROOT = 'http://www.afriquemedia.tv'

URL_LIVE = URL_ROOT + '/live'

URL_REPLAY = URL_ROOT + '/replay?jut1=%s'
# page


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
    item.set_callback(list_videos, item_id=item_id, page='1')
    item_post_treatment(item)
    yield item


@Route.register
def list_videos(plugin, item_id, page, **kwargs):

    resp = urlquick.get(URL_REPLAY % page)
    root = resp.parse()

    for video_datas in root.iterfind(
            ".//div[@class='yt-fp-outer outerwidthlarge3 outerwidthsmall1 rounding7']"
    ):
        video_title = video_datas.find('.//img').get('alt')
        video_image = video_datas.find('.//img').get('src')
        video_id = video_datas.find('.//a').get('href').split('?v=')[1]

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = item.art['landscape'] = video_image

        item.set_callback(get_video_url,
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

    return resolver_proxy.get_stream_youtube(plugin, video_id, download_mode)


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_LIVE)
    live_id = re.compile(r'dailymotion.com/embed/video/(.*?)[\?\"]').findall(
        resp.text)[0]
    return resolver_proxy.get_stream_dailymotion(plugin, live_id, False)
