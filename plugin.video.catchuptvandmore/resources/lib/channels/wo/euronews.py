# -*- coding: utf-8 -*-
# Copyright: (c) 2017, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import json

from codequick import Resolver, Script
import urlquick

from resources.lib import resolver_proxy
from resources.lib import web_utils


# TODO
# Replay add emissions

URL_LIVE_API = 'http://%s.euronews.com/api/geoblocking_live.json'
# Language

DESIRED_LANGUAGE = Script.setting['euronews.language']


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    final_language = kwargs.get('language', Script.setting['euronews.language'])

    if final_language == 'EN':
        url_live_json = URL_LIVE_API % 'www'
    elif final_language == 'AR':
        url_live_json = URL_LIVE_API % 'arabic'
    elif final_language == 'RO':
        return resolver_proxy.get_stream_youtube(plugin, 'tdwXKd9Gqb8', False)
    else:
        url_live_json = URL_LIVE_API % final_language.lower()

    resp = urlquick.get(url_live_json,
                        headers={'User-Agent': web_utils.get_random_ua()},
                        max_age=-1)
    json_parser = json.loads(resp.text)
    return resolver_proxy.get_stream_youtube(plugin, json_parser['videoId'], False)
