# -*- coding: utf-8 -*-
# Copyright: (c) 2017, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import json

# noinspection PyUnresolvedReferences
from codequick import Resolver, Script
import urlquick

from resources.lib import resolver_proxy, web_utils

# TODO
# Replay add emissions


URL_LIVE_API = 'https://www.euronews.com/api/live/data'
URL_LIVE_API_V2 = 'https://api.euronews.com/v2/apps/androidPhoneEuronews-6.3/languages/%s/livestream/%s'

GENERIC_HEADERS = {'User-Agent': web_utils.get_random_ua()}


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    final_language = kwargs.get('language', Script.setting['euronews.language'])
    lang = final_language.lower()

    try:
        url_live_json = URL_LIVE_API_V2 % (lang, lang)
        json_parser = urlquick.get(url_live_json, headers=GENERIC_HEADERS, max_age=-1).json()
        video_url = json_parser['primary']

        return resolver_proxy.get_stream_with_quality(plugin, video_url)

    except Exception:
        params = {'locale': lang}
        json_parser = urlquick.get(URL_LIVE_API, headers=GENERIC_HEADERS, params=params, max_age=-1).json()

        return resolver_proxy.get_stream_youtube(plugin, json_parser['videoId'], False)
