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

from builtins import str
from codequick import Route, Resolver, Listitem, utils, Script

from resources.lib.labels import LABELS
from resources.lib import web_utils
from resources.lib import download
from resources.lib.listitem_utils import item_post_treatment, item2dict

import re
import urlquick

URL_ROOT = 'http://www.antennereunion.fr'

URL_LIVE = URL_ROOT + '/direct'

CATEGORIES = {
    'ÉMISSIONS':
    URL_ROOT +
    '/replay/emissions?debut_article_divertissement=%s#pagination_article_divertissement',
    'SÉRIES ET FICTIONS':
    URL_ROOT +
    '/replay/series-et-fictions?debut_article_divertissement=%s#pagination_article_divertissement',
    'INFO ET MAGAZINES':
    URL_ROOT +
    '/replay/info-et-magazines?debut_article_divertissement=%s#pagination_article_divertissement'
}


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
    for category_name, category_url in list(CATEGORIES.items()):

        item = Listitem()
        item.label = category_name
        item.set_callback(list_videos,
                          item_id=item_id,
                          category_url=category_url,
                          page='0')
        item_post_treatment(item)
        yield item


@Route.register
def list_videos(plugin, item_id, category_url, page, **kwargs):

    resp = urlquick.get(category_url % page)
    root = resp.parse()

    for video_datas in root.iterfind(".//div[@class='panel-item']"):
        video_title = video_datas.find('.//h3').find('.//a').text
        video_image = video_datas.find('.//img').get('src')
        video_url = URL_ROOT + '/' + video_datas.find('.//a').get('href')

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = video_image

        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_label=LABELS[item_id] + ' - ' + item.label,
                          video_url=video_url)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item

    # More videos...
    yield Listitem.next_page(item_id=item_id,
                             page=str(int(page) + 21),
                             category_url=category_url)


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_url,
                  download_mode=False,
                  video_label=None,
                  **kwargs):

    resp = urlquick.get(video_url, timeout=20, max_age=-1)

    list_streams_datas = re.compile(r'file: \'(.*?)\'').findall(resp.text)

    stream_url = ''
    for stream_datas in list_streams_datas:
        if 'http' in stream_datas:
            stream_url = stream_datas
            break

    if download_mode:
        return download.download_video(stream_url, video_label)
    return stream_url


def live_entry(plugin, item_id, item_dict, **kwargs):
    return get_live_url(plugin, item_id, item_id.upper(), item_dict)


@Resolver.register
def get_live_url(plugin, item_id, video_id, item_dict, **kwargs):

    live_html = urlquick.get(URL_LIVE,
                             headers={'User-Agent': web_utils.get_random_ua()},
                             max_age=-1)
    list_url_stream = re.compile(r'file"\: "(.*?)"').findall(live_html.text)
    url_live = ''
    for url_stream_data in list_url_stream:
        if 'm3u8' in url_stream_data:
            url_live = url_stream_data
    return url_live
