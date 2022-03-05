# -*- coding: utf-8 -*-
# Copyright: (c) 2018, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import re

from codequick import Resolver, Script
import json
import urlquick

from resources.lib import web_utils


URL_ROOT = 'https://www.realmadrid.com'

URL_LIVE = URL_ROOT + '/sv-st-rmtv?cp=300'

URL_REFERER = URL_ROOT + '/real-madrid-tv'


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    # Obtain language key as lower letter
    final_language = kwargs.get('language', Script.setting['realmadridtv.language']).lower()

    # Get m3u8 url in a json
    resp = urlquick.get(URL_LIVE,
                        headers={'referer': URL_REFERER},
                        max_age=-1)

    # Parse json, format : {'vurl': {'es':url,'en':url}}
    resp_json = json.loads(resp.text)

    url_live = resp_json['vurl'][final_language]

    return url_live
