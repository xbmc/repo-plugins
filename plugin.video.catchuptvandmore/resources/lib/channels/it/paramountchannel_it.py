# -*- coding: utf-8 -*-
# Copyright: (c) 2018, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import re

from codequick import Resolver
import urlquick

from resources.lib import resolver_proxy


# TO DO
# Add Replay

URL_LIVE = 'https://www.paramountchannel.it/tv/diretta'


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_LIVE, max_age=-1)
    video_uri = re.compile(r'uri\"\:\"(.*?)\"').findall(resp.text)[0]
    account_override = 'intl.mtvi.com'
    ep = 'be84d1a2'

    return resolver_proxy.get_mtvnservices_stream(
        plugin, video_uri, False, account_override, ep)
