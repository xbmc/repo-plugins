# -*- coding: utf-8 -*-
# Copyright: (c) 2022, itasli
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import re

from codequick import Resolver
import urlquick

from resources.lib import resolver_proxy


URL_ROOT = 'https://www.kanal7.com'

URL_LIVE = URL_ROOT + '/canli-izle'


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_LIVE)
    video_url = re.compile('\'video-source\',\'(.*?)\'').findall(resp.text)[0]

    if item_id == "kanal7avrupa":
        video_url = re.compile('\'video-source\',\'(.*?)\'').findall(resp.text)[1]

    return resolver_proxy.get_stream_with_quality(plugin, video_url, manifest_type="hls")
