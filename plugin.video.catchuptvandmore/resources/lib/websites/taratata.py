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


from codequick import Route, Resolver, Listitem, utils
import urlquick

import json
import re
from bs4 import BeautifulSoup as bs
import xbmcgui
import resources.lib.cq_utils as cqu

from resources.lib.labels import LABELS
from resources.lib import download
from resources.lib import resolver_proxy


# TO DO
# Download Video
# Find a better solution to strip some text
# remove YT_DL use API FTV
# Fix Bonus

URL_ROOT = utils.urljoin_partial('https://mytaratata.com')

URL_EMBED_FTV = 'http://api-embed.webservices.francetelevisions.fr/key/%s'
# Id Video
# http://embed.francetv.fr/?ue=fb23d5e2c7e5c020b2e710c5fe233aea

SHOW_INFO_FTV = 'https://api-embed.webservices.francetelevisions.fr/v2/key/%s'
# idEmbeded


def website_entry(plugin, item_id):
    """
    First executed function after website_bridge
    """
    return root_taratata(plugin, item_id)


@Route.register
def root_taratata(plugin, item_id):
    """Add modes in the listing"""
    list_categories_html = urlquick.get(URL_ROOT('')).text
    list_categories_soup = bs(list_categories_html, 'html.parser')
    list_categories = list_categories_soup.find(
        'ul', class_='nav navbar-nav').find_all('a')

    for category in list_categories:
        item = Listitem()
        item.label = category.get_text()
        category_url = URL_ROOT(category.get('href'))

        value_next = ''
        if 'taratata' in category.get('href'):
            value_next = 'list_shows_taratata'
        elif 'artistes' in category.get('href'):
            value_next = 'list_shows_artistes_1'
        elif 'bonus' in category.get('href'):
            value_next = 'list_shows_bonus'
        else:
            continue

        item.set_callback(
            eval(value_next),
            item_id=item_id,
            category_url=category_url,
            page=1
        )
        yield item


@Route.register
def list_shows_taratata(plugin, item_id, category_url, page):
    list_shows_html = urlquick.get(
        category_url + '/page/%s' % str(page)).text
    list_shows_soup = bs(list_shows_html, 'html.parser')
    list_shows = list_shows_soup.find_all(
        'div', class_='col-md-6')

    for live in list_shows:
        item = Listitem()
        item.label = live.find('img').get('alt')
        item.art['thumb'] = live.find('img').get('src')
        show_url = URL_ROOT(live.find(
            'a').get('href'))

        item.set_callback(
            list_videos,
            item_id=item_id,
            category_url=show_url
        )
        yield item

    # More videos...
    yield Listitem.next_page(
        item_id=item_id,
        category_url=category_url,
        page=page + 1)


@Route.register
def list_shows_artistes_1(plugin, item_id, category_url, page):
    # Build categories alphabet artistes
    list_alphabet_html = urlquick.get(category_url).text
    list_alphabet_soup = bs(list_alphabet_html, 'html.parser')
    list_alphabet = list_alphabet_soup.find(
        'ul', class_='pagination pagination-artists').find_all('a')

    for alphabet in list_alphabet:
        item = Listitem()
        item.label = alphabet.get_text()
        alphabet_url = URL_ROOT(alphabet.get('href'))

        item.set_callback(
            list_shows_artistes_2,
            item_id=item_id,
            category_url=alphabet_url
        )
        yield item


@Route.register
def list_shows_artistes_2(plugin, item_id, category_url):
    # Build list artistes
    list_artistes_html = urlquick.get(category_url).text
    list_artistes_soup = bs(list_artistes_html, 'html.parser')
    list_artistes = list_artistes_soup.find_all(
        'div', class_='slot slot-artist')

    if not list_artistes:
        plugin.notify(plugin.localize(LABELS['No videos found']), '')
        yield False

    for artiste in list_artistes:
        item = Listitem()
        item.label = artiste.find('img').get('alt')
        artiste_url = URL_ROOT(artiste.find('a').get('href'))
        item.art['thumb'] = 'https:' + artiste.find('img').get('src')

        item.set_callback(
            list_shows_artistes_3,
            item_id=item_id,
            category_url=artiste_url,
        )
        yield item


@Route.register
def list_shows_artistes_3(plugin, item_id, category_url):
    # Build Live and Bonus for an artiste
    videos_artiste_html = urlquick.get(category_url).text
    videos_artiste_soup = bs(videos_artiste_html, 'html.parser')
    videos_artiste = videos_artiste_soup.find(
        'ul', class_='nav nav-tabs').find_all('a')

    if not videos_artiste:
        plugin.notify(plugin.localize(LABELS['No videos found']), '')
        yield False

    for videos in videos_artiste:
        item = Listitem()
        if 'Infos' not in videos.get_text():
            item.label = videos.get_text()
            videos_url = URL_ROOT(videos.get('href'))

        item.set_callback(
            list_videos,
            item_id=item_id,
            category_url=videos_url
        )
        yield item


@Route.register
def list_shows_bonus(plugin, item_id, category_url, page):
    # Build categories bonus
    list_bonus_html = urlquick.get(category_url).text
    list_bonus_soup = bs(list_bonus_html, 'html.parser')
    list_bonus = list_bonus_soup.find(
        'ul', class_='nav nav-pills').find_all('a')

    if not list_bonus:
        plugin.notify(plugin.localize(LABELS['No videos found']), '')
        yield False

    for bonus in list_bonus:
        item = Listitem()
        item.label = bonus.get_text()
        bonus_url = URL_ROOT(bonus.get('href'))

        item.set_callback(
            list_videos_bonus,
            item_id=item_id,
            category_url=bonus_url,
            page=1
        )
        yield item


@Route.register
def list_videos(plugin, item_id, category_url):

    replay_episodes_html = urlquick.get(
        category_url).text
    replay_episodes_soup = bs(replay_episodes_html, 'html.parser')
    video_integral = replay_episodes_soup.find(
        'div', class_='col-md-6')
    all_videos = replay_episodes_soup.find_all(
        'div', class_='col-md-3')

    if video_integral is not None:
        item = Listitem()
        item.label = video_integral.find('img').get('alt')
        video_url = URL_ROOT(video_integral.find(
            'a').get('href'))
        item.art['thumb'] = video_integral.find('img').get('src')

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
            video_url=video_url,
            item_dict=cqu.item2dict(item)
        )
        yield item

    for video in all_videos:

        item = Listitem()
        item.label = video.find('img').get('alt')
        video_url = URL_ROOT(video.find('a').get('href'))
        item.art['thumb'] = video.find('img').get('src')

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
            video_url=video_url,
            item_dict=cqu.item2dict(item)
        )
        yield item


@Route.register
def list_videos_bonus(plugin, item_id, category_url, page):

    replay_episodes_html = urlquick.get(
        category_url + '/page/%s' % str(page)).text
    replay_episodes_soup = bs(replay_episodes_html, 'html.parser')
    video_integral = replay_episodes_soup.find(
        'div', class_='col-md-6')
    all_videos = replay_episodes_soup.find_all(
        'div', class_='col-md-3')

    at_least_one_item = False

    if video_integral is not None:
        at_least_one_item = True
        item = Listitem()
        item.label = video_integral.find('img').get('alt')
        video_url = URL_ROOT(video_integral.find(
            'a').get('href'))
        item.art['thumb'] = video_integral.find('img').get('src')

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
            video_url=video_url,
            item_dict=cqu.item2dict(item)
        )
        yield item

    for video in all_videos:
        at_least_one_item = True
        item = Listitem()
        item.label = video.find('img').get('alt')
        video_url = URL_ROOT(video.find('a').get('href'))
        item.art['thumb'] = video.find('img').get('src')

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
            video_url=video_url,
            item_dict=cqu.item2dict(item)
        )
        yield item

    if page is not None and at_least_one_item:
        # More videos...
        yield Listitem.next_page(
            item_id=item_id,
            category_url=category_url,
            page=page + 1)
    else:
        plugin.notify(plugin.localize(LABELS['No videos found']), '')
        yield False


@Resolver.register
def get_video_url(
        plugin, item_id, video_url, item_dict=None, download_mode=False, video_label=None):
    """Get video URL and start video player"""
    url_selected = ''
    all_datas_videos_quality = []
    all_datas_videos_path = []
    videos_html = urlquick.get(video_url).text
    videos_soup = bs(videos_html, 'html.parser')

    list_videos = videos_soup.find(
        'ul', class_='nav nav-tabs').find_all('a')

    for video in list_videos:
        if '#video-' in video.get('href'):
            # Find a better solution to strip
            all_datas_videos_quality.append(video.get_text().strip())
            # Get link
            value_jwplayer_id = video.get('data-jwplayer-id')
            # Case mp4
            if value_jwplayer_id != '':
                list_streams = videos_soup.find_all(
                    'div', class_='jwplayer')
                for stream in list_streams:
                    if stream.get('id') == value_jwplayer_id:
                        url = stream.get('data-source')
            # Cas Yt
            else:
                video_id = re.compile(
                    'youtube.com/embed/(.*?)\?').findall(videos_html)[0]
                url = resolver_proxy.get_stream_youtube(plugin, video_id, False)

            all_datas_videos_path.append(url + '|referer=%s' % video_url)

        # Get link from FranceTV
        elif '#ftv-player-' in video.get('href'):
            # Get link
            value_ftvlayer_id = video.get('data-ftvplayer-id')
            list_streams = videos_soup.find_all(
                'iframe', class_='embed-responsive-item')
            for stream in list_streams:
                if stream.get('id') == value_ftvlayer_id:
                    url_id = stream.get('src')
            id_embeded = url_id.split('akamaihd.net/')[1]
            json_value = urlquick.get(SHOW_INFO_FTV % id_embeded)
            json_value_parser = json.loads(json_value.text)
            id_diffusion = json_value_parser["video_id"]
            return resolver_proxy.get_francetv_video_stream(plugin, id_diffusion, item_dict, download_mode=download_mode)

    final_url = ''
    if len(all_datas_videos_quality) > 1:
        seleted_item = xbmcgui.Dialog().select(
            plugin.localize(LABELS['choose_video_quality']),
            all_datas_videos_quality)
        if seleted_item == -1:
            return False
        url_selected = all_datas_videos_path[seleted_item]
        final_url = url_selected
    else:
        final_url = all_datas_videos_path[0]

    if download_mode:
        return download.download_video(final_url, video_label)

    return final_url