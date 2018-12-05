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

from codequick import Route, Resolver, Listitem, utils, Script

from resources.lib.labels import LABELS
from resources.lib import web_utils
from resources.lib import download


from bs4 import BeautifulSoup as bs
# Verify md5 still present in hashlib python 3 (need to find another way if it is not the case)
# https://docs.python.org/3/library/hashlib.html
from hashlib import md5

import json
import os
import re
import urlquick
import xbmcgui


# TO DO
# Add aired, date, duration etc...
# Rework get_video_url (remove code not needed)

URL_ROOT = utils.urljoin_partial("http://www.tf1.fr")

URL_LCI_REPLAY = "http://www.lci.fr/emissions"
URL_LCI_ROOT = "http://www.lci.fr"

URL_TIME = 'http://www.wat.tv/servertime2/'

URL_TOKEN = 'http://api.wat.tv/services/Delivery'

SECRET_KEY = 'W3m0#1mFI'
APP_NAME = 'sdk/Iphone/1.0'
VERSION = '2.1.3'
HOSTING_APPLICATION_NAME = 'com.tf1.applitf1'
HOSTING_APPLICATION_VERSION = '7.0.4'

URL_VIDEO_STREAM = 'https://www.wat.tv/get/webhtml/%s'

DESIRED_QUALITY = Script.setting['quality']


def replay_entry(plugin, item_id):
    """
    First executed function after replay_bridge
    """
    return list_programs(plugin, item_id)


@Route.register
def list_programs(plugin, item_id):
    """
    Build programs listing
    - Les feux de l'amour
    - ...
    """
    resp = urlquick.get(URL_LCI_REPLAY)
    root_soup = bs(resp.text, 'html.parser')
    programs_soup = root_soup.find(
        'ul',
        attrs={'class': 'topic-chronology-milestone-component'})
    for program in programs_soup.find_all('li'):
        item = Listitem()
        program_url = URL_LCI_ROOT + program.find(
            'a')['href']
        program_name = program.find(
            'h2',
            class_='text-block').get_text()
        img = program.find_all('source')[0]
        try:
            img = img['data-srcset']
        except Exception:
            img = img['srcset']
        img = img.split(',')[0].split(' ')[0]
        item.label = program_name
        item.art["thumb"] = img
        item.set_callback(
            list_videos,
            item_id=item_id,
            program_url=program_url,
            page='1'
        )
        yield item


@Route.register
def list_videos(plugin, item_id, program_url, page):

    if page == '1':
        program_html = urlquick.get(program_url)
    else:
        program_html = urlquick.get(program_url + '/%s/' % page)
    program_soup = bs(program_html.text, 'html.parser')

    list_replay = program_soup.find_all(
        'a',
        class_='medium-3col-article-block-article-link')

    for replay in list_replay:
        if replay.find(
                'span', class_='emission-infos-type'):
            if 'Replay' in replay.find(
                    'span', class_='emission-infos-type').get_text():
                title = replay.find_all(
                    'img')[0].get('alt')
                img = ''
                for img in replay.find_all('source'):
                    try:
                        img = img['data-srcset']
                    except Exception:
                        img = img['srcset']

                img = img.split(',')[0].split(' ')[0]
                program_id = URL_LCI_ROOT + replay.get(
                    'href')

                item = Listitem()
                item.label = title
                item.art["thumb"] = img

                item.context.script(
                    get_video_url,
                    plugin.localize(LABELS['Download']),
                    item_id=item_id,
                    program_id=program_id,
                    video_label=LABELS[item_id] + ' - ' + item.label,
                    download_mode=True)

                item.set_callback(
                    get_video_url,
                    item_id=item_id,
                    program_id=program_id
                )
                yield item

    # More videos...
    yield Listitem.next_page(
        item_id=item_id,
        program_url=program_url,
        page=str(int(page) + 1))


@Resolver.register
def get_video_url(
        plugin, item_id, program_id, download_mode=False, video_label=None):

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
        video_id = re.compile(
            r'data-videoid="(.*?)"').findall(video_html)[0]
    else:
        video_html_soup = bs(video_html, 'html.parser')
        iframe_player_soup = video_html_soup.find(
            'div',
            class_='iframe_player')
        if iframe_player_soup is not None:
            video_id = iframe_player_soup['data-watid']
        else:
            video_id = re.compile(
                r'www\.tf1\.fr\/embedplayer\/(.*?)\"').findall(video_html)[0]

    url_json = URL_VIDEO_STREAM % video_id
    htlm_json = urlquick.get(
        url_json,
        headers={'User-Agent': web_utils.get_random_ua},
        max_age=-1)
    json_parser = json.loads(htlm_json.text)

    # Check DRM in the m3u8 file
    manifest = urlquick.get(
        json_parser["hls"],
        headers={'User-Agent': web_utils.get_random_ua},
        max_age=-1).text
    if 'drm' in manifest:
        Script.notify(
            "TEST",
            plugin.localize(LABELS['drm_notification']),
            Script.NOTIFY_INFO)
        return False

    root = os.path.dirname(json_parser["hls"])

    manifest = urlquick.get(
        json_parser["hls"].split(
            '&max_bitrate=')[0],
        headers={'User-Agent': web_utils.get_random_ua},
        max_age=-1)

    final_video_url = ''
    lines = manifest.text.splitlines()
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


def live_entry(plugin, item_id, item_dict):
    return get_live_url(plugin, item_id, item_id.upper(), item_dict)


@Resolver.register
def get_live_url(plugin, item_id, video_id, item_dict):

    video_id = 'L_%s' % item_id.upper()

    timeserver = str(urlquick.get(URL_TIME, max_age=-1).text)

    auth_key = '%s-%s-%s-%s-%s' % (
        video_id,
        SECRET_KEY,
        APP_NAME,
        SECRET_KEY,
        timeserver
    )

    auth_key = md5(auth_key).hexdigest()
    auth_key = auth_key + '/' + timeserver

    post_data = {
        'appName': APP_NAME,
        'method': 'getUrl',
        'mediaId': video_id,
        'authKey': auth_key,
        'version': VERSION,
        'hostingApplicationName': HOSTING_APPLICATION_NAME,
        'hostingApplicationVersion': HOSTING_APPLICATION_VERSION
    }

    url_video = urlquick.post(
        URL_TOKEN,
        data=post_data, max_age=-1)
    url_video = json.loads(url_video.text)
    url_video = url_video['message'].replace('\\', '')
    return url_video.split('&b=')[0]
