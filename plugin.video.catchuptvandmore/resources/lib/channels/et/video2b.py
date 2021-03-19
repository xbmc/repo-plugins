# -*- coding: utf-8 -*-
# Copyright: (c) 2017, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import re

from codequick import Resolver
import urlquick

# Source: https://ethiov.com/live-channels


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    html = urlquick.get('http://video2b.vixtream.net/tv/v/%s' % item_id).text.encode('utf-8')
    m3u8_url = re.compile(r'var src=\'(.*?)\';').findall(html)
    if not m3u8_url:
        return False

    m3u8_url = m3u8_url[0]
    root_url = m3u8_url.split('playlist.m3u8')[0]
    m3u8_text = urlquick.get(m3u8_url).text.encode('utf-8')

    working_stream = []

    # First m3u8 file contains other m3u8 links with diferent bandwidth/resoltuion
    # but some of them returns 404 error
    # We need to check and only select streams that works
    # Else, Kodi fail if at least one stream returns 404 error
    # (instead of ignore this stream and take another one...)
    all_stream_are_ok = True
    for line in m3u8_text.splitlines():
        if '#EXT' not in line:
            url = root_url + line
            try:
                r = urlquick.get(root_url + line, max_age=-1)
                if r.status_code != 404:
                    working_stream.append(url)
                else:
                    all_stream_are_ok = False
            except Exception:
                all_stream_are_ok = False

    if all_stream_are_ok:
        return m3u8_url

    if working_stream:
        return working_stream[0]

    return False
