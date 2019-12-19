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

from codequick import Route, Resolver, Listitem, utils, Script

from resources.lib.labels import LABELS
from resources.lib import web_utils
from resources.lib import download
from resources.lib.listitem_utils import item_post_treatment, item2dict

import json
import re
import urlquick

# TO DO
# Fix Replay (DRM)

URL_ROOT = 'http://www.blaze.tv'
# Live
URL_LIVE_JSON = URL_ROOT + '/stream/live/widevine/%s'

# Replay
URL_SHOWS = URL_ROOT + '/series'
# pageId

URL_STREAM = URL_ROOT + '/stream/replay/widevine/%s'
# apiKey, videoId


def replay_entry(plugin, item_id, **kwargs):
    """
    First executed function after replay_bridge
    """
    return list_categories(plugin, item_id)


@Route.register
def list_categories(plugin, item_id, **kwargs):
    """
    Build programs listing
    - Les feux de l'amour
    - ...
    """
    item = Listitem()
    item.label = plugin.localize(LABELS['All programs'])
    item.set_callback(list_programs, item_id=item_id)
    item_post_treatment(item)
    yield item


@Route.register
def list_programs(plugin, item_id, **kwargs):
    """
    Build programs listing
    - Les feux de l'amour
    - ...
    """
    resp = urlquick.get(URL_SHOWS)
    root = resp.parse()

    for program_datas in root.iterfind(".//div[@class='col-sm-4']"):
        program_title = program_datas.find('.//h3').get('title')
        program_image = program_datas.find('.//img').get('data-src')
        program_url = URL_ROOT + program_datas.find('a').get('href')

        item = Listitem()
        item.label = program_title
        item.art['thumb'] = program_image
        item.set_callback(list_seasons,
                          item_id=item_id,
                          program_url=program_url)
        item_post_treatment(item)
        yield item


@Route.register
def list_seasons(plugin, item_id, program_url, **kwargs):

    resp = urlquick.get(program_url, headers={"User-Agent": web_utils.get_random_ua()})
    root = resp.parse("ul", attrs={"class": "nav nav-tabs"})

    for season_datas in root.iterfind(".//h3"):
        season_title = season_datas.text.strip()
        season_url = program_url + '#%s' % season_datas.text.split(' ')[1]

        item = Listitem()
        item.label = season_title
        item.set_callback(list_videos, item_id=item_id, season_url=season_url)
        item_post_treatment(item)
        yield item

    if root.find('.//h2') is not None:
        season_title = 'Series %s' % root.find('.//h2').text.strip()
        season_url = program_url

        item = Listitem()
        item.label = season_title
        item.set_callback(list_videos, item_id=item_id, season_url=season_url)
        item_post_treatment(item)
        yield item


@Route.register
def list_videos(plugin, item_id, season_url, **kwargs):

    resp = urlquick.get(season_url)
    root = resp.parse()

    for video_datas in root.iterfind(
            ".//a[@class='thumbnail video vod-REPLAY play-video-trigger']"):

        video_title = video_datas.find('.//h3').get('title')
        video_image = video_datas.find('.//img').get('data-src')
        video_url = URL_ROOT + video_datas.get('href')

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = video_image

        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_label=LABELS[item_id] + ' - ' + item.label,
                          video_url=video_url)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_url,
                  download_mode=False,
                  video_label=None,
                  **kwargs):

    resp = urlquick.get(video_url)
    stream_id = re.compile(r'blaze\"\,\"uvid\"\:\"(.*?)\"').findall(resp.text)[0]
    resp2 = urlquick.get(URL_STREAM % stream_id,
                         headers={"x-requested-with": "XMLHttpRequest"},
                         max_age=-1)
    json_parser2 = json.loads(resp2.text)
    stream_url = ''
    for stream_datas in json_parser2["playerSource"]["sources"]:
        stream_url = stream_datas["src"]
    if download_mode:
        return download.download_video(stream_url, video_label)
    return stream_url


def live_entry(plugin, item_id, item_dict, **kwargs):
    return get_live_url(plugin, item_id, item_id.upper(), item_dict)


@Resolver.register
def get_live_url(plugin, item_id, video_id, item_dict, **kwargs):

    resp = urlquick.get(URL_ROOT)
    live_id = re.compile(r'href\=\"\/live\/(.*?)\"').findall(resp.text)[0]
    resp2 = urlquick.get(
        URL_LIVE_JSON % live_id,
        headers={"x-requested-with": "XMLHttpRequest"},
        max_age=-1)
    json_parser2 = json.loads(resp2.text)
    resp3 = urlquick.get(
        json_parser2["tokenizer"]["url"],
        headers={
            "Token": json_parser2["tokenizer"]["token"],
            "Token-Expiry": json_parser2["tokenizer"]["expiry"],
            "Uvid": "blaze"
        },
        max_age=-1)
    json_parser3 = json.loads(resp3.text)
    return json_parser3["Streams"]["Adaptive"]
