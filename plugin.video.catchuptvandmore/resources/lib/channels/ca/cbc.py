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


from resources.lib import web_utils
from resources.lib import resolver_proxy

import json
import re
import urlquick

# TO DO
# Replay add emissions

URL_ROOT = 'https://gem.cbc.ca'

URL_LIVES_INFO = URL_ROOT + '/public/js/main.js'

LIVE_CBC_REGIONS = {
    "Ottawa": "CBOT",
    "Montreal": "CBMT",
    "Charlottetown": "CBCT",
    "Fredericton": "CBAT",
    "Halifax": "CBHT",
    "Windsor": "CBET",
    "Yellowknife": "CFYK",
    "Winnipeg": "CBWT",
    "Regina": "CBKT",
    "Calgary": "CBRT",
    "Edmonton": "CBXT",
    "Vancouver": "CBUT",
    "Toronto": "CBLT",
    "St. John's": "CBNT"
}


def live_entry(plugin, item_id, **kwargs):
    return get_live_url(plugin, item_id, item_id.upper())


@Resolver.register
def get_live_url(plugin, item_id, video_id, **kwargs):

    final_region = kwargs.get('language', Script.setting['cbc.language'])
    region = utils.ensure_unicode(final_region)

    resp = urlquick.get(URL_LIVES_INFO, max_age=-1)
    url_live_stream = 'https:' + re.compile(
        r'LLC_URL\=r\+\"(.*?)\?').findall(resp.text)[0]

    headers = {
        'User-Agent':
        web_utils.get_random_ua()
    }
    resp2 = urlquick.get(url_live_stream, headers=headers, max_age=-1)
    json_parser = json.loads(resp2.text)

    stream_datas_url = ''
    for live_datas in json_parser["entries"]:
        if LIVE_CBC_REGIONS[region] in live_datas['cbc$callSign']:
            stream_datas_url = live_datas["content"][0]["url"]

    resp3 = urlquick.get(stream_datas_url, headers=headers, max_age=-1)
    return re.compile(
        r'video src\=\"(.*?)\"').findall(resp3.text)[0]
