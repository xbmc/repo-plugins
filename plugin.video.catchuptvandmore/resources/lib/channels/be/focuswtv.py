# -*- coding: utf-8 -*-
# Copyright: (c) 2017, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals

from codequick import Resolver


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    return 'https://hls-origin01-focus-wtv.cdn01.rambla.be/main/adliveorigin-focus-wtv/_definst_/ARXpX7.smil/playlist.m3u8|referer=http://player.clevercast.com/players/video-js/'
