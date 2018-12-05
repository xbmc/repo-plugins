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

from bs4 import BeautifulSoup as bs

import json
import re
import os
import urlquick
import xbmcgui

# TO DO
# Move WAT to resolver.py (merge with mytf1 code)


URL_ROOT = 'https://www.%s.fr'
# ChannelName

URL_VIDEOS = 'https://www.%s.fr/videos'
# PageId

URL_WAT_BY_ID = 'https://www.wat.tv/embedframe/%s'

URL_VIDEO_STREAM = 'https://www.wat.tv/get/webhtml/%s'

DESIRED_QUALITY = Script.setting['quality']


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
    item = Listitem()
    item.label = plugin.localize(LABELS['All videos'])
    item.set_callback(
        list_videos,
        item_id=item_id,
        page='1')
    yield item


@Route.register
def list_videos(plugin, item_id, page):

    if item_id == 'tvbreizh':
        resp = urlquick.get(URL_VIDEOS % item_id)
    else:
        resp = urlquick.get(URL_VIDEOS % item_id + '?page=%s' % page)
    videos_soup = bs(resp.text, 'html.parser')
    list_videos_datas = videos_soup.find_all(
        'div', class_=re.compile("views-row"))
    for video_datas in list_videos_datas:
        video_title = video_datas.find(
            'span', class_='field-content').find(
            'a').get_text()
        video_plot = ''
        if video_datas.find(
                'div', class_='field-resume'):
            video_plot = video_datas.find(
                'div', class_='field-resume').get_text().strip()
        video_image = URL_ROOT % item_id + \
            video_datas.find('img').get('src')
        video_url = URL_ROOT % item_id + '/' + \
            video_datas.find('a').get('href')

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = video_image
        item.info['plot'] = video_plot

        item.context.script(
            get_video_url,
            plugin.localize(LABELS['Download']),
            item_id=item_id,
            video_url=video_url,
            video_label=LABELS[item_id] + ' - ' + item.label,
            download_mode=True)

        item.set_callback(
            get_video_url,
            item_id=item_id,
            video_url=video_url)
        yield item

    if 'tvbreizh' not in item_id:
        yield Listitem.next_page(
            item_id=item_id,
            page=str(int(page) + 1))


@Resolver.register
def get_video_url(
        plugin, item_id, video_url, download_mode=False, video_label=None):

    resp = urlquick.get(
        video_url,
        headers={'User-Agent': web_utils.get_random_ua},
        max_age=-1)
    video_id = re.compile(
        r'www.wat.tv/embedframe/(.*?)[\"\?]').findall(
            resp.text)[0]
    url_wat_embed = URL_WAT_BY_ID % video_id
    wat_embed_html = urlquick.get(
        url_wat_embed,
        headers={'User-Agent': web_utils.get_random_ua},
        max_age=-1)
    stream_id = re.compile('UVID=(.*?)&').findall(wat_embed_html.text)[0]
    url_json = URL_VIDEO_STREAM % stream_id
    htlm_json = urlquick.get(
        url_json,
        headers={'User-Agent': web_utils.get_random_ua},
        max_age=-1)
    json_parser = json.loads(htlm_json.text)

    # Check DRM in the m3u8 file
    manifest = urlquick.get(
        json_parser["hls"],
        headers={'User-Agent': web_utils.get_random_ua},
        max_age=-1)
    if 'drm' in manifest:
        Script.notify(
            "TEST",
            plugin.localize(LABELS['drm_notification']),
            Script.NOTIFY_INFO)
        return False

    root = os.path.dirname(json_parser["hls"])

    manifest = urlquick.get(
        json_parser["hls"].split('&max_bitrate=')[0],
        headers={'User-Agent': web_utils.get_random_ua},
        max_age=-1)

    lines = manifest.text.splitlines()
    final_video_url = ''
    all_datas_videos_quality = []
    all_datas_videos_path = []
    for k in range(0, len(lines) - 1):
        if 'RESOLUTION=' in lines[k]:
            all_datas_videos_quality.append(
                re.compile(
                    r'RESOLUTION=(.*?),').findall(
                    lines[k])[0])
            all_datas_videos_path.append(
                root + '/' + lines[k + 1])
    if DESIRED_QUALITY == "DIALOG":
        seleted_item = xbmcgui.Dialog().select(
            plugin.localize(LABELS['choose_video_quality']),
            all_datas_videos_quality)
        final_video_url = all_datas_videos_path[seleted_item]
    elif DESIRED_QUALITY == 'BEST':
        # Last video in the Best
        for k in all_datas_videos_path:
            url = k
        final_video_url = url
    else:
        final_video_url = all_datas_videos_path[0]

    if download_mode:
        return download.download_video(final_video_url, video_label)
    return final_video_url
