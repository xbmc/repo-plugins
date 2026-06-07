# -*- coding: utf-8 -*-
# Copyright: (c) 2018, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import json

from codequick import Resolver
import urlquick

from resources.lib import resolver_proxy

# TODO
# Add Replay

URL_API = 'https://api.radio-canada.ca/validationMedia/v1/Validation.html'

URL_LIVE = URL_API + '?connectionType=broadband&output=json&multibitrate=true&deviceType=ipad&appCode=medianetlive&idMedia=rdi'


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_LIVE)
    json_parser = json.loads(resp.text)
    return resolver_proxy.get_stream_with_quality(plugin, video_url=json_parser["url"], manifest_type="hls")
