# -*- coding: utf-8 -*-
# Copyright: (c) 2022, itasli
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import re

from codequick import Resolver
import urlquick

from resources.lib import resolver_proxy


URL_ROOT = 'https://tele1.com.tr'

URL_LIVE = URL_ROOT + '/canli-yayin'


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_LIVE)
    live_id_channel = re.compile('www.youtube.com/embed/(.*?)\"').findall(resp.text)[0]
    live_youtube_html = urlquick.get('https://www.youtube.com/embed/' + live_id_channel)
    live_id = re.compile(r'VIDEO_ID\"\:\"(.*?)\"').findall(
        live_youtube_html.text)[0]
    return resolver_proxy.get_stream_youtube(plugin, live_id, False)
