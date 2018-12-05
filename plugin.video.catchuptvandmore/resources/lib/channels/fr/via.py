# -*- coding: utf-8 -*-
"""
    Catch-up TV & More
    Copyright (C) 2018  SylvainCecchetto

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
from resources.lib import resolver_proxy

from bs4 import BeautifulSoup as bs

import json
import re
import urlquick

'''
TODO Add Replay
'''

URL_ROOT = 'https://%s.tv'

URL_LIVE = URL_ROOT + '/direct-tv/'

URL_LIVE_VIA93 =  URL_ROOT + '/le-direct/'

URL_STREAM = 'https://player.myvideoplace.tv/ajax_actions.php'

URL_STREAM_INFOMANIAK = 'https://livevideo.infomaniak.com/player_config/%s.json'
# player_id

def live_entry(plugin, item_id, item_dict):
    return get_live_url(plugin, item_id, item_id.upper(), item_dict)


@Resolver.register
def get_live_url(plugin, item_id, video_id, item_dict):

    if item_id == 'via93':
        live_html = urlquick.get(
            URL_LIVE_VIA93 % item_id,
            headers={'User-Agent': web_utils.get_random_ua},
            max_age=-1)
    else:
        live_html = urlquick.get(
            URL_LIVE % item_id,
            headers={'User-Agent': web_utils.get_random_ua},
            max_age=-1)
    live_soup = bs(live_html.text, 'html.parser')
    list_lives_datas = live_soup.find_all(
        'iframe')
    live_id = ''
    for live_datas in list_lives_datas:
        src_datas = live_datas.get('src')
        break

    if 'dailymotion' in src_datas:
        live_id = re.compile(
            r'dailymotion.com/embed/video/(.*?)[\?\"]').findall(src_datas)[0]
        return resolver_proxy.get_stream_dailymotion(plugin, live_id, False)
    elif 'infomaniak' in src_datas:
        player_id = src_datas.split('player=')[1]
        resp2 = urlquick.get(
            URL_STREAM_INFOMANIAK % player_id, headers={'User-Agent': web_utils.get_random_ua}, max_age=-1)
        json_parser = json.loads(resp2.text)
        return 'https://' + json_parser["sPlaylist"]
    else:
        live_id = re.compile(
            r'v=(.*?)\&').findall(src_datas)[0]
        stream_json = urlquick.post(
            URL_STREAM,
            data={'action': 'video_info', 'refvideo': live_id},
            headers={'User-Agent': web_utils.get_random_ua}, max_age=-1)
        stream_jsonparser = json.loads(stream_json.text)
        return stream_jsonparser["data"]["bitrates"]["hls"]
