# -*- coding: utf-8 -*-
# Copyright: (c) 2022, itasli
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import re

from codequick import Resolver
import urlquick

from resources.lib import resolver_proxy


URL_LIVE = {
    'dmax': 'https://www.dmax.com.tr/canli-izle',
    'tlc': 'https://www.tlctv.com.tr/canli-izle',
    'eurostar': 'https://www.eurostartv.com.tr/canli-izle',
    'star': 'https://www.startv.com.tr/canli-yayin',
}


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_LIVE[item_id])

    if item_id in ['dmax', 'tlc']:
        video_url = re.compile('daionUrl : \'(.*?)\?.*?\'').findall(resp.text)[0]
        video_url = video_url.replace('dogus', 'dogus-live')

    elif item_id == 'eurostar':
        video_url = re.compile('var liveUrl = \'(.*?)\'').findall(resp.text)[0]

    elif item_id == 'star':
        live_id = re.compile('data-video=\"(.*?)\"').findall(resp.text)[0]
        return resolver_proxy.get_stream_dailymotion(plugin, live_id, False)

    return resolver_proxy.get_stream_with_quality(plugin, video_url, manifest_type="hls")
