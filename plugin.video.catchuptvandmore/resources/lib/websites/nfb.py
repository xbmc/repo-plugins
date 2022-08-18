# -*- coding: utf-8 -*-
# Copyright: (c) 2017, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals

import json
import re

import htmlement
import urlquick
from codequick import Listitem, Resolver, Route
from resources.lib.menu_utils import item_post_treatment

# TO DO

URL_ROOT = "https://www.nfb.ca"

URL_VIDEOS = (
    URL_ROOT
    + "/remote/explore-all-films/?language=en&genre=%s&availability=free&sort_order=publication_date&page=%s"
)
# Genre, Page


GENRE_VIDEOS = {
    "61": "Animation",
    "63": "Children's film",
    "30500": "Documentary",
    "62": "Experimental",
    "60": "Feature-length fiction",
    "59": "Fiction",
    "89": "Interactive Materials",
    "64": "News Magazine (1940-1965)",
}


@Route.register
def website_root(plugin, item_id, **kwargs):
    """Add modes in the listing"""
    for category_id, category_title in list(GENRE_VIDEOS.items()):
        item = Listitem()
        item.label = category_title
        item.set_callback(
            list_videos, item_id=item_id, category_title=category_title, page=1
        )
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
            item.label = episode.find(".//img").get("alt")
            video_url = URL_ROOT + episode.find(".//a").get("href")
            item.art["thumb"] = item.art["landscape"] = episode.find(".//img").get(
                "src"
            )

            item.set_callback(get_video_url, item_id=item_id, video_url=video_url)
            item_post_treatment(item, is_playable=True, is_downloadable=True)
            yield item

    if at_least_one:
        # More videos...
        yield Listitem.next_page(
            item_id=item_id, category_title=category_title, page=page + 1
        )
    else:
        plugin.notify(plugin.localize(30718), "")
        yield False


@Resolver.register
def get_video_url(plugin, item_id, video_url, download_mode=False, **kwargs):
    """Get video URL and start video player"""

    video_html = urlquick.get(video_url).text
    root = htmlement.fromstring(video_html)
    iframe_src = URL_ROOT + root.find('.//iframe[@id="player-iframe"]').get("src")
    player_html = urlquick.get(iframe_src).text
    video_url = re.search("source: '(.*?)'", player_html).group(1)
    return video_url
