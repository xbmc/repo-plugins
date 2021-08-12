# -*- coding: utf-8 -*-
# Copyright: (c) 2017, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import re

from codequick import Resolver
import urlquick


# TO DO
# Replay add emissions

URL_ROOT = 'http://ntv.ca'

URL_LIVE = URL_ROOT + '/web-tv/'


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_LIVE, max_age=-1)
    root = resp.parse()
    live_datas = root.find('.//iframe')
    resp2 = urlquick.get(live_datas.get('src'), max_age=-1)
    stream_url = ''
    for url in re.compile(r'\"url\"\:\"(.*?)\"').findall(resp2.text):
        if 'm3u8' in url and 'msoNum' not in url:
            stream_url = url
    return stream_url
