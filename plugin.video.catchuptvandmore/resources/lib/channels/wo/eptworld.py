# -*- coding: utf-8 -*-
# Copyright: (c) 2022, Joaopa
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import json

from codequick import Resolver
import urlquick

from resources.lib import resolver_proxy, web_utils


# TO DO
# Add Replay

URL_API = 'https://api.app.ertflix.gr/v1/Player/AcquireContent'

GENERIC_HEADERS = {"User-Agent": web_utils.get_random_ua()}


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    params = {
        'platformCodename': 'www',
        'codename': "ept-world-live"
    }

    resp = urlquick.get(URL_API, headers=GENERIC_HEADERS, params=params, max_age=-1)
    data_json = json.loads(resp.text)
    possible_formats = data_json['MediaFiles'][0]['Formats']
    default = True

    for video_type in possible_formats:
        if 'm3u8' in video_type['Url']:
            video_url = video_type['Url']
            break
        if 'mpd' in video_type['Url']:
            video_url = video_type['Url']
            default = False
            if default:
                video_url = video_type['Url']

    return resolver_proxy.get_stream_with_quality(plugin, video_url)
