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
from resources.lib import resolver_proxy
from resources.lib.listitem_utils import item_post_treatment, item2dict

import htmlement
import json
import re
import urlquick

# TO DO

URL_ROOT = 'https://www.nfb.ca'

URL_VIDEOS = URL_ROOT + '/remote/explore-all-films/?language=en&genre=%s&availability=free&sort_order=publication_date&page=%s'
# Genre, Page


def website_entry(plugin, item_id, **kwargs):
    """
    First executed function after website_bridge
    """
    return root(plugin, item_id)


GENRE_VIDEOS = {
    '61': 'Animation',
    '63': 'Children\'s film',
    '30500': 'Documentary',
    '62': 'Experimental',
    '60': 'Feature-length fiction',
    '59': 'Fiction',
    '89': 'Interactive Materials',
    '64': 'News Magazine (1940-1965)'
}


def root(plugin, item_id, **kwargs):
    """Add modes in the listing"""
    for category_id, category_title in list(GENRE_VIDEOS.items()):
        item = Listitem()
        item.label = category_title
        item.set_callback(list_videos,
                          item_id=item_id,
                          category_title=category_title,
                          page=1)
        item_post_treatment(item)
        yield item


@Route.register
def list_videos(plugin, item_id, category_title, page, **kwargs):
    """Build videos listing"""
    replay_episodes_json = urlquick.get(URL_VIDEOS % (category_title, page)).text
    replay_episodes_jsonparser = json.loads(replay_episodes_json)
    at_least_one = False
    for replay_episodes_datas in replay_episodes_jsonparser["items_html"]:
        parser = htmlement.HTMLement()
        parser.feed(replay_episodes_datas)
        root = parser.close()

        for episode in root.iterfind(".//li"):
            at_least_one = True
            item = Listitem()
            item.label = episode.find('.//img').get('alt')
            video_url = URL_ROOT + episode.find('.//a').get('href')
            item.art['thumb'] = episode.find('.//img').get('src')

            item.set_callback(get_video_url,
                              item_id=item_id,
                              video_label=LABELS[item_id] + ' - ' + item.label,
                              video_url=video_url)
            item_post_treatment(item, is_playable=True, is_downloadable=True)
            yield item

    if at_least_one:
        # More videos...
        yield Listitem.next_page(item_id=item_id,
                                 category_title=category_title,
                                 page=page + 1)
    else:
        plugin.notify(plugin.localize(LABELS['No videos found']), '')
        yield False


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_url,
                  download_mode=False,
                  video_label=None,
                  **kwargs):
    """Get video URL and start video player"""

    video_html = urlquick.get(video_url).text
    # Get Kalkura Id Video
    video_url = re.compile(r'og\:video\:url" content="(.*?)"').findall(
        video_html)[0]

    return resolver_proxy.get_stream_kaltura(plugin, video_url, download_mode,
                                             video_label)
