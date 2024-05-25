# -*- coding: utf-8 -*-
# Copyright: (c) 2017, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import json

# noinspection PyUnresolvedReferences
from codequick import Resolver, Script
import urlquick

from resources.lib import resolver_proxy
from resources.lib import web_utils

# TODO
# Replay add emissions

URL_LIVE_API = 'https://%s.euronews.com/api/live/data?locale=%s'

GENERIC_HEADERS = {'User-Agent': web_utils.get_random_ua()}


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    final_language = kwargs.get('language', Script.setting['euronews.language'])
    lang = final_language.lower()
    if final_language == 'EN':
        url_live_json = URL_LIVE_API % ('www', lang)
    elif final_language == 'AR':
        url_live_json = URL_LIVE_API % ('arabic', lang)
    elif final_language == 'RO':
        return resolver_proxy.get_stream_youtube(plugin, 'PHFADeLxJ2w', False)
    elif final_language == 'BG':
        return resolver_proxy.get_stream_youtube(plugin, 'P7dqy-tvU08', False)
    else:
        url_live_json = URL_LIVE_API % (lang, lang)

    json_parser = urlquick.get(url_live_json, headers=GENERIC_HEADERS, max_age=-1).json()

    return resolver_proxy.get_stream_youtube(plugin, json_parser['videoId'], False)
