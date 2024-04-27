# -*- coding: utf-8 -*-
# Copyright: (c) 2022, joaopa
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import re

# noinspection PyUnresolvedReferences
from codequick import Resolver, Script
import urlquick

from kodi_six import xbmcgui
from resources.lib.addon_utils import Quality

from resources.lib import resolver_proxy, web_utils

# TODO
# Add Replay


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    headers = {
        'User-Agent': web_utils.get_random_ua(),
        'Referer': 'https://componentes.enlace.org'
    }
    rate = {
        0: "https://11554-1.b.cdn13.com/LiveHTTPOrigin/live_160p/playlist.m3u8",
        1: "https://11554-1.b.cdn13.com/LiveHTTPOrigin/live_360p/playlist.m3u8",
        2: "https://11554-1.b.cdn13.com/LiveHTTPOrigin/live/playlist.m3u8"
    }

    quality = Script.setting.get_string('quality')
    if quality == Quality['WORST']:
        video_url = rate[0]
    elif quality == Quality['BEST'] or quality == Quality['DEFAULT']:
        video_url = rate[len(rate) - 1]
    else:
        video_url = rate[xbmcgui.Dialog().select(Script.localize(30180), ["160p", "360p", "480p"])]

    return resolver_proxy.get_stream_with_quality(plugin, video_url, headers=headers, manifest_type="hls", bypass=True)
