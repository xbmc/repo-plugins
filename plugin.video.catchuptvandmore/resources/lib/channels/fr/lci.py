# -*- coding: utf-8 -*-
"""
    Catch-up TV & More
    Original work (C) JUL1EN094, SPM, SylvainCecchetto
    Copyright (C) 2016  SylvainCecchetto

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

from builtins import str
from builtins import range
from codequick import Route, Resolver, Listitem, utils, Script

from resources.lib.labels import LABELS
from resources.lib import web_utils
from resources.lib import download
from resources.lib.menu_utils import item_post_treatment

# Verify md5 still present in hashlib python 3 (need to find another way if it is not the case)
# https://docs.python.org/3/library/hashlib.html
from hashlib import md5

import json
import os
import re
import urlquick
from kodi_six import xbmcgui

# TO DO
# Add aired, date, duration etc...
# Rework get_video_url (remove code not needed)

URL_ROOT = utils.urljoin_partial("http://www.tf1.fr")

URL_LCI_REPLAY = "http://www.lci.fr/emissions"
URL_LCI_ROOT = "http://www.lci.fr"

URL_VIDEO_STREAM_2 = 'https://delivery.tf1.fr/mytf1-wrd/%s?format=%s'
# videoId, format['hls', 'dash']

URL_VIDEO_STREAM = 'https://www.wat.tv/get/webhtml/%s'

DESIRED_QUALITY = Script.setting['quality']


def replay_entry(plugin, item_id, **kwargs):
    """
    First executed function after replay_bridge
    """
    return list_programs(plugin, item_id)


@Route.register
def list_programs(plugin, item_id, **kwargs):
    """
    Build programs listing
    - Les feux de l'amour
    - ...
    """
    resp = urlquick.get(URL_LCI_REPLAY)
    root = resp.parse("ul",
                      attrs={"class": "topic-chronology-milestone-component"})

    for program in root.iterfind(".//li"):
        item = Listitem()
        program_url = URL_LCI_ROOT + program.find('.//a').get('href')
        program_name = program.find(".//h2[@class='text-block']").text
        img = program.findall('.//source')[0]
        try:
            img = img.get('data-srcset')
        except Exception:
            img = img.get('srcset')
        img = img.split(',')[0].split(' ')[0]
        item.label = program_name
        item.art["thumb"] = img
        item.set_callback(list_videos,
                          item_id=item_id,
                          program_url=program_url,
                          page='1')
        item_post_treatment(item)
        yield item


@Route.register
def list_videos(plugin, item_id, program_url, page, **kwargs):

    if page == '1':
        resp = urlquick.get(program_url)
    else:
        resp = urlquick.get(program_url + '/%s/' % page)
    root = resp.parse()

    for replay in root.iterfind(
            ".//article[@class='grid-blk__item']"):

        title = replay.find('.//img').get('alt')
        img = ''
        for img in replay.findall('.//source'):
            try:
                img = img.get('data-srcset')
            except Exception:
                img = img.get('srcset')

        img = img.split(',')[0].split(' ')[0]
        program_id = URL_LCI_ROOT + replay.find('.//a').get('href')

        item = Listitem()
        item.label = title
        item.art["thumb"] = img

        item.set_callback(get_video_url,
                          item_id=item_id,
                          program_id=program_id)
        item_post_treatment(item,
                            is_playable=True,
                            is_downloadable=True)
        yield item

    # More videos...
    yield Listitem.next_page(item_id=item_id,
                             program_url=program_url,
                             page=str(int(page) + 1))


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  program_id,
                  download_mode=False,
                  **kwargs):

    if 'www.wat.tv/embedframe' in program_id:
        url = 'http:' + program_id
    elif "http" not in program_id:
        if program_id[0] == '/':
            program_id = program_id[1:]
        url = URL_ROOT(program_id)
    else:
        url = program_id

    video_html = urlquick.get(url).text

    if 'www.wat.tv/embedframe' in program_id:
        video_id = re.compile('UVID=(.*?)&').findall(video_html)[0]
    elif item_id == 'lci':
        video_id = re.compile(r'data-videoid="(.*?)"').findall(video_html)[0]
    else:
        root = video_html.parse()
        iframe_player = root.find(".//div[@class='iframe_player']")
        if iframe_player is not None:
            video_id = iframe_player.get('data-watid')
        else:
            video_id = re.compile(
                r'www\.tf1\.fr\/embedplayer\/(.*?)\"').findall(video_html)[0]

    url_json = URL_VIDEO_STREAM % video_id
    htlm_json = urlquick.get(url_json,
                             headers={'User-Agent': web_utils.get_random_ua()},
                             max_age=-1)
    json_parser = json.loads(htlm_json.text)

    # Check DRM in the m3u8 file
    manifest = urlquick.get(json_parser["hls"],
                            headers={
                                'User-Agent': web_utils.get_random_ua()},
                            max_age=-1).text
    if 'drm' in manifest:
        Script.notify("TEST", plugin.localize(LABELS['drm_notification']),
                      Script.NOTIFY_INFO)
        return False

    root = os.path.dirname(json_parser["hls"])

    manifest = urlquick.get(json_parser["hls"].split('&max_bitrate=')[0],
                            headers={'User-Agent': web_utils.get_random_ua()},
                            max_age=-1)

    final_video_url = ''
    lines = manifest.text.splitlines()
    all_datas_videos_quality = []
    all_datas_videos_path = []
    for k in range(0, len(lines) - 1):
        if 'RESOLUTION=' in lines[k]:
            all_datas_videos_quality.append(
                re.compile(r'RESOLUTION=(.*?),').findall(lines[k])[0])
            all_datas_videos_path.append(root + '/' + lines[k + 1])
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
        return download.download_video(final_video_url)
    return final_video_url


def live_entry(plugin, item_id, **kwargs):
    return get_live_url(plugin, item_id, item_id.upper())


@Resolver.register
def get_live_url(plugin, item_id, video_id, **kwargs):

    video_id = 'L_%s' % item_id.upper()

    video_format = 'hls'
    url_json = URL_VIDEO_STREAM_2 % (video_id, video_format)
    htlm_json = urlquick.get(url_json,
                             headers={'User-Agent': web_utils.get_random_ua()},
                             max_age=-1)
    json_parser = json.loads(htlm_json.text)

    if json_parser['code'] > 400:
        plugin.notify('ERROR', plugin.localize(30713))
        return False
    else:
        return json_parser['url'].replace('master_2000000.m3u8',
                                          'master_4000000.m3u8')
