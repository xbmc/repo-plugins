# -*- coding: utf-8 -*-
# Copyright: (c) 2025, Joaopa, nictjir  GNU General Public License v2.0+
# (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)
# This file is part of Catch-up TV & More

from __future__ import unicode_literals

from codequick import Resolver
from resources.lib import resolver_proxy


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    return resolver_proxy.get_stream_youtube(plugin, '34tfyR8mO9k')
