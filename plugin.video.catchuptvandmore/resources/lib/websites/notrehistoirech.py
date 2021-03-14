# -*- coding: utf-8 -*-
'''
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
'''
# The unicode_literals import only has
# an effect on Python 2.
# It makes string literals as unicode like in Python 3
from __future__ import unicode_literals

from codequick import Route, Resolver, Listitem


from resources.lib import download
from resources.lib.menu_utils import item_post_treatment

import re
import urlquick

# TO DO
# Download Mode

URL_ROOT = 'http://www.notrehistoire.ch'


@Route.register
def website_root(plugin, item_id, **kwargs):
    """Add modes in the listing"""
    item = Listitem()
    item.label = plugin.localize(30701)
    category_url = URL_ROOT + '/search?scope=media&types[0]=video&page=%s'

    item.set_callback(list_videos,
                      item_id=item_id,
                      category_url=category_url,
                      page=1)
    item_post_treatment(item)
    yield item


@Route.register
def list_videos(plugin, item_id, category_url, page, **kwargs):
    """Build videos listing"""
    resp = urlquick.get(category_url % page)
    root = resp.parse()

    for episode in root.iterfind(".//div[@class='w-full sm:w-1/2 md:w-1/3 px-2 md:px-3 mb-5 md:mb-6 group']"):
        item = Listitem()
        item.label = episode.find(
            ".//a[@class='text-black text-sm leading-xs font-semibold block']").text.strip()
        video_url = episode.find(
            ".//a[@class='text-black text-sm leading-xs font-semibold block']").get('href')
        item.art['thumb'] = item.art['landscape'] = episode.find(
            ".//img[@class='w-full h-auto align-top']").get('data-src')
        item.info['plot'] = episode.find(
            ".//div[@class='text-grey-darker text-sm leading-xs mb-3']").text

        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_url=video_url)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item

    # More videos...
    yield Listitem.next_page(item_id=item_id,
                             category_url=category_url,
                             page=page + 1)


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_url,
                  download_mode=False,
                  **kwargs):
    """Get video URL and start video player"""

    video_html = urlquick.get(video_url).text
    video_url = re.compile(
        r'source src=\"(.*?)\"').findall(video_html)[0]

    if download_mode:
        return download.download_video(video_url)

    return video_url
