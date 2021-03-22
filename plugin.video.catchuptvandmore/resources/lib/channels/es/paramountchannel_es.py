# -*- coding: utf-8 -*-
# Copyright: (c) 2018, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import re

from codequick import Resolver
import urlquick

from resources.lib import resolver_proxy


URL_LIVE = 'http://www.paramountnetwork.es/en-directo/4ypes1'


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_LIVE)
    video_uri = re.compile(r'\"config"\:\{\"uri\"\:\"(.*?)\"').findall(
        resp.text)[0]

    return resolver_proxy.get_mtvnservices_stream(plugin, video_uri)
