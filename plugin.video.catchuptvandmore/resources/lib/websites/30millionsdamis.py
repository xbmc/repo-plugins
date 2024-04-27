# -*- coding: utf-8 -*-
# Copyright: (c) 2017, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import re

from codequick import Listitem, Resolver, Route
import urlquick

from resources.lib import resolver_proxy
from resources.lib.menu_utils import item_post_treatment

URL_ROOT = 'https://www.30millionsdamis.fr'


@Route.register
def website_root(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_ROOT + '/actualites/videos')
    root = resp.parse("select", attrs={"class": "selecttourl"})

    for category in root.iterfind("option"):
        item = Listitem()
        item.label = category.text.strip()
        category_url = category.get('value')

        item.set_callback(list_videos, page=0, category_url=category_url)
        item_post_treatment(item)
        yield item


@Route.register
def list_videos(plugin, page, category_url, **kwargs):
    """Build videos listing"""
    if int(page) > 0:
        resp = urlquick.get(category_url + 'actu-page/%s/' % page)
    else:
        resp = urlquick.get(category_url)
    root = resp.parse("div", attrs={"class": "tt-news"})

    at_least_one_item = False

    for episode in root.iterfind(".//div[@class='news-latest']"):
        at_least_one_item = True
        item = Listitem()
        item.label = episode.find('.//h2/a').text
        video_url = URL_ROOT + episode.find('.//a').get('href')
        item.art['thumb'] = item.art['landscape'] = URL_ROOT + episode.find('.//img').get('src')

        item.set_callback(get_video_url, video_url=video_url)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item

    # More videos...
    if at_least_one_item:
        yield Listitem.next_page(category_url=category_url, page=page + 1)
    else:
        plugin.notify(plugin.localize(30718), '')
        yield False


@Resolver.register
def get_video_url(plugin, video_url, download_mode=False, **kwargs):
    """Get video URL and start video player"""
    video_html = urlquick.get(video_url).text
    video_id = re.compile(r'videoID\=\"(.*?)\"').findall(video_html)[0]

    return resolver_proxy.get_stream_youtube(plugin, video_id, download_mode)
