# -*- coding: utf-8 -*-
# Copyright: (c) 2022, darodi
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals

import urlquick
# noinspection PyUnresolvedReferences
from codequick import Listitem, Resolver, Route
# noinspection PyUnresolvedReferences
from codequick.utils import urljoin_partial

from resources.lib import resolver_proxy

URL_ROOT = 'http://www.canalzoom.be/'
url_constructor = urljoin_partial(URL_ROOT)

URL_LIVE = url_constructor('live')

URL_M3U8 = "https://tvlocales-live.freecaster.com/live/%s/%s.isml/master.m3u8"


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    player = urlquick.get(URL_LIVE).parse("div", attrs={"class": "freecaster-player"})
    token = player.get("data-fc-token")

    url = URL_M3U8 % (token, token)
    return resolver_proxy.get_stream_with_quality(plugin, video_url=url, manifest_type="hls")
