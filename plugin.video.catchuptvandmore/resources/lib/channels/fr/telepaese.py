# -*- coding: utf-8 -*-
# Copyright: (c) 2025, Joaopa
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals

from codequick import Listitem, Resolver, Route
import urlquick

from resources.lib import resolver_proxy, web_utils


# TODO
# Add Replay

URL_ROOT = "https://tv.telepaese.media"

DIRECT_URL_LIVE = 'https://srv.webtvmanager.fr:3970/live/viatelepaeselive.m3u8'

GENERIC_HEADERS = {"User-Agent": web_utils.get_random_ua()}


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    try:
        resp = urlquick.get(URL_ROOT, headers=GENERIC_HEADERS, max_age=-1)
        root = resp.parse()
        live_url = URL_ROOT + root.find(".//a[@class='button live']").get('href')
        resp = urlquick.get(live_url, headers=GENERIC_HEADERS, max_age=-1)
        root = resp.parse()
        live_url = resp.parse().find('.//iframe').get('src')
        resp = urlquick.get(live_url, headers=GENERIC_HEADERS, max_age=-1)
        root = resp.parse()
        video_url = root.find(".//source").get('src')
    except Exception:
        video_url = DIRECT_URL_LIVE

    return resolver_proxy.get_stream_with_quality(plugin, video_url=video_url)
