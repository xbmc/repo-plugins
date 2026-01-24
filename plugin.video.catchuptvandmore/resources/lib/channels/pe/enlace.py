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

URL_ROOT = 'https://www.enlace.org'
URL_LIVE = URL_ROOT + '/envivo'

GENERIC_HEADERS = {'User-Agent': web_utils.get_random_ua()}

# TODO
# Add Replay


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_LIVE, headers=GENERIC_HEADERS, max_age=-1)
    root = resp.parse("iframe", attrs={"class": "livevideo"})
    live_url = root.get('src')
    resp = urlquick.get(live_url, headers=GENERIC_HEADERS, max_age=-1)
    video_url = re.compile(r'link \= \[\{\"title\"\:\"Enlace en vivo\"\,\"file\"\:\"(.*?)\"').findall(resp.text)[0]

    return resolver_proxy.get_stream_with_quality(plugin, video_url)
