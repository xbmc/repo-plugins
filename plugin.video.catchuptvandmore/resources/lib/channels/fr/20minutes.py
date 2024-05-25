# -*- coding: utf-8 -*-
# Copyright: (c) 2023, Joaopa
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import re
import json

# noinspection PyUnresolvedReferences
from codequick import Listitem, Resolver, Route
# noinspection PyUnresolvedReferences
import urlquick

from resources.lib import download, resolver_proxy, web_utils
from resources.lib.menu_utils import item_post_treatment

URL_ROOT = 'https://www.20minutes.tv'
URL_LIVE = URL_ROOT + '/direct'

GENERIC_HEADERS = {"User-Agent": web_utils.get_random_ua()}


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    resp = urlquick.get(URL_LIVE, headers=GENERIC_HEADERS, max_age=-1)
    root = resp.parse("div", attrs={"class": "background-black bg-custom-primary"})
    url_player = 'https:' + root.find('.//iframe').get('src')

    resp = urlquick.get(url_player, headers=GENERIC_HEADERS, max_age=-1)
    json_text = re.compile(r'DtkPlayer\.init\((.*?)\, \{\"topic').findall(resp.text)[0]
    json_parser = json.loads(json_text)
    video_url = json_parser['video']['media_sources']['live']['src']

    return resolver_proxy.get_stream_with_quality(plugin, video_url=video_url)
