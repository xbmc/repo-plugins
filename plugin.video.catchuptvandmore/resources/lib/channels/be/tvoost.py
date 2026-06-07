# -*- coding: utf-8 -*-
# Copyright: (c) 2017, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals

from codequick import Resolver


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    return 'https://live.zendzend.com/cmaf/29375_399410/master.m3u8?HLS_version=ts'
