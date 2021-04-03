# -*- coding: utf-8 -*-
# Copyright: (c) 2019, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import json
import re

import inputstreamhelper
from codequick import Listitem, Resolver, Route
import urlquick

from resources.lib import web_utils
from resources.lib.menu_utils import item_post_treatment
from resources.lib.kodi_utils import get_selected_item_art, get_selected_item_label, get_selected_item_info


# TODO
# Find a way for mpd inputstream not protected by DRM to be downloadable by youtube-dl
# Add date info to catch-up tv video

URL_ROOT = "https://www.alsace20.tv"

URL_LIVE = URL_ROOT + "/emb/live1"


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
                item.art['thumb'] = item.art['landscape'] = program_image
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
                item.art['thumb'] = item.art['landscape'] = program_image
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
            item.art['thumb'] = item.art['landscape'] = program_image
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
        item.art['thumb'] = item.art['landscape'] = video_image
        item.info['plot'] = video_plot
        item.set_callback(
            get_video_url,
            item_id=item_id,
            video_url=video_url)
        item_post_treatment(item, is_playable=True, is_downloadable=False)
        yield item


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_url,
                  download_mode=False,
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
    item.label = get_selected_item_label()
    item.art.update(get_selected_item_art())
    item.info.update(get_selected_item_info())
    return item


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

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
    item.label = get_selected_item_label()
    item.art.update(get_selected_item_art())
    item.info.update(get_selected_item_info())
    return item
