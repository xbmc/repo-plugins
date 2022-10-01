# -*- coding: utf-8 -*-
# Copyright: (c) 2018, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import re

# noinspection PyUnresolvedReferences
from codequick import Listitem, Resolver, Route
# noinspection PyUnresolvedReferences
from codequick.utils import urljoin_partial
import urlquick

from resources.lib import download, resolver_proxy
from resources.lib.menu_utils import item_post_treatment

URL_ROOT = 'http://www.antennereunion.fr'
url_constructor = urljoin_partial(URL_ROOT)

URL_LIVE = 'https://live-antenne-reunion.zeop.tv/live/c3eds/antreunihd/hls_fta/antreunihd.m3u8'


@Route.register
def list_categories(plugin, item_id, **kwargs):
    resp = urlquick.get(url_constructor("/"))
    root = resp.parse("div", attrs={"class": "content-home"})

    for category in root.iterfind(".//div[@class='content-liste-une']"):
        item = Listitem()
        if category.find(".//h2") is not None:
            item.label = category.findtext(".//h2")
        elif category.find(".//h3") is not None:
            item.label = category.findtext(".//h3")
        item.set_callback(list_videos_in_category,
                          item_id=item_id,
                          category=category)
        item_post_treatment(item)
        yield item

    for category in root.iterfind(".//div[@class='content_emission']"):
        item = Listitem()
        item.label = category.findtext(".//h2")
        item.set_callback(list_videos_in_category,
                          item_id=item_id,
                          category=category)
        item_post_treatment(item)
        yield item


@Route.register
def list_videos_in_category(plugin, item_id, category, **kwargs):
    for emission in category.iterfind(".//div[@class='liste_emission']"):
        video_title = emission.find('.//h3').findtext('.//a')
        video_image = emission.find('.//img').get('src')
        emission_url = url_constructor(emission.find('.//a').get('href'))

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = item.art['landscape'] = video_image
        item.set_callback(list_videos,
                          item_id=item_id,
                          category_url=emission_url)
        yield item


@Route.register
def list_videos(plugin, item_id, category_url, **kwargs):
    resp = urlquick.get(url_constructor(category_url))
    root = resp.parse("div", attrs={"class": "content_news"})

    for video_datas in root.iterfind(".//a"):
        video_title = video_datas.find(".//div[@class='info-profil-rubrique']/span").text
        video_image = video_datas.find('.//img').get('src')
        video_url = url_constructor(video_datas.get('href'))

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
    resp = urlquick.get(video_url, timeout=20, max_age=-1)

    # "url":"https://cdn.jwplayer.com/manifests/OfEl17Oy.m3u8"
    list_streams_data = re.compile(r'"url":"(.*?)\.m3u8"').findall(resp.text)

    stream_url = None
    for url in list_streams_data:
        if 'http' in url:
            stream_url = url + '.m3u8'
            break

    if stream_url is None:
        return False

    if download_mode:
        return download.download_video(stream_url)
    return resolver_proxy.get_stream_with_quality(plugin, stream_url)


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    return resolver_proxy.get_stream_with_quality(plugin, URL_LIVE)
