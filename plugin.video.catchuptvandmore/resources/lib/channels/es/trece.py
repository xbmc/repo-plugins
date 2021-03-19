# -*- coding: utf-8 -*-
# Copyright: (c) 2016-2020, Team Catch-up TV & More
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import json

from codequick import Resolver
import urlquick


URL_ROOT = 'https://www.cope.es'

URL_LIVE_JSON = URL_ROOT + '/api/es/appbeta/streaming/trece'
# Live Id


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_LIVE_JSON)
    json_parser = json.loads(resp.text)

    return json_parser["medias"][0]["url"]
