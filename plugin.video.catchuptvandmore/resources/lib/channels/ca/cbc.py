# -*- coding: utf-8 -*-
# Copyright: (c) 2017, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import json
import re

from codequick import Resolver, Script, utils
import urlquick

from resources.lib import web_utils


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


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

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
