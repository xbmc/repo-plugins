# -*- coding: utf-8 -*-
# Copyright: (c) 2018, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals

from codequick import Resolver, Script


# Live
# https://www.cgtn.com/public/bundle/js/live.js
URL_LIVE_CGTN = 'https://news.cgtn.com/resource/live/%s/cgtn-%s.m3u8'
# Channel (FR|ES|AR|EN|RU|DO(documentary))


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    final_language = kwargs.get('language', Script.setting['cgtn.language'])

    if item_id == 'cgtndocumentary':
        stream_url = URL_LIVE_CGTN % ('document', 'doc')
    else:
        if final_language == 'FR':
            stream_url = URL_LIVE_CGTN % ('french', 'f')
        elif final_language == 'EN':
            stream_url = URL_LIVE_CGTN % ('english', 'news')
        elif final_language == 'AR':
            stream_url = URL_LIVE_CGTN % ('arabic', 'r')
        elif final_language == 'ES':
            stream_url = URL_LIVE_CGTN % ('espanol', 'e')
        elif final_language == 'RU':
            stream_url = URL_LIVE_CGTN % ('russian', 'r')
    return stream_url
