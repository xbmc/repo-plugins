# -*- coding: utf-8 -*-
# Copyright: (c) 2018, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import json
import re

from codequick import Resolver, Script
import urlquick


# Live
URL_LIVE_QVC_IT = 'https://www.qvc.%s/tv/live.html'
# language

URL_LIVE_QVC_JP = 'https://qvc.jp/content/shop-live-tv.html'

URL_LIVE_QVC_DE_UK_US = 'http://www.qvc%s/content/shop-live-tv.qvc.html'
# language

URL_STREAM_LIMELIGHT = 'http://production-ps.lvp.llnw.net/r/PlaylistService/media/%s/getMobilePlaylistByMediaId'
# MediaId

DESIRED_LANGUAGE = Script.setting['qvc.language']


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

    if final_language == 'JP':
        resp = urlquick.get(URL_LIVE_QVC_JP)
        resp.encoding = "shift_jis"
        return 'https:' + re.compile(r'url\"\:\"(.*?)\"').findall(resp.text)[0]

    if final_language == 'DE':
        resp = urlquick.get(URL_LIVE_QVC_DE_UK_US % '.de')
        live_datas_json = re.compile(r'oLiveStreams=(.*?)}},').findall(resp.text)[0] + '}}'
        json_parser = json.loads(live_datas_json)
        return 'http:' + json_parser["QVC"]["url"]

    if final_language == 'UK':
        resp = urlquick.get(URL_LIVE_QVC_DE_UK_US % 'uk.com')
        live_datas_json = re.compile(r'oLiveStreams=(.*?)}},').findall(resp.text)[0] + '}}'
        json_parser = json.loads(live_datas_json)
        return 'http:' + json_parser["QVC"]["url"]

    # Use US by default
    resp = urlquick.get(URL_LIVE_QVC_DE_UK_US % '.com')
    live_datas_json = re.compile(r'oLiveStreams=(.*?)}},').findall(resp.text)[0] + '}}'
    json_parser = json.loads(live_datas_json)
    return 'http:' + json_parser["QVC"]["url"]
