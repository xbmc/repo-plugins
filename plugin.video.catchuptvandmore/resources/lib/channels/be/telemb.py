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

from builtins import str
from codequick import Route, Resolver, Listitem, utils, Script


from resources.lib import web_utils
from resources.lib import download
from resources.lib.menu_utils import item_post_treatment

import json
import re
import urlquick

# TO DO
# Token (live) maybe more work todo
# Fix Download Mode

URL_ROOT = 'https://www.telemb.be'

URL_LIVE = URL_ROOT + '/direct'

URL_STREAM_LIVE = 'https://telemb.fcst.tv/player/embed/%s'
# LiveId


@Route.register
def list_programs(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_ROOT)
    root = resp.parse()
    root2 = root.findall(".//li[@class='we-mega-menu-li dropdown-menu']")[3]

    for program_datas in root2.iterfind(".//li[@class='we-mega-menu-li']"):

        program_title = program_datas.find('.//a').text.strip()
        program_url = URL_ROOT + program_datas.find('.//a').get('href')

        item = Listitem()
        item.label = program_title
        item.set_callback(list_videos,
                          item_id=item_id,
                          program_url=program_url,
                          page='0')
        item_post_treatment(item)
        yield item


@Route.register
def list_videos(plugin, item_id, program_url, page, **kwargs):

    resp = urlquick.get(program_url + '?page=%s' % page)
    root = resp.parse()
    root2 = root.findall(".//div[@class='view-content']")[1]

    for video_datas in root2.iterfind(".//div[@class='views-row']"):
        video_title = video_datas.find('.//a').text
        video_image = URL_ROOT + video_datas.find('.//img').get('src')
        video_url = URL_ROOT + video_datas.find('.//a').get('href')

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = item.art['landscape'] = video_image

        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_url=video_url)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item

    yield Listitem.next_page(item_id=item_id,
                             program_url=program_url,
                             page=str(int(page) + 1))


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_url,
                  download_mode=False,
                  **kwargs):

    resp = urlquick.get(video_url, max_age=-1)
    root = resp.parse()
    video_id_url = root.findall('.//iframe')[1].get('src')

    resp2 = urlquick.get(video_id_url, max_age=-1)
    final_video_url = 'https://tvl-vod.l3.freecaster.net' + re.compile(
        r'freecaster\.net(.*?)\"').findall(resp2.text)[0] + '/master.m3u8'
    if download_mode:
        return download.download_video(final_video_url)
    return final_video_url


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_LIVE, max_age=-1)
    root = resp.parse()
    live_datas = root.findall('.//iframe')[0].get('src')

    resp2 = urlquick.get(live_datas, max_age=-1)
    return re.compile(
        r'file\"\:\"(.*?)\"').findall(resp2.text)[2] + '|referer=https://telemb.fcst.tv/'
