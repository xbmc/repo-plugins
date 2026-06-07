# -*- coding: utf-8 -*-
# Copyright: (c) 2022, darodi
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals

# noinspection PyUnresolvedReferences
from codequick import Listitem, Resolver, Route
# noinspection PyUnresolvedReferences
from codequick.utils import urljoin_partial

from resources.lib import resolver_proxy

URL_ROOT = 'https://www.die-neue-zeit.tv'
url_constructor = urljoin_partial(URL_ROOT)

URL_LIVE = url_constructor('/web-tv-radio/')

URL_LIVE_M3U8 = "https://bild-und-ton.stream/die-neue-zeit-tv-live/smil:dnz-de.smil/playlist.m3u8"


@Route.register
def list_programs(plugin, item_id, **kwargs):
    # TODO
    return False


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    # TODO get m3u8 from URL_LIVE
    return resolver_proxy.get_stream_with_quality(plugin, video_url=URL_LIVE_M3U8, manifest_type="hls")
