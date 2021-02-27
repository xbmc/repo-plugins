# -*- coding: utf-8 -*-
"""
    Catch-up TV & More
    Copyright (C) 2017  SylvainCecchetto

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

import htmlement
from codequick import Route, Resolver, Listitem

from resources.lib import resolver_proxy
from resources.lib import download
from resources.lib.menu_utils import item_post_treatment

import base64
import json
import re
# Working for Python 2/3
try:
    from urllib.parse import quote_plus
except ImportError:
    from urllib import quote_plus
import urlquick

# TO DO
# Some video Sky sports required account (add account)

URL_LIVE_SKYNEWS = 'https://news.sky.com/watch-live'

URL_IMG_YOUTUBE = 'https://i.ytimg.com/vi/%s/hqdefault.jpg'
# video_id

URL_VIDEOS_CHANNEL_YT = 'https://www.youtube.com/channel/%s/videos'
# Channel_name

URL_VIDEOS_SKYSPORTS = 'http://www.skysports.com/watch/video'

URL_ROOT_SKYSPORTS = 'http://www.skysports.com'

URL_OOYALA_VOD = 'https://player.ooyala.com/sas/player_api/v2/authorization/' \
    'embed_code/%s/%s?embedToken=%s&device=html5&domain=www.skysports.com'
# pcode, Videoid, embed_token

URL_PCODE_EMBED_TOKEN = 'http://www.skysports.com/watch/video/auth/v4/23'

VIDEO_PER_PAGE = 12


@Route.register
def list_categories(plugin, item_id, **kwargs):

    if item_id == 'skynews':
        item = Listitem()
        item.label = 'Skynews (youtube)'
        item.set_callback(list_videos_youtube,
                          item_id=item_id,
                          channel_youtube='UCoMdktPbSTixAyNGwb-UYkQ')
        item_post_treatment(item)
        yield item

    elif item_id == 'skysports':

        item = Listitem()
        item.label = 'Soccer AM (youtube)'
        item.set_callback(list_videos_youtube,
                          item_id=item_id,
                          channel_youtube='UCE97AW7eR8VVbVPBy4cCLKg')
        item_post_treatment(item)
        yield item

        item = Listitem()
        item.label = 'Sky Sports Football (youtube)'
        item.set_callback(list_videos_youtube,
                          item_id=item_id,
                          channel_youtube='UCNAf1k0yIjyGu3k9BwAg3lg')
        item_post_treatment(item)
        yield item

        item = Listitem()
        item.label = 'Sky Sports (youtube)'
        item.set_callback(list_videos_youtube,
                          item_id=item_id,
                          channel_youtube='UCTU_wC79Dgi9rh4e9-baTqA')
        item_post_treatment(item)
        yield item

        resp = urlquick.get(URL_VIDEOS_SKYSPORTS)
        root = resp.parse()

        categories = []
        for category_datas in root.iterfind(".//a[@class='page-nav__link']"):
            category_title = category_datas.text
            if category_title not in categories:
                categories.append(category_title)
                _category_url = URL_ROOT_SKYSPORTS + category_datas.get('href')
                resp2 = urlquick.get(_category_url)
                root2 = resp2.parse()
                try:
                    category_url = URL_ROOT_SKYSPORTS + root2.find(
                        './/div[@class-id="loadmore1"]').get("data-url")
                    category_url = category_url.replace('#', '')
                except AttributeError:
                    continue

                item = Listitem()
                item.label = category_title
                item.set_callback(list_videos_sports,
                                  item_id=item_id,
                                  category_url=category_url,
                                  start=0,
                                  end=VIDEO_PER_PAGE)
                item_post_treatment(item)
                yield item


@Route.register
def list_videos_youtube(plugin, item_id, channel_youtube, **kwargs):

    # TODO add favoris ?
    yield Listitem.youtube(channel_youtube)


@Route.register
def list_videos_sports(plugin, item_id, category_url, start, end, **kwargs):

    parser = htmlement.HTMLement()
    resp = urlquick.get(category_url.format(start=start, end=end))
    parser.feed(resp.json())  # json unescaped string needed
    root = parser.close()

    at_least_one_item = 0

    for video_datas in root.iterfind(".//div[@class='polaris-tile__inner']"):
        video_title = video_datas.find('.//h2').find('.//a').text.strip()
        video_image = video_datas.find('.//img').get('data-src')
        video_url = URL_ROOT_SKYSPORTS + video_datas.find(
            './/h2').find('.//a').get('href')

        at_least_one_item += 1
        item = Listitem()
        item.label = video_title
        item.art['thumb'] = item.art['landscape'] = video_image

        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_url=video_url)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item

    if at_least_one_item == VIDEO_PER_PAGE:
        # More videos...
        yield Listitem.next_page(item_id=item_id,
                                 category_url=category_url,
                                 start=end,
                                 end=end + VIDEO_PER_PAGE)
    elif at_least_one_item == 0:
        plugin.notify(plugin.localize(30718), '')
        yield False


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_url,
                  download_mode=False,
                  **kwargs):

    data_embed_token = urlquick.get(URL_PCODE_EMBED_TOKEN).json()
    pcode = re.compile(
        r'sas/embed_token/(.*?)/all').findall(data_embed_token)[0]
    data_embed_token = quote_plus(data_embed_token.replace('"', ''))

    resp = urlquick.get(video_url)
    root = resp.parse()
    try:
        video_id = root.find(
            './/div[@data-provider="ooyala"]').get('data-sdc-video-id')
    except AttributeError:
        plugin.notify('ERROR', plugin.localize(30712))
        return False

    video_vod = urlquick.get(URL_OOYALA_VOD %
                             (pcode, video_id, data_embed_token)).text
    json_parser = json.loads(video_vod)
    streams_base64 = []
    if 'streams' in json_parser["authorization_data"][video_id]:
        for stream in json_parser["authorization_data"][video_id]["streams"]:
            url_base64 = stream["url"]["data"]
            if url_base64:
                streams_base64.append(url_base64)

        final_video_url = base64.standard_b64decode(streams_base64[-1])

        if download_mode:
            return download.download_video(final_video_url)

        return final_video_url


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_LIVE_SKYNEWS)
    live_id = re.compile(r'www.youtube.com/embed/(.*?)\?').findall(
        resp.text)[0]
    return resolver_proxy.get_stream_youtube(plugin, live_id, False)
