# -*- coding: utf-8 -*-
# Copyright: (c) 2017, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals

from codequick import Listitem, Resolver, Route
import urlquick

from resources.lib import download
from resources.lib.menu_utils import item_post_treatment


URL_ROOT = 'https://news.tbs.co.jp'

URL_CONTENT = URL_ROOT + '/digest/%s.html'
# content

URL_STREAM = 'https://flvstream.tbs.co.jp/flvfiles/_definst_/newsi/digest/%s_1m.mp4/playlist.m3u8'
# content

NEWS_CONTENT = ['nb', '23', 'nst', 'jnn']


@Route.register
def list_categories(plugin, item_id, **kwargs):
    """
    Build categories listing
    - Tous les programmes
    - Séries
    - Informations
    - ...
    """
    category_title = 'TBS ニュース'
    item = Listitem()
    item.label = category_title
    item.set_callback(list_videos_news, item_id=item_id)
    item_post_treatment(item)
    yield item

    category_title = 'TBS ニュース - 気象'
    item = Listitem()
    item.label = category_title
    item.set_callback(list_videos_weather, item_id=item_id)
    item_post_treatment(item)
    yield item


@Route.register
def list_videos_news(plugin, item_id, **kwargs):

    for content in NEWS_CONTENT:
        resp = urlquick.get(URL_CONTENT % content)
        root = resp.parse()
        video_news_datas = root.find(".//div[@class='cp-digestMovie']")

        video_title = video_news_datas.findall(".//div[@class='ls__label']")[0].text
        video_image = ''
        for video_image_datas in video_news_datas.findall(".//div"):
            if video_image_datas.get("tbs-player") is not None:
                video_image = URL_ROOT + video_image_datas.get('splashUrl')
        video_url = URL_STREAM % content

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = item.art['landscape'] = video_image

        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_url=video_url)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item


@Route.register
def list_videos_weather(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_CONTENT % 'weather')
    root = resp.parse()
    video_weather_datas = root.find(".//div[@class='cp-digestMovie']")

    video_title = video_weather_datas.findall(".//div[@class='ls__label']")[0].text
    video_image = ''
    for video_image_datas in video_weather_datas.findall(".//div"):
        if video_image_datas.get("tbs-player") is not None:
            video_image = URL_ROOT + video_image_datas.get('splashUrl')
    video_url = URL_STREAM % 'weather'

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
    if download_mode:
        return download.download_video(video_url)
    return video_url
