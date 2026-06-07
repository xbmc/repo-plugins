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

URL_LIVE = "https://www.citymusic.be/video/"
URL_M3U8 = "https://5592f056abba8.streamlock.net/citytv/citytv/playlist.m3u8"


# TODO add replay https://www.citymusic.be/videos/

@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    # URL_LIVE contains
    #     <iframe .. src="https://ssl.streampartner.nl/player.php?url=009559fb0fc2c236300d"
    # player_url = urlquick.get(URL_LIVE).parse("iframe").get("src")
    # that player_url gives a scrambled javascript that contains the link to the stream
    #      <script type="text/javascript">;eval(function(w,i,s,e){var lIll=0;var ll1I=0;var Il1l=0; ...
    # I'll just hardcode the URL_M3U8 decoded, let's hope it doesn't change
    return resolver_proxy.get_stream_with_quality(plugin, video_url=URL_M3U8, manifest_type="hls")
