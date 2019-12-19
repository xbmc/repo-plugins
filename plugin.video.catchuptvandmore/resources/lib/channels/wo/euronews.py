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

import json
import urlquick

# TO DO
# Replay add emissions

URL_LIVE_API = 'http://%s.euronews.com/api/watchlive.json'
# Language

DESIRED_LANGUAGE = Script.setting['euronews.language']


def live_entry(plugin, item_id, item_dict, **kwargs):
    return get_live_url(plugin, item_id, item_id.upper(), item_dict)


@Resolver.register
def get_live_url(plugin, item_id, video_id, item_dict, **kwargs):

    final_language = DESIRED_LANGUAGE

    # If we come from the M3U file and the language
    # is set in the M3U URL, then we overwrite
    # Catch Up TV & More language setting
    if type(item_dict) is not dict:
        item_dict = eval(item_dict)
    if 'language' in item_dict:
        final_language = item_dict['language']

    if final_language == 'EN':
        url_live_json = URL_LIVE_API % 'www'
    elif final_language == 'AR':
        url_live_json = URL_LIVE_API % 'arabic'
    else:
        url_live_json = URL_LIVE_API % final_language.lower()

    resp = urlquick.get(url_live_json,
                        headers={'User-Agent': web_utils.get_random_ua()},
                        max_age=-1)
    json_parser = json.loads(resp.text)
    if 'http' in json_parser["url"]:
        url2_live_json = json_parser["url"]
    else:
        url2_live_json = 'https:' + json_parser["url"]

    resp2 = urlquick.get(url2_live_json,
                         headers={'User-Agent': web_utils.get_random_ua()},
                         max_age=-1)
    json_parser_2 = json.loads(resp2.text)
    return json_parser_2["primary"]
