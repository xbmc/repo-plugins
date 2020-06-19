# -*- coding: utf-8 -*-
"""
    Catch-up TV & More
    Copyright (C) 2017  SylvainCecchetto

    This file is part of Catch-up TV & More.

    Catch-up TV & More is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    Catch-up TV & More is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along
    with Catch-up TV & More; if not, write to the Free Software Foundation,
    Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""

# The unicode_literals import only has
# an effect on Python 2.
# It makes string literals as unicode like in Python 3
from __future__ import unicode_literals

from codequick import Route, Resolver, Listitem, utils, Script


@Resolver.register
def live_entry(plugin, item_id, **kwargs):
    m3u8 = {
        'slo1': 'https://31-rtvslo-tv-slo1-int.cdn.eurovisioncdn.net/playlist.m3u8',
        'slo2': 'https://21-rtvslo-tv-slo2-int.cdn.eurovisioncdn.net/playlist.m3u8',
        'slo3': 'https://16-rtvslo-tv-slo3-int.cdn.eurovisioncdn.net/playlist.m3u8',
        'koper': 'https://27-rtvslo-tv-kp-int.cdn.eurovisioncdn.net/playlist.m3u8',
        'maribor': 'https://25-rtvslo-tv-mb-int.cdn.eurovisioncdn.net/playlist.m3u8',
        'mmc': 'https://29-rtvslo-tv-mmc-int.cdn.eurovisioncdn.net/playlist.m3u8'
    }
    return m3u8[item_id]
