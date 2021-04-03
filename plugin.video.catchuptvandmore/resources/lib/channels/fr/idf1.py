# -*- coding: utf-8 -*-
# Copyright: (c) 2019, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import json
import re

from codequick import Resolver
import urlquick


# TODO Add Replay


URL_ROOT = 'http://www.idf1.fr'

# LIVE :
URL_LIVE = URL_ROOT + '/live'
# Get Id
JSON_LIVE = 'https://playback.dacast.com/content/access?contentId=%s&provider=dacast'
# Id in 3 part


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_LIVE, max_age=-1)
    list_id_values = re.compile(r'contentId\=(.*?)\"').findall(resp.text)[0]

    # json with token
    resp2 = urlquick.get(
        JSON_LIVE % (list_id_values),
        max_age=-1)
    live_json_parser = json.loads(resp2.text)

    return live_json_parser["hls"]
