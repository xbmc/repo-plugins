# -*- coding: utf-8 -*-
# Copyright: (c) 2017, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals


from codequick import Resolver
from resources.lib import resolver_proxy


LIVE_DAILYMOTION = {
    'c8': 'x5gv5rr',
    'cstar': 'x5gv5v0',
    'canalplus': 'x5gv6be'
}


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    return resolver_proxy.get_stream_dailymotion(plugin, LIVE_DAILYMOTION[item_id], False)
