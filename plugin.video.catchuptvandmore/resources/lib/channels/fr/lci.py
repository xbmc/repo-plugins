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


from resources.lib import web_utils
from resources.lib import download
from resources.lib.kodi_utils import get_kodi_version, get_selected_item_art, get_selected_item_label, get_selected_item_info, INPUTSTREAM_PROP
from resources.lib.menu_utils import item_post_treatment

# Verify md5 still present in hashlib python 3 (need to find another way if it is not the case)
# https://docs.python.org/3/library/hashlib.html
from hashlib import md5

import inputstreamhelper
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

URL_LICENCE_KEY = 'https://drm-wide.tf1.fr/proxy?id=%s|Content-Type=&User-Agent=Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3041.0 Safari/537.36&Host=drm-wide.tf1.fr|R{SSM}|'
# videoId

URL_VIDEO_STREAM = 'https://www.wat.tv/get/webhtml/%s'

DESIRED_QUALITY = Script.setting['quality']


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
        item.art['thumb'] = item.art['landscape'] = img
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
        resp = urlquick.get(program_url + '%s/' % page)
    root = resp.parse()

    for replay in root.iterfind(
            ".//article[@class='grid-blk__item']"):

        title = replay.find('.//h2').text
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
        item.art['thumb'] = item.art['landscape'] = img

        item.set_callback(get_video_url,
                          item_id=item_id,
                          program_id=program_id)
        item_post_treatment(item,
                            is_playable=True,
                            is_downloadable=False)
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

    if download_mode:
        xbmcgui.Dialog().ok('Info', plugin.localize(30603))
        return False

    is_helper = inputstreamhelper.Helper('mpd', drm='widevine')
    if not is_helper.check_inputstream():
        return False

    item = Listitem()
    item.path = json_parser["mpd"]
    item.label = get_selected_item_label()
    item.art.update(get_selected_item_art())
    item.info.update(get_selected_item_info())
    item.property[INPUTSTREAM_PROP] = 'inputstream.adaptive'
    item.property['inputstream.adaptive.manifest_type'] = 'mpd'
    item.property[
        'inputstream.adaptive.license_type'] = 'com.widevine.alpha'
    item.property[
        'inputstream.adaptive.license_key'] = URL_LICENCE_KEY % video_id

    return item


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

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
