# -*- coding: utf-8 -*-
# Copyright: (c) 2018, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import re

from codequick import Resolver
import urlquick


# TO DO
# Add Replay

URL_ROOT = 'https://www.telem1.ch'

# Live
URL_LIVE = URL_ROOT + '/live'


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_LIVE)
    list_lives = re.compile(r'contentUrl\":\"(.*?)\"').findall(resp.text)
    stream_url = ''
    for stream_datas in list_lives:
        if 'm3u8' in stream_datas:
            stream_url = stream_datas
    return stream_url
