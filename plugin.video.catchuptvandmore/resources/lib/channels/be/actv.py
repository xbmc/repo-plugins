# -*- coding: utf-8 -*-
# Copyright: (c) 2019, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import re

from codequick import Resolver
import urlquick

# TO DO
# Add Replay

URL_ROOT = 'https://www.antennecentre.tv'

URL_LIVE = URL_ROOT + '/direct'

URL_STREAM = 'https://actv.fcst.tv/player/embed/%s'


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_LIVE, max_age=-1)
    live_id = re.compile(
        r'actv\.fcst\.tv\/player\/embed\/(.*?)\?').findall(resp.text)[0]
    resp2 = urlquick.get(URL_STREAM % live_id, max_age=-1)
    list_files = re.compile(
        r'file\"\:\"(.*?)\"').findall(resp2.text)
    url_stream = ''
    for stream_datas in list_files:
        if 'm3u8' in stream_datas:
            url_stream = stream_datas
    return url_stream + '|referer=https://actv.fcst.tv/'
