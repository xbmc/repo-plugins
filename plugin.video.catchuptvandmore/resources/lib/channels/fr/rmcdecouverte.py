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

from codequick import Route, Resolver, Listitem, utils, Script

from resources.lib.labels import LABELS
from resources.lib import web_utils
from resources.lib import resolver_proxy

from bs4 import BeautifulSoup as bs

import urlquick

# TODO
# Get informations of replay ?

# RMC Decouverte
URL_REPLAY_RMCDECOUVERTE = 'http://rmcdecouverte.bfmtv.com/mediaplayer-replay/'

URL_VIDEO_HTML_RMCDECOUVERTE = 'http://rmcdecouverte.bfmtv.com/'\
                               'mediaplayer-replay/?id=%s'
# VideoId_html

URL_LIVE_RMCDECOUVERTE = 'http://rmcdecouverte.bfmtv.com/mediaplayer-direct/'


def replay_entry(plugin, item_id):
    """
    First executed function after replay_bridge
    """
    return list_categories(plugin, item_id)


@Route.register
def list_categories(plugin, item_id):
    """
    Build categories listing
    - Tous les programmes
    - Séries
    - Informations
    - ...
    """
    item = Listitem()
    item.label = plugin.localize(LABELS['All videos'])
    item.set_callback(
        list_videos,
        item_id=item_id)
    yield item


@Route.register
def list_videos(plugin, item_id):

    resp = urlquick.get(URL_REPLAY_RMCDECOUVERTE)
    videos_soup = bs(resp.text, 'html.parser')
    list_videos_datas = videos_soup.find_all(
        'article',
        class_='art-c modulx2-5 bg-color-rub0-1 box-shadow relative')
    for video_datas in list_videos_datas:

        video_id = video_datas.find(
            'figure').find(
                'a')['href'].split('&', 1)[0].rsplit('=', 1)[1]
        video_image = video_datas.find(
            'figure').find(
                'a').find('img')['data-original']
        video_titles = video_datas.find(
            'div', class_="art-body"
            ).find('a').find('h2').get_text().replace(
                '\n', ' ').replace('\r', ' ').split(' ')
        video_title = ''
        for i in video_titles:
            video_title = video_title + ' ' + i.strip()

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = video_image

        item.context.script(
            get_video_url,
            plugin.localize(LABELS['Download']),
            item_id=item_id,
            video_id=video_id,
            video_label=LABELS[item_id] + ' - ' + item.label,
            download_mode=True)

        item.set_callback(
            get_video_url,
            item_id=item_id,
            video_id=video_id)
        yield item


@Resolver.register
def get_video_url(
        plugin, item_id, video_id, download_mode=False, video_label=None):

    resp = urlquick.get(
        URL_VIDEO_HTML_RMCDECOUVERTE % video_id,
        headers={'User-Agent': web_utils.get_random_ua},
        max_age=-1)
    video_datas_soup = bs(resp.text, 'html.parser')
    video_datas = video_datas_soup.find('div', class_='next-player')

    data_account = video_datas['data-account']
    data_video_id = video_datas['data-video-id']
    data_player = video_datas['data-player']

    return resolver_proxy.get_brightcove_video_json(
        plugin,
        data_account,
        data_player,
        data_video_id,
        download_mode,
        video_label)


def live_entry(plugin, item_id, item_dict):
    return get_live_url(plugin, item_id, item_id.upper(), item_dict)


@Resolver.register
def get_live_url(plugin, item_id, video_id, item_dict):

    resp = urlquick.get(
        URL_LIVE_RMCDECOUVERTE,
        headers={'User-Agent': web_utils.get_random_ua},
        max_age=-1)

    live_soup = bs(resp.text, 'html.parser')
    data_live_soup = live_soup.find(
        'div', class_='next-player')
    data_account = data_live_soup['data-account']
    data_video_id = data_live_soup['data-video-id']
    data_player = data_live_soup['data-player']
    return resolver_proxy.get_brightcove_video_json(
        plugin,
        data_account,
        data_player,
        data_video_id)
