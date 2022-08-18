# -*- coding: utf-8 -*-
# Copyright: (c) 2018, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import json
import re

from codequick import Resolver
import urlquick

from resources.lib import web_utils


# TODO Add Replay

URL_ROOT = 'https://www.canal10.fr'

URL_STREAM = 'https://livevideo.infomaniak.com/player_config/%s.json'
# player_id


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_ROOT,
                        headers={'User-Agent': web_utils.get_random_ua()},
                        max_age=-1)
    player_id = re.compile(r'\&player\=(.*?)\"').findall(resp.text)[0]
    resp2 = urlquick.get(URL_STREAM % player_id,
                         headers={'User-Agent': web_utils.get_random_ua()},
                         max_age=-1)
    json_parser = json.loads(resp2.text)
    return 'https://' + json_parser["sPlaylist"]
