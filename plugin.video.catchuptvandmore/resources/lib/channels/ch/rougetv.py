# -*- coding: utf-8 -*-
# Copyright: (c) 2017, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import re

from codequick import Resolver
import urlquick


# TO DO
# Add replay

URL_ROOT = 'https://www.rougetv.ch/'


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_ROOT)
    list_live_streams = re.compile('data-url\=\"(.*?)\"').findall(resp.text)
    stream_url = ''
    for live_stream_datas in list_live_streams:
        if 'm3u8' in live_stream_datas:
            stream_url = live_stream_datas
    return stream_url
