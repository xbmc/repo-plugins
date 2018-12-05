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

from codequick import Route, Resolver, Listitem, utils, Script

from resources.lib.labels import LABELS
from resources.lib import web_utils
from resources.lib import download

from bs4 import BeautifulSoup as bs

import re
import urlquick

# TO DO
# Fix Download Video


# Live
URL_LIVE_JSON = 'http://dbxm993i42r09.cloudfront.net/' \
                'configs/blaze.json?callback=blaze'

# Replay
URL_SHOWS = 'http://www.blaze.tv/series?page=%s'
# pageId

URL_API_KEY = 'https://dbxm993i42r09.cloudfront.net/configs/config.blaze.js'

URL_STREAM = 'https://d2q1b32gh59m9o.cloudfront.net/player/config?' \
             'callback=ssmp&client=blaze&type=vod&apiKey=%s&videoId=%s&' \
             'format=jsonp&callback=ssmp'
# apiKey, videoId

URL_ROOT = 'http://www.blaze.tv'


def replay_entry(plugin, item_id):
    """
    First executed function after replay_bridge
    """
    return list_categories(plugin, item_id)


@Route.register
def list_categories(plugin, item_id):
    """
    Build programs listing
    - Les feux de l'amour
    - ...
    """
    item = Listitem()
    item.label = plugin.localize(LABELS['All programs'])
    item.set_callback(
        list_programs,
        item_id=item_id,
        page='0')
    yield item


@Route.register
def list_programs(plugin, item_id, page):
    """
    Build programs listing
    - Les feux de l'amour
    - ...
    """
    resp = urlquick.get(URL_SHOWS % page)
    root_soup = bs(resp.text, 'html.parser')
    list_programs_datas = root_soup.find_all(
        'div', class_='item')

    for program_datas in list_programs_datas:
        program_title = program_datas.find('a').find('img').get('alt')
        program_image = program_datas.find('a').find('img').get('src')
        program_url = URL_ROOT + program_datas.find('a').get('href')

        item = Listitem()
        item.label = program_title
        item.art['thumb'] = program_image
        item.set_callback(
            list_seasons,
            item_id=item_id,
            program_url=program_url)
        yield item

    yield Listitem.next_page(
        item_id=item_id,
        page=str(int(page) + 1))


@Route.register
def list_seasons(plugin, item_id, program_url):

    resp = urlquick.get(program_url)
    root_soup = bs(resp.text, 'html.parser')
    list_seasons_datas = root_soup.find(
        'div', class_='pagination').find_all('a')

    for season_datas in list_seasons_datas:
        season_title = 'Series %s' % season_datas.text.strip()
        season_url = URL_ROOT + season_datas.get('href')

        item = Listitem()
        item.label = season_title
        item.set_callback(
            list_videos,
            item_id=item_id,
            season_url=season_url)
        yield item


@Route.register
def list_videos(plugin, item_id, season_url):

    resp = urlquick.get(season_url)
    root_soup = bs(resp.text, 'html.parser')
    list_videos_datas = root_soup.find_all(
        'div', class_='carousel-inner')[0].find_all(
            'div', class_='col-md-4 wrapper-item season')

    for video_datas in list_videos_datas:

        value_episode = video_datas.find(
            'span', class_='caption-description'
        ).get_text().split(' | ')[1].split(' ')[1]
        value_season = video_datas.find(
            'span', class_='caption-description'
        ).get_text().split(' | ')[0].split(' ')[1]
        video_title = video_datas.find(
            'span', class_='caption-title'
        ).get_text() + ' S%sE%s' % (value_season, value_episode)
        video_plot = video_datas.find(
            'span', class_='caption-title').get_text() + ' '
        video_plot = video_plot + video_datas.find(
            'span', class_='caption-description').get_text()
        video_image = video_datas.find('a').find('img').get('src')
        video_url = URL_ROOT + video_datas.find('a').get('href')

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = video_image
        item.info['plot'] = video_plot

        item.context.script(
            get_video_url,
            plugin.localize(LABELS['Download']),
            item_id=item_id,
            video_url=video_url,
            video_label=LABELS[item_id] + ' - ' + item.label,
            download_mode=True)

        item.set_callback(
            get_video_url,
            item_id=item_id,
            video_url=video_url)
        yield item


@Resolver.register
def get_video_url(
        plugin, item_id, video_url, download_mode=False, video_label=None):

    resp = urlquick.get(
        video_url,
        headers={'User-Agent': web_utils.get_random_ua},
        max_age=-1)
    videoId = re.compile('data-uvid="(.*?)"').findall(resp.text)[0]
    resp_apikey = urlquick.get(
        URL_API_KEY,
        headers={'User-Agent': web_utils.get_random_ua},
        max_age=-1)
    apikey = re.compile('"apiKey": "(.*?)"').findall(resp_apikey.text)[0]
    resp_stream = urlquick.get(
        URL_STREAM % (apikey, videoId),
        headers={'User-Agent': web_utils.get_random_ua},
        max_age=-1)

    final_video_url = re.compile('"hls":"(.*?)"').findall(resp_stream.text)[0]
    if download_mode:
        return download.download_video(final_video_url, video_label)
    return final_video_url


def live_entry(plugin, item_id, item_dict):
    return get_live_url(plugin, item_id, item_id.upper(), item_dict)


@Resolver.register
def get_live_url(plugin, item_id, video_id, item_dict):

    resp = urlquick.get(URL_LIVE_JSON)
    return re.compile('"url": "(.*?)"').findall(resp.text)[0]
