# -*- coding: utf-8 -*-
# Copyright: (c) 2018, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import re

from codequick import Resolver
import urlquick

from resources.lib import resolver_proxy, web_utils

# TODO
# Add Videos, Replays ?

# URL_ROOT = 'http://www.news24.jp'
# URL_LIVE = URL_ROOT + '/livestream/'
URL_LIVE = 'https://news.ntv.co.jp/live'


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    return 'https://n24-cdn-live.ntv.co.jp/ch01/index.m3u8'
