# -*- coding: utf-8 -*-
# Copyright: (c) 2017, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals

import re
from builtins import str

import json
import urlquick
from codequick import Listitem, Resolver, Route
from resources.lib import resolver_proxy, web_utils, download
from resources.lib.menu_utils import item_post_treatment

URL_ROOT = 'https://www.rtc.be'

URL_LIVE = URL_ROOT + '/live'

URL_PLAYER = 'https://tvlocales-player.freecaster.com/embed/%s.json'

URL_VIDEOS = URL_ROOT + '/videos'

URL_EMISSIONS = URL_ROOT + '/emissions'

GENERIC_HEADERS = {'User-Agent': web_utils.get_random_ua()}


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
    item.set_callback(list_videos,
                      item_id=item_id,
                      next_url=URL_VIDEOS,
                      page='0')
    item_post_treatment(item)
    yield item

    item = Listitem()
    item.label = plugin.localize(30717)
    item.set_callback(list_programs, item_id=item_id)
    item_post_treatment(item)
    yield item


@Route.register
def list_programs(plugin, item_id, **kwargs):
    resp = urlquick.get(URL_EMISSIONS, headers=GENERIC_HEADERS, max_age=-1)
    root = resp.parse()

    for program_datas in root.iterfind(".//div[@class='col-sm-4']"):
        program_title = program_datas.find('.//h3').text
        program_image = program_datas.find('.//img').get('src')
        program_image = append_schema(program_image)
        program_url = program_datas.find(".//a").get("href")
        program_url = append_schema(program_url)

        item = Listitem()
        item.label = program_title
        item.art['thumb'] = item.art['landscape'] = program_image
        item.set_callback(list_videos,
                          item_id=item_id,
                          next_url=program_url,
                          page='0')
        item_post_treatment(item)
        yield item


def append_schema(url):
    if not url.startswith("http://") and not url.startswith("https://"):
        url = URL_ROOT + ("" if url.startswith("/") else "/") + url
    return url


@Route.register
def list_videos(plugin, item_id, next_url, page, **kwargs):
    resp = urlquick.get(next_url + '?lim_un=%s' % page, headers=GENERIC_HEADERS, max_age=-1)
    root = resp.parse()

    for video_datas in root.iterfind(".//div[@class='col-sm-4']"):
        video_title = video_datas.find('.//h3').text
        video_image = video_datas.find('.//img').get('src')
        video_image = append_schema(video_image)
        video_url = video_datas.find('.//a').get('href')
        video_url = append_schema(video_url)

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = item.art['landscape'] = video_image

        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_url=video_url)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item

    yield Listitem.next_page(item_id=item_id,
                             next_url=next_url,
                             page=str(int(page) + 12))


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_url,
                  download_mode=False,
                  **kwargs):
    resp = urlquick.get(video_url, headers=GENERIC_HEADERS, max_age=-1)
    root = resp.parse()

    video_data = root.findall(".//div[@class='freecaster-player']")[0].get('data-fc-token')
    resp = urlquick.get(URL_PLAYER % video_data, headers=GENERIC_HEADERS, max_age=-1)
    json_data = json.loads(resp.text)
    video_url = json_data['video']['src'][0]['src']
    try:
        subtitles = json_data['video']['tracks'][0]['src']
    except KeyError:
        subtitles = None

    if download_mode:
        return download.download_video(video_url)
    return resolver_proxy.get_stream_with_quality(plugin, video_url, subtitles=subtitles)


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    resp = urlquick.get(URL_LIVE, headers=GENERIC_HEADERS, max_age=-1)
    root = resp.parse()

    live_data = root.findall(".//div[@class='freecaster-player']")[0].get('data-video-id')
    resp = urlquick.get(URL_PLAYER % live_data, headers=GENERIC_HEADERS, max_age=-1)
    video_url = json.loads(resp.text)['video']['src'][0]['src']

    return resolver_proxy.get_stream_with_quality(plugin, video_url)
