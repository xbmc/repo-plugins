# -*- coding: utf-8 -*-
"""
    Catch-up TV & More
    Copyright (C) 2019  SylvainCecchetto

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
from resources.lib.listitem_utils import item_post_treatment, item2dict

import inputstreamhelper
import json
import re
import urlquick

# TODO
# Find a way for mpd inputstream not protected by DRM to be downloadable by youtube-dl
# Add date info to catch-up tv video

URL_ROOT = "https://www.alsace20.tv"

URL_LIVE = URL_ROOT + "/emb/live1"


def replay_entry(plugin, item_id, **kwargs):
    """
    First executed function after replay_bridge
    """
    return list_categories(plugin, item_id)


@Route.register
def list_categories(plugin, item_id, **kwargs):
    """
    Build categories listing
    - ...
    """
    resp = urlquick.get(URL_ROOT)
    root = resp.parse("ul", attrs={"class": "menu-vod hidden-xs"})

    for category_datas in root.iterfind(".//li"):
        category_name = category_datas.find('.//a').text
        if '#' in category_datas.find('.//a').get('href'):
            category_url = URL_ROOT
        else:
            category_url = URL_ROOT + category_datas.find('.//a').get('href')

        item = Listitem()
        item.label = category_name
        item.set_callback(
            list_programs, item_id=item_id, category_url=category_url)
        item_post_treatment(item)
        yield item


@Route.register
def list_programs(plugin, item_id, category_url, **kwargs):
    """
    Build programs listing
    - ...
    """
    resp = urlquick.get(category_url)
    root = resp.parse("div", attrs={"class": "emissions hidden-xs"})

    for program_datas in root.iterfind(".//a"):
        if 'VOD/est' in category_url:
            if 'Est' in program_datas.get('href').split('/')[2]:
                program_name = program_datas.find(
                    ".//div[@class='title']").text
                program_image = URL_ROOT + re.compile(r'url\((.*?)\)').findall(
                    program_datas.find(".//div[@class='bg']").get('style'))[0]
                program_url = URL_ROOT + program_datas.get('href')

                item = Listitem()
                item.label = program_name
                item.art['thumb'] = program_image
                item.set_callback(
                    list_videos, item_id=item_id, program_url=program_url)
                item_post_treatment(item)
                yield item
        elif 'VOD' in category_url:
            if program_datas.get('href').split('/')[2] in category_url:
                program_name = program_datas.find(
                    ".//div[@class='title']").text
                program_image = URL_ROOT + re.compile(r'url\((.*?)\)').findall(
                    program_datas.find(".//div[@class='bg']").get('style'))[0]
                program_url = URL_ROOT + program_datas.get('href')

                item = Listitem()
                item.label = program_name
                item.art['thumb'] = program_image
                item.set_callback(
                    list_videos, item_id=item_id, program_url=program_url)
                item_post_treatment(item)
                yield item
        else:
            program_name = program_datas.find(".//div[@class='title']").text
            program_image = URL_ROOT + re.compile(r'url\((.*?)\)').findall(
                program_datas.find(".//div[@class='bg']").get('style'))[0]
            program_url = URL_ROOT + program_datas.get('href')

            item = Listitem()
            item.label = program_name
            item.art['thumb'] = program_image
            item.set_callback(
                list_videos, item_id=item_id, program_url=program_url)
            item_post_treatment(item)
            yield item


@Route.register
def list_videos(plugin, item_id, program_url, **kwargs):

    resp = urlquick.get(program_url)
    root = resp.parse("ul", attrs={"class": "list-vids"})

    for video_datas in root.iterfind(".//li"):
        video_title = video_datas.find('.//h2').text
        video_image = URL_ROOT + '/videoimages/' + video_datas.find(
            ".//div[@class='img']").get('data-img')
        video_plot = ''
        if video_datas.find(".//div[@class='resume']").text is not None:
            video_plot = video_datas.find(
                ".//div[@class='resume']").text.strip()
        video_url = URL_ROOT + video_datas.find('.//a').get('href')

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = video_image
        item.info['plot'] = video_plot
        item.set_callback(
            get_video_url,
            item_id=item_id,
            video_label=LABELS[item_id] + ' - ' + item.label,
            video_url=video_url,
            item_dict=item2dict(item))
        item_post_treatment(item, is_playable=True, is_downloadable=False)
        yield item


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_url,
                  item_dict,
                  download_mode=False,
                  video_label=None,
                  **kwargs):

    is_helper = inputstreamhelper.Helper('mpd')
    if not is_helper.check_inputstream():
        return False

    resp = urlquick.get(
        video_url, headers={"User-Agent": web_utils.get_random_ua()}, max_age=-1)
    root = resp.parse()
    url_stream_datas = URL_ROOT + root.find(".//div[@class='HDR_VISIO']").get(
        "data-url") + "&mode=html"

    resp2 = urlquick.get(
        url_stream_datas,
        headers={"User-Agent": web_utils.get_random_ua()},
        max_age=-1)
    json_parser = json.loads(resp2.text)

    item = Listitem()
    item.path = json_parser["files"]["auto"]
    item.property["inputstreamaddon"] = "inputstream.adaptive"
    item.property["inputstream.adaptive.manifest_type"] = "mpd"
    if "label" in item_dict:
        item.label = item_dict["label"]
    if "info" in item_dict:
        item.info.update(item_dict["info"])
    if "art" in item_dict:
        item.art.update(item_dict["art"])
    return item


def live_entry(plugin, item_id, item_dict, **kwargs):
    return get_live_url(plugin, item_id, item_id.upper(), item_dict)


@Resolver.register
def get_live_url(plugin, item_id, video_id, item_dict, **kwargs):

    is_helper = inputstreamhelper.Helper('mpd')
    if not is_helper.check_inputstream():
        return False

    resp = urlquick.get(
        URL_LIVE, headers={"User-Agent": web_utils.get_random_ua()}, max_age=-1)
    root = resp.parse()
    url_live_datas = URL_ROOT + root.find(".//div[@class='HDR_VISIO']").get(
        "data-url") + "&mode=html"

    resp2 = urlquick.get(
        url_live_datas,
        headers={"User-Agent": web_utils.get_random_ua()},
        max_age=-1)
    json_parser = json.loads(resp2.text)

    item = Listitem()
    item.path = json_parser["files"]["auto"]
    item.property["inputstreamaddon"] = "inputstream.adaptive"
    item.property["inputstream.adaptive.manifest_type"] = "mpd"
    if item_dict:
        if "label" in item_dict:
            item.label = item_dict["label"]
        if "info" in item_dict:
            item.info.update(item_dict["info"])
        if "art" in item_dict:
            item.art.update(item_dict["art"])
    else:
        item.label = LABELS[item_id]
        item.art["thumb"] = ""
        item.art["icon"] = ""
        item.art["fanart"] = ""
        item.info["plot"] = LABELS[item_id]
    return item
