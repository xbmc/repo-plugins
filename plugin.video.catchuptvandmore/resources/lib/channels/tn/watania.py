# -*- coding: utf-8 -*-
# Copyright: (c) 2018, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import re

from codequick import Resolver
import urlquick

from resources.lib import resolver_proxy


# TODO
# Add Replay

# Live
URL_ROOT = 'http://www.%s.tn'
# channel_name


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_ROOT % item_id)
    root = resp.parse()

    if root.find(".//section[@id='block-block-2']") is not None:
        live_url = root.find(".//section[@id='block-block-2']").findall(
            './/a')[0].get('href')
    else:
        live_url = root.find(".//section[@id='block-block-4']").findall(
            './/a')[0].get('href')
    live_html = urlquick.get(live_url)
    live_id_channel = re.compile('www.youtube.com/embed/(.*?)\"').findall(
        live_html.text)[1]
    live_youtube_html = urlquick.get('https://www.youtube.com/embed/' +
                                     live_id_channel)
    live_id = re.compile(r'VIDEO_ID\"\:\"(.*?)\"').findall(
        live_youtube_html.text)[0]
    return resolver_proxy.get_stream_youtube(plugin, live_id, False)
