# -*- coding: utf-8 -*-
# Copyright: (c) 2017, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import re
import urlquick

from codequick import Resolver

URL_LIVES = 'http://www.m24tv.ma/'


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_LIVES)
    return re.compile(r'Direct\ TV[\S\s]*\"file\"\:\ \"(.*\.m3u8.*)\"\,').findall(resp.text)[0]
