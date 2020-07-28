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


from resources.lib import web_utils

import json
import re
import urlquick

# TO DO

# Live
URL_LIVE_QVC_IT = 'https://www.qvc.%s/tv/live.html'
# language

URL_LIVE_QVC_JP = 'https://qvc.jp/content/shop-live-tv.html'

URL_LIVE_QVC_DE_UK_US = 'http://www.qvc%s/content/shop-live-tv.qvc.html'
# language

URL_STREAM_LIMELIGHT = 'http://production-ps.lvp.llnw.net/r/PlaylistService/media/%s/getMobilePlaylistByMediaId'
# MediaId

DESIRED_LANGUAGE = Script.setting['qvc.language']


def live_entry(plugin, item_id, **kwargs):
    return get_live_url(plugin, item_id, **kwargs)


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    final_language = kwargs.get('language', Script.setting['qvc.language'])

    if final_language == 'IT':
        resp = urlquick.get(URL_LIVE_QVC_IT % final_language.lower())
        live_id = re.compile(r'data-media="(.*?)"').findall(resp.text)[0]
        live_datas_json = urlquick.get(URL_STREAM_LIMELIGHT % live_id)
        json_parser = json.loads(live_datas_json.text)

        stream_url = ''
        for live_datas in json_parser["mediaList"][0]["mobileUrls"]:
            if live_datas["targetMediaPlatform"] == "HttpLiveStreaming":
                stream_url = live_datas["mobileUrl"]
        return stream_url
    elif final_language == 'JP':
        resp = urlquick.get(URL_LIVE_QVC_JP)
        resp.encoding = "shift_jis"
        return 'https:' + re.compile(
            r'url\"\:\"(.*?)\"').findall(resp.text)[0]
    elif final_language == 'DE' or\
            final_language == 'UK' or\
            final_language == 'US':
        if final_language == 'DE':
            resp = urlquick.get(URL_LIVE_QVC_DE_UK_US % '.de')
        elif final_language == 'UK':
            resp = urlquick.get(URL_LIVE_QVC_DE_UK_US % 'uk.com')
        elif final_language == 'US':
            resp = urlquick.get(URL_LIVE_QVC_DE_UK_US % '.com')
        live_datas_json = re.compile(r'oLiveStreams=(.*?)}},').findall(
            resp.text)[0] + '}}'
        json_parser = json.loads(live_datas_json)
        return 'http:' + json_parser["QVC"]["url"]
