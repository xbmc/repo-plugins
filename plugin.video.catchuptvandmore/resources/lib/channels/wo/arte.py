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


import json
import re
import urlquick
import xbmcgui


# TO DO
#   Most recent
#   Most viewed

URL_ROOT = 'https://www.arte.tv/%s/'
# Language

URL_REPLAY_ARTE = 'https://api.arte.tv/api/player/v1/config/%s/%s'
# desired_language, videoid

URL_LIVE_ARTE = 'https://api.arte.tv/api/player/v1/livestream/%s'
# Langue, ...

URL_VIDEOS = 'http://www.arte.tv/hbbtvv2/services/web/index.php/OPA/v3/videos/subcategory/%s/page/%s/limit/100/%s'
# VideosCode, Page, language

URL_VIDEOS_2 = 'http://www.arte.tv/hbbtvv2/services/web/index.php/OPA/v3/videos/collection/%s/%s/%s'
# VideosCode, Page, language

DESIRED_LANGUAGE = Script.setting['arte.language']

DESIRED_QUALITY = Script.setting['quality']

CORRECT_MONTH = {
    'Jan': '01',
    'Feb': '02',
    'Mar': '03',
    'Apr': '04',
    'May': '05',
    'Jun': '06',
    'Jul': '07',
    'Aug': '08',
    'Sep': '09',
    'Oct': '10',
    'Nov': '11',
    'Dec': '12'
}


def replay_entry(plugin, item_id):
    """
    First executed function after replay_bridge
    """
    return list_categories(plugin, item_id)


@Route.register
def list_categories(plugin, item_id):
    """
    Build categories listing
    - Tous les programmes
    - Séries
    - Informations
    - ...
    """
    resp = urlquick.get(URL_ROOT % DESIRED_LANGUAGE.lower())
    json_value = re.compile(
        r'_INITIAL_STATE__ \= (.*?)\}\;').findall(resp.text)[0]
    # print 'json_value : ' + repr(json_value)
    json_parser = json.loads(json_value + '}')

    value_code = json_parser['pages']['currentCode']
    for category_datas in json_parser['pages']['list'][value_code]['zones']:
        if 'category' in category_datas['code']['name']:
            category_title = category_datas['title']
            category_url = category_datas['link']['url']

            item = Listitem()
            item.label = category_title
            item.set_callback(
                list_sub_categories,
                item_id=item_id,
                category_url=category_url)
            yield item


@Route.register
def list_sub_categories(plugin, item_id, category_url):
    """
    Build programs listing
    - Les feux de l'amour
    - ...
    """
    resp = urlquick.get(category_url)
    json_value = re.compile(
        r'_INITIAL_STATE__ \= (.*?)\}\;').findall(resp.text)[0]
    json_parser = json.loads(json_value + '}')

    value_code = json_parser['pages']['currentCode']
    for sub_category_datas in json_parser['pages']['list'][value_code]['zones']:
        if 'subcategory' in sub_category_datas['code']['name']:
            sub_category_title = sub_category_datas['title']
            sub_category_url = sub_category_datas['link']['page']

            item = Listitem()
            item.label = sub_category_title
            item.set_callback(
                list_videos_sub_category,
                item_id=item_id,
                sub_category_url=sub_category_url,
                page='1')
            yield item

        elif sub_category_datas['code']['name'] == 'playlists' or \
                sub_category_datas['code']['name'] == 'collections' or \
                sub_category_datas['code']['name'] == 'magazines':
            sub_category_title = sub_category_datas['title']
            sub_category_code_name = sub_category_datas['code']['name']
            sub_category_url = category_url

            item = Listitem()
            item.label = sub_category_title

            item.set_callback(
                list_programs,
                item_id=item_id,
                sub_category_code_name=sub_category_code_name,
                sub_category_url=sub_category_url)
            yield item
        # else:
        #     # Add Notification (Category Not known)
        #     return None


@Route.register
def list_programs(plugin, item_id, sub_category_code_name, sub_category_url):
    """
    Build programs listing
    - Les feux de l'amour
    - ...
    """
    resp = urlquick.get(sub_category_url)
    json_value = re.compile(
        r'_INITIAL_STATE__ \= (.*?)\}\;').findall(resp.text)[0]
    json_parser = json.loads(json_value + '}')

    value_code = json_parser['pages']['currentCode']
    for sub_category_datas in json_parser['pages']['list'][value_code]['zones']:
        if sub_category_datas['code']['name'] == sub_category_code_name:
            for program_datas in sub_category_datas['data']:
                program_title = program_datas['title']
                program_id = program_datas['programId']
                program_image = ''
                for image_datas in program_datas['images']['landscape']['resolutions']:
                    program_image = image_datas['url']

                item = Listitem()
                item.label = program_title
                item.art['thumb'] = program_image
                item.set_callback(
                    list_videos_program,
                    item_id=item_id,
                    sub_category_code_name=sub_category_code_name,
                    program_id=program_id)
                yield item


@Route.register
def list_videos_sub_category(plugin, item_id, sub_category_url, page):

    resp = urlquick.get(URL_VIDEOS % (sub_category_url, page, DESIRED_LANGUAGE.lower()))
    json_parser = json.loads(resp.text)

    for video_datas in json_parser['videos']:
        if video_datas['subtitle'] is not None:
            video_title = video_datas['title'] + ' - ' + video_datas['subtitle']
        else:
            video_title = video_datas['title']
        video_id = video_datas['programId']
        vudeo_image = video_datas['imageUrl']
        video_duration = video_datas["durationSeconds"]
        video_plot = video_datas["shortDescription"]
        date_value = video_datas["videoRightsBegin"].split(' ')
        day = date_value[1]
        try:
            month = CORRECT_MONTH[date_value[2]]
        except Exception:
            month = '00'
        year = date_value[3]
        date_value = '-'.join((year, month, day))

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = vudeo_image
        item.info['duration'] = video_duration
        item.info['plot'] = video_plot
        item.info.date(date_value, '%Y-%m-%d')

        item.context.script(
            get_video_url,
            plugin.localize(LABELS['Download']),
            item_id=item_id,
            video_id=video_id,
            video_label=LABELS[item_id] + ' - ' + item.label,
            download_mode=True)

        item.set_callback(
            get_video_url,
            item_id=item_id,
            video_id=video_id)
        yield item

    if int(json_parser['meta']['pages']) > int(page):
        yield Listitem.next_page(
            item_id=item_id,
            sub_category_url=sub_category_url,
            page=str(int(page) + 1))


@Route.register
def list_videos_program(plugin, item_id, sub_category_code_name, program_id):

    resp = urlquick.get(URL_VIDEOS_2 % (sub_category_code_name.upper(), program_id, DESIRED_LANGUAGE.lower()))
    json_parser = json.loads(resp.text)

    for video_datas in json_parser['videos']:
        if video_datas['subtitle'] is not None:
            video_title = video_datas['title'] + ' - ' + video_datas['subtitle']
        else:
            video_title = video_datas['title']
        video_id = video_datas['programId']
        vudeo_image = video_datas['imageUrl']
        video_duration = video_datas["durationSeconds"]
        video_plot = video_datas["shortDescription"]
        date_value = video_datas["videoRightsBegin"].split(' ')
        day = date_value[1]
        try:
            month = CORRECT_MONTH[date_value[2]]
        except Exception:
            month = '00'
        year = date_value[3]
        date_value = '-'.join((year, month, day))

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = vudeo_image
        item.info['duration'] = video_duration
        item.info['plot'] = video_plot
        item.info.date(date_value, '%Y-%m-%d')

        item.context.script(
            get_video_url,
            plugin.localize(LABELS['Download']),
            item_id=item_id,
            video_id=video_id,
            video_label=LABELS[item_id] + ' - ' + item.label,
            download_mode=True)

        item.set_callback(
            get_video_url,
            item_id=item_id,
            video_id=video_id)
        yield item


@Resolver.register
def get_video_url(
        plugin, item_id, video_id, download_mode=False, video_label=None):

    resp = urlquick.get(URL_REPLAY_ARTE % (DESIRED_LANGUAGE.lower(), video_id))
    json_parser = json.loads(resp.text)

    url_selected = ''
    stream_datas = json_parser['videoJsonPlayer']['VSR']

    if DESIRED_QUALITY == "DIALOG":
        all_datas_videos_quality = []
        all_datas_videos_path = []

        for video in stream_datas:
            if not video.find("HLS"):
                datas = json_parser['videoJsonPlayer']['VSR'][video]
                all_datas_videos_quality.append(
                    datas['mediaType'] + " (" +
                    datas['versionLibelle'] + ")")
                all_datas_videos_path.append(datas['url'])

        seleted_item = xbmcgui.Dialog().select(
            plugin.localize(LABELS['choose_video_quality']), all_datas_videos_quality)
        if seleted_item > -1:
            url_selected = all_datas_videos_path[seleted_item]
        else:
            return False

    elif DESIRED_QUALITY == "BEST":
        url_selected = stream_datas['HTTPS_SQ_1']['url']
    else:
        url_selected = stream_datas['HTTPS_HQ_1']['url']

    if download_mode:
        return download.download_video(url_selected, video_label)

    return url_selected


def live_entry(plugin, item_id, item_dict):
    return get_live_url(plugin, item_id, item_id.upper(), item_dict)


@Resolver.register
def get_live_url(plugin, item_id, video_id, item_dict):

    if DESIRED_LANGUAGE == 'FR' or DESIRED_LANGUAGE == 'DE':
        resp = urlquick.get(URL_LIVE_ARTE % DESIRED_LANGUAGE.lower())
        json_parser = json.loads(resp.text)
        return json_parser["videoJsonPlayer"]["VSR"]["HLS_SQ_1"]["url"]
    # Add Notification (NOT available in this language)
    return False
