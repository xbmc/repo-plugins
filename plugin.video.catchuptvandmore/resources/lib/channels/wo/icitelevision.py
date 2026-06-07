# -*- coding: utf-8 -*-
# Copyright: (c) 2017, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import re

# noinspection PyUnresolvedReferences
from codequick import Resolver
import urlquick

from resources.lib import web_utils

URL_ROOT = 'https://icitelevision.ca'

URL_LIVE = URL_ROOT + '/live-video/'


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    headers = {
        "User-Agent": web_utils.get_random_ua(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "fr-BE,en-US;q=0.7,en;q=0.3"
    }
    resp = urlquick.get(URL_LIVE, headers=headers, max_age=-1)
    found_source = re.compile('source src=\"(.*?)\"').findall(resp.text)
    if len(found_source) == 0:
        return False
    return found_source[0]
