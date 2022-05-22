# -*- coding: utf-8 -*-
# Copyright: (c) 2018, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals

import json
import re

import urlquick
from codequick import Listitem, Resolver, Route, Script
from resources.lib import download
from resources.lib.menu_utils import item_post_treatment

# TO DO
# Add replay

URL_ROOT = 'https://www.raiplay.it'

# Live
URL_LIVE = URL_ROOT + '/dirette/%s.json'
# Channel

URL_REPLAYS = URL_ROOT + '/dl/RaiTV/RaiPlayMobile/Prod/Config/programmiAZ-elenco.json'

URL_HOMEPAGE = URL_ROOT + '/index.json'


# ROOT_______________
@Route.register
def list_root(plugin, item_id, **kwargs):
    """
    Build inital menu.
    """

    # all videos
    item = Listitem()
    item.label = "A-Z"
    item.set_callback(list_letters,
                      item_id=item_id)
    item_post_treatment(item)
    yield item

    # home page categories
    item = Listitem()
    item.label = "Home Page"
    item.set_callback(list_homepage,
                      item_id=item_id)
    item_post_treatment(item)
    yield item

    # Search feature
    item = Listitem.search(search)
    item_post_treatment(item)
    yield item


# SEARCH_______________
@Route.register
def search(plugin, search_query, **kwargs):
    resp = urlquick.get(URL_REPLAYS)
    json_parser = json.loads(resp.text)

    for letter_group in json_parser.values():
        for program_datas in letter_group:
            if search_query.lower() in program_datas["name"].lower():
                if "PathID" in program_datas:
                    program_title = program_datas["name"]
                    program_image = ''
                    if "images" in program_datas:
                        if 'landscape' in program_datas["images"]:
                            program_image = URL_ROOT + program_datas["images"][
                                "landscape"].replace('/resizegd/[RESOLUTION]', '')
                    program_url = program_datas["PathID"]
                    # replace trailing '/?json' by '.json'
                    program_url = '.'.join(program_url.rsplit('/?', 1))

                    item = Listitem()
                    item.label = program_title
                    item.art['thumb'] = item.art['landscape'] = program_image
                    item.set_callback(list_dispatcher,
                                      item_id=None,
                                      program_url=program_url,
                                      program_image=program_image)
                    item_post_treatment(item)
                    yield item


# HOMEPAGE_______________
@Route.register
def list_homepage(plugin, item_id, **kwargs):
    """
    Build homepage categories
    """
    resp = urlquick.get(URL_HOMEPAGE)
    json_parser = json.loads(resp.text)

    for category in json_parser["contents"]:
        category_title = category["name"]
        try:
            category_contents = category["contents"]
        except KeyError:
            continue

        item = Listitem()
        item.label = category_title
        item.set_callback(list_hp_programs,
                          item_id=item_id,
                          category_contents=category_contents)
        item_post_treatment(item)
        yield item


@Route.register
def list_hp_programs(plugin, item_id, category_contents, **kwargs):
    """
    Build programs listing
    - Imma Tataranni
    - ...
    """
    for program_datas in category_contents:
        if "path_id" in program_datas:
            program_title = program_datas["name"]
            program_image = ''
            if "images" in program_datas:
                if 'landscape' in program_datas["images"]:
                    program_image = URL_ROOT + program_datas["images"][
                        "landscape"].replace('/resizegd/[RESOLUTION]', '')
            program_url = URL_ROOT + program_datas["path_id"]
            # replace trailing '/?json' by '.json'
            program_url = '.'.join(program_url.rsplit('/?', 1))

            item = Listitem()
            item.label = program_title
            item.art['thumb'] = item.art['landscape'] = program_image
            item.set_callback(list_dispatcher,
                              item_id=item_id,
                              program_url=program_url,
                              program_image=program_image)
            item_post_treatment(item)
            yield item


# A-Z_______________
@Route.register
def list_letters(plugin, item_id, **kwargs):
    """
    Build letter
    - A
    - B
    - ....
    """
    resp = urlquick.get(URL_REPLAYS)
    json_parser = json.loads(resp.text)

    for letter_title in sorted(json_parser.keys()):
        item = Listitem()
        item.label = letter_title
        item.set_callback(list_AZ_programs,
                          item_id=item_id,
                          letter_title=letter_title)
        item_post_treatment(item)
        yield item


@Route.register
def list_AZ_programs(plugin, item_id, letter_title, **kwargs):
    """
    Build programs listing
    - Les feux de l'amour
    - ...
    """
    resp = urlquick.get(URL_REPLAYS)
    json_parser = json.loads(resp.text)

    for program_datas in json_parser[letter_title]:
        if "PathID" in program_datas:
            program_title = program_datas["name"]
            program_image = ''
            if "images" in program_datas:
                if 'landscape' in program_datas["images"]:
                    program_image = URL_ROOT + program_datas["images"][
                        "landscape"].replace('/resizegd/[RESOLUTION]', '')
            program_url = program_datas["PathID"]
            # replace trailing '/?json' by '.json'
            program_url = '.'.join(program_url.rsplit('/?', 1))

            item = Listitem()
            item.label = program_title
            item.art['thumb'] = item.art['landscape'] = program_image
            item.set_callback(list_dispatcher,
                              item_id=item_id,
                              program_url=program_url,
                              program_image=program_image)
            item_post_treatment(item)
            yield item


# COMMON_______________
@Route.register
def list_dispatcher(plugin, item_id, program_url, program_image, **kwargs):
    resp = urlquick.get(program_url)
    json_parser = json.loads(resp.text)

    program_name = json_parser["name"]
    program_plot = json_parser["program_info"]["description"]

    blocks = json_parser["blocks"]
    if len(blocks) > 1:
        for item in list_blocks(plugin, item_id, program_name, program_plot, program_image, blocks):
            yield item
    elif len(blocks[0]["sets"]) > 1:
        for item in list_sets(plugin, item_id, program_name, program_plot, program_image, blocks[0]["sets"]):
            yield item
    else:
        for item in list_videos(plugin, item_id, program_name, blocks[0]["sets"][0]):
            yield item


@Route.register
def list_blocks(plugin, item_id, program_name, program_plot, program_image, blocks, **kwargs):
    for block in blocks:
        item = Listitem()
        item.label = block["name"]
        item.art['thumb'] = item.art['landscape'] = program_image
        item.info['plot'] = program_plot
        item.set_callback(list_sets,
                          item_id=item_id,
                          program_name=program_name,
                          program_plot=program_plot,
                          program_image=program_image,
                          sets=block["sets"])
        item_post_treatment(item)
        yield item


@Route.register
def list_sets(plugin, item_id, program_name, program_plot, program_image, sets, **kwargs):
    if len(sets) > 1:
        for video_set in sets:
            item = Listitem()
            item.label = video_set["name"]
            item.art['thumb'] = item.art['landscape'] = program_image
            item.info['plot'] = program_plot
            item.set_callback(list_videos,
                              item_id=item_id,
                              program_name=program_name,
                              video_set=video_set)
            item_post_treatment(item)
            yield item
    else:
        for item in list_videos(plugin, item_id, program_name, sets[0]):
            yield item


@Route.register
def list_videos(plugin, item_id, program_name, video_set, **kwargs):
    has_contents = False
    try:
        url_videos = URL_ROOT + video_set["path_id"]
        has_contents = True
    except Exception:
        pass

    if has_contents:
        resp2 = urlquick.get(url_videos)
        json_parser2 = json.loads(resp2.text)

        for video_datas in json_parser2["items"]:
            video_title = program_name + ' ' + video_datas[
                'name'] + ' ' + video_datas['subtitle']
            video_image = URL_ROOT + video_datas["images"]["landscape"].replace(
                '/resizegd/[RESOLUTION]', '')
            duration_value = video_datas['duration'].split(':')
            video_duration = 0
            if len(duration_value) > 2:
                video_duration = int(duration_value[0]) * 3600 + int(
                    duration_value[1]) * 60 + int(duration_value[2])
            elif len(duration_value) > 1:
                video_duration = int(duration_value[0]) * 60 + int(
                    duration_value[1])
            video_url = video_datas['video_url']

            item = Listitem()
            item.label = video_title
            item.art['thumb'] = item.art['landscape'] = video_image
            item.info['duration'] = video_duration
            item.info['plot'] = video_datas.get("description", program_name)
            item.params['title'] = video_title

            # subtitles
            try:
                weblink = video_datas['weblink']
                weblink = weblink.rsplit('.', 1)[0] + '.json'
                resp3 = urlquick.get(URL_ROOT + weblink)
                json_parser3 = json.loads(resp3.text)
                subtitles = json_parser3['video']['subtitlesArray']
                item.params['subtitles'] = subtitles
            except Exception:
                Script.log('[raiplay.py] Problem getting subtitles.')

            item.set_callback(get_video_url,
                              item_id=item_id,
                              video_url=video_url)
            item_post_treatment(item, is_playable=True, is_downloadable=True)
            yield item


@Resolver.register
def get_video_url(plugin, item_id, video_url, download_mode=False, **kwargs):
    if download_mode:
        return download.download_video(video_url)

    item = Listitem()
    item.label = kwargs.get('title', 'unknown')
    item.path = video_url
    if kwargs.get('subtitles') and plugin.setting.get_boolean('active_subtitle'):
        item.subtitles = [URL_ROOT + sub['url'] for sub in kwargs['subtitles']]
    return item


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    resp = urlquick.get(URL_LIVE % item_id, max_age=-1).json()
    return resp['video']['content_url']
