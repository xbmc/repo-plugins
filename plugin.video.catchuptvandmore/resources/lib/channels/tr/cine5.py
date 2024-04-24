# -*- coding: utf-8 -*-
# Copyright: (c) 2022, itasli
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import re

from codequick import Resolver
import urlquick

from resources.lib import resolver_proxy, web_utils


URL_ROOT = 'https://www.cine5tv.com'


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_ROOT, headers={"User-Agent": web_utils.get_random_ua()})
    player_url = re.compile('<script src=\"(.*?)\"').findall(resp.text)[0]
    player_url = player_url.replace("#038;", "").replace("//", "https://")

    resp = urlquick.get(player_url)
    video_url = re.compile('var yayincomtr4=\"(.*?)\"').findall(resp.text)[0]
    video_url = video_url.replace("//", "https://")

    return resolver_proxy.get_stream_with_quality(plugin, video_url, manifest_type="hls")
