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

URL_ROOT = 'https://www.notele.be/'
url_constructor = urljoin_partial(URL_ROOT)

URL_LIVE = url_constructor('it105-md5-direct.html')


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    video_source = urlquick.get(URL_LIVE).parse("video", attrs={"id": "live"}).find("./source").get("src")
    return resolver_proxy.get_stream_with_quality(plugin, video_url=video_source, manifest_type="hls")
