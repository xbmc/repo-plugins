# -*- coding: utf-8 -*-
# Copyright: (c) 2019, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
from builtins import str
import re
import json

from codequick import Listitem, Resolver, Route
import urlquick

from resources.lib import download
from resources.lib.menu_utils import item_post_treatment
from resources.lib import resolver_proxy, web_utils

URL_ROOT = 'https://www.sudouest.fr'
URL_ROOT_TVPI = URL_ROOT + '/lachainetv7'

GENERIC_HEADERS = {"User-Agent": web_utils.get_random_ua()}


@Route.register
def list_categories(plugin, item_id, **kwargs):
    """
    Build categories listing
    - ...
    """
    resp = urlquick.get(URL_ROOT_TVPI, headers=GENERIC_HEADERS)
    root = resp.parse()

    for category in root.iterfind(".//section[@class=' gutter base-margin-bottom sm-base-padding-right sm-base-padding-left']"):
        item = Listitem()
        item.label = category.find(".//div[@class='section-title-text base-margin-bottom']").text
        item.set_callback(list_videos, category)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item


@Route.register
def list_videos(plugin, category, **kwargs):
    for video_datas in category.iterfind(".//article[@class='article ']"):
        video_title = video_datas.find('.//a').get('title')
        video_page = URL_ROOT + video_datas.find('.//a').get('href')
        picture_source = video_datas.find('.//img').get('data-lazy').replace('&quote;', '"')
        video_image = re.compile(r'src\"(.*?)\"').findall(picture_source)[0].replace('\\', '')
        video_date = re.compile(r'(.*?)T').findall(video_datas.find(".//meta").get('content'))[0]

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = item.art['landscape'] = video_image
        item.info.date(video_date, "%Y-%m-%d")
        item.set_callback(get_video_url, video_page=video_page)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item


@Resolver.register
def get_video_url(plugin, video_page, download_mode=False, **kwargs):
    resp = urlquick.get(video_page)
    video_url = resp.parse().findall(".//figure")[0].find('.//iframe').get('src')

    resp = urlquick.get(video_url)
    final_url = re.compile(r'\"mp4_720\"\:\"(.*?)\"').findall(resp.text)[0].replace('\\', '')

    if download_mode:
        return download.download_video(final_url)
    return final_url


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    resp = urlquick.get(URL_ROOT_TVPI, headers=GENERIC_HEADERS, max_age=-1)
    root = resp.parse('iframe', attrs={"class": "iframe-responsive iframe-16-9"})
    url_player = 'https:' + root.get('src')
    player = urlquick.get(url_player, headers=GENERIC_HEADERS, max_age=-1)
    data_json = json.loads(re.compile(r'DtkPlayer.init\((.*?)\, \{\"topic').findall(player.text)[0])
    video_url = data_json['video']['media_sources']['live']['src']

    return resolver_proxy.get_stream_with_quality(plugin, video_url)
