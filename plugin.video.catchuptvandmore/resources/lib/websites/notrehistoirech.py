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

from resources.lib.labels import LABELS
from resources.lib import download
from resources.lib.listitem_utils import item_post_treatment, item2dict

import re
import urlquick

# TO DO
# Download Mode

URL_ROOT = 'http://www.notrehistoire.ch'


def website_entry(plugin, item_id, **kwargs):
    """
    First executed function after website_bridge
    """
    return root(plugin, item_id)


def root(plugin, item_id, **kwargs):
    """Add modes in the listing"""
    item = Listitem()
    item.label = plugin.localize(LABELS['All videos'])
    category_url = URL_ROOT + '/search?types=video&page=%s&sort=-origin_date'

    item.set_callback(list_videos,
                      item_id=item_id,
                      category_url=category_url,
                      page=1)
    item_post_treatment(item)
    yield item

    resp = urlquick.get(URL_ROOT + '/search?types=video')
    root = resp.parse("div",
                      attrs={"class": "facet-group facet-group--tags open"})

    for category in root.iterfind(".//label"):
        item = Listitem()
        item.label = category.find('input').tail.strip()
        category_id = category.find('input').get('value')
        category_url = URL_ROOT + '/search?types=video' + \
            '&tags=%s&sort=-origin_date' % category_id + \
            '&page=%s'

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

    for episode in root.iterfind(".//div[@class='media-item']"):
        item = Listitem()
        item.label = episode.get('title')
        video_url = URL_ROOT + episode.find('.//a').get('href')
        item.art['thumb'] = episode.find('.//img').get('src')

        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_label=LABELS[item_id] + ' - ' + item.label,
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
                  video_label=None,
                  **kwargs):
    """Get video URL and start video player"""

    video_html = urlquick.get(video_url).text
    video_url = re.compile(
        r'property=\"og\:video\" content=\"(.*?)\"').findall(video_html)[0]

    if download_mode:
        return download.download_video(video_url, video_label)

    return video_url
