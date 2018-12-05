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

import re
from codequick import Route, Resolver, Listitem
import urlquick
from bs4 import BeautifulSoup as bs

from resources.lib.labels import LABELS
from resources.lib import resolver_proxy


URL_ROOT = 'http://www.30millionsdamis.fr'


def website_entry(plugin, item_id):
    """
    First executed function after website_bridge
    """
    return root(plugin, item_id)


def root(plugin, item_id):
    categories_html = urlquick.get(
        URL_ROOT + '/actualites/videos').text
    categories_soup = bs(categories_html, 'html.parser')
    categories = categories_soup.find(
        'select', class_='selecttourl').find_all(
        'option')

    for category in categories:
        item = Listitem()
        item.label = category.get_text().strip()
        category_url = category.get('value')

        item.set_callback(
            list_videos,
            item_id=item_id,
            page=0,
            category_url=category_url)
        yield item


@Route.register
def list_videos(plugin, item_id, page, category_url):
    """Build videos listing"""
    if int(page) > 0:
        replay_episodes_html = urlquick.get(
            category_url + 'actu-page/%s/' % page).text
    else:
        replay_episodes_html = urlquick.get(
            category_url).text
    replay_episodes_soup = bs(replay_episodes_html, 'html.parser')

    episodes = replay_episodes_soup.find_all(
        'div', class_='news-latest')

    at_least_one_item = False

    for episode in episodes:
        at_least_one_item = True
        item = Listitem()
        item.label = episode.find(
            'a').get('title')
        video_url = URL_ROOT + episode.find('a').get('href')
        item.art['thumb'] = URL_ROOT + episode.find('img').get('src')
        item.info['plot'] = episode.find(
            'p').get_text().strip()

        item.context.script(
            get_video_url,
            plugin.localize(LABELS['Download']),
            video_url=video_url,
            item_id=item_id,
            video_label=LABELS[item_id] + ' - ' + item.label,
            download_mode=True)

        item.set_callback(
            get_video_url,
            item_id=item_id,
            video_url=video_url)
        yield item

    # More videos...
    if at_least_one_item:
        yield Listitem.next_page(
            item_id=item_id,
            category_url=category_url,
            page=page + 1)
    else:
        plugin.notify(plugin.localize(LABELS['No videos found']), '')
        yield False


@Resolver.register
def get_video_url(
        plugin, video_url, item_id, download_mode=False, video_label=None):
    """Get video URL and start video player"""
    video_html = urlquick.get(video_url).text
    video_id = re.compile(
        r'www.youtube.com/embed/(.*?)[\?\"]').findall(video_html)[0]

    return resolver_proxy.get_stream_youtube(
        plugin,
        video_id,
        download_mode,
        video_label)
