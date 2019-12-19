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

from resources.lib.labels import LABELS
from resources.lib import web_utils
from resources.lib.listitem_utils import item_post_treatment, item2dict

import re
import urlquick

# TO DO
# Add Replay

# Live
URL_LIVE = 'http://tvpstream.vod.tvp.pl/'

URL_STREAM = 'http://www.tvp.pl/sess/tvplayer.php?object_id=%s'
# videoId

LIVE_TVP3_REGIONS = {
    "Białystok": "tvp3-bialystok",
    "Bydgoszcz": "tvp3-bydgoszcz",
    "Gdańsk": "tvp3-gdansk",
    "Gorzów Wielkopolski": "tvp3-gorzow-wielkopolski",
    "Katowice": "tvp3-katowice",
    "Kielce": "tvp3-kielce",
    "Kraków": "tvp3-krakow",
    "Lublin": "tvp3-lublin",
    "Łódź": "tvp3-lodz",
    "Olsztyn": "tvp3-olsztyn",
    "Opole": "tvp3-opole",
    "Poznań": "tvp3-poznan",
    "Rzeszów": "tvp3-rzeszow",
    "Szczecin": "tvp3-szczecin",
    "Warszawa": "tvp3-warszawa",
    "Wrocław": "tvp3-wroclaw"
}


def live_entry(plugin, item_id, item_dict, **kwargs):
    return get_live_url(plugin, item_id, item_id.upper(), item_dict)


@Resolver.register
def get_live_url(plugin, item_id, video_id, item_dict, **kwargs):
    final_language = Script.setting['tvp3.language']

    # If we come from the M3U file and the language
    # is set in the M3U URL, then we overwrite
    # Catch Up TV & More language setting
    if type(item_dict) is not dict:
        item_dict = eval(item_dict)
    if 'language' in item_dict:
        final_language = item_dict['language']

    resp = urlquick.get(URL_LIVE,
                        headers={'User-Agent': web_utils.get_random_ua()},
                        max_age=-1)
    root = resp.parse()

    live_id = ''
    for live_datas in root.findall(".//div"):
        if live_datas.get('data-stationname') is not None:
            if item_id == 'tvpinfo':
                if 'info' in live_datas.find('.//img').get('alt'):
                    live_id = live_datas.get('data-video-id')
            elif item_id == 'tvppolonia':
                if 'Polonia' in live_datas.get('data-title'):
                    live_id = live_datas.get('data-video-id')
            elif item_id == 'tvppolandin':
                if 'News and entertainment' in live_datas.get('data-title'):
                    live_id = live_datas.get('data-video-id')
            elif item_id == 'tvp3':
                if LIVE_TVP3_REGIONS[utils.ensure_unicode(
                        final_language)] in live_datas.find('.//img').get(
                            'alt'):
                    live_id = live_datas.get('data-video-id')
    if live_id == '':
        # Add Notification
        return False
    lives_html = urlquick.get(URL_STREAM % live_id,
                              headers={'User-Agent': web_utils.get_random_ua()},
                              max_age=-1)
    return re.compile(r'src:\'(.*?)\'').findall(lives_html.text)[0]
