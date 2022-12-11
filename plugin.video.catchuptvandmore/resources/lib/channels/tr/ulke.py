# -*- coding: utf-8 -*-
# Copyright: (c) 2022, itasli
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import re

from codequick import Resolver
import urlquick

from resources.lib import resolver_proxy


URL_ROOT = 'https://www.ulketv.com.tr'

URL_LIVE = URL_ROOT + '/canli-yayin'


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_LIVE)
    live_id = re.compile('src=\"https://www.dailymotion.com/embed/video/(.*?)\?.*?\"').findall(resp.text)[0].split('?')[0]
    return resolver_proxy.get_stream_dailymotion(plugin, live_id, False)
