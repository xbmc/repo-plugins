# -*- coding: utf-8 -*-
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import re

from codequick import Resolver
import urlquick

from resources.lib import web_utils

URL_LIVE = 'https://omroepbrabant.bbvms.com/p/default/c/1080520.json'

# I would prefer to use this live url but I cannot find the 1080520.json file in its body.
# URL_LIVE = 'https://www.omroepbrabant.nl/tv'


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_LIVE,
                        headers={'User-Agent': web_utils.get_random_ua()},
                        max_age=-1)
    url = re.compile(r'([^"]+\.m3u8)').findall(resp.text)[0]
    return url.replace('\\/', '/')
