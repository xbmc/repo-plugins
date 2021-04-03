# -*- coding: utf-8 -*-
# Copyright: (c) 2018, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import re

from codequick import Resolver
import urlquick


# TODO
# Replay

URL_ROOT = 'https://www.boxplus.com'

URL_LIVE_ID = URL_ROOT + '/live-tv-guide/?channel=%s'


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    """Get video URL and start video player"""
    resp = urlquick.get(URL_LIVE_ID % item_id)
    return re.compile('src: \'(.*?)\'').findall(resp.text)[0]
