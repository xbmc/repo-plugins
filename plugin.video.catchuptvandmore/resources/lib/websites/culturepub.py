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
import json

from resources.lib.codequick import Route, Resolver, Listitem, Script
from resources.lib import urlquick
from kodi_six import xbmcgui

from resources.lib.labels import LABELS
from resources.lib import web_utils
from resources.lib import download
from resources.lib.menu_utils import item_post_treatment


URL_ROOT = 'http://www.culturepub.fr'

INFO_VIDEO = 'http://api.cbnews.webtv.flumotion.com/videos/%s'
# IdVideo

INFO_STREAM = 'http://cbnews.ondemand.flumotion.com/video/mp4/%s/%s.mp4'
# Quality, IdStream

QUALITIES_STREAM = ['low', 'hd']


def website_entry(plugin, item_id, **kwargs):
    """
    First executed function after website_bridge
    """
    return root(plugin, item_id)


def root(plugin, item_id, **kwargs):
    """Add modes in the listing"""

    resp = urlquick.get(URL_ROOT)
    root = resp.parse("ul", attrs={"class": "nav"})

    for category in root.iterfind(".//a[@class='dropdown-toggle']"):

        if 'emissions' in category.get('href'):
            item = Listitem()
            item.label = category.text.strip()
            category_url = URL_ROOT + category.get('href')

            item.set_callback(list_shows,
                              item_id=item_id,
                              category_url=category_url)
            item_post_treatment(item)
            yield item

        elif 'videos' in category.get('href'):
            item = Listitem()
            item.label = category.text.strip()
            category_url = URL_ROOT + category.get('href')

            item.set_callback(list_videos,
                              item_id=item_id,
                              category_url=category_url,
                              page=1)
            item_post_treatment(item)
            yield item

        elif 'playlists' in category.get('href'):
            item = Listitem()
            item.label = category.text.strip()
            category_url = URL_ROOT + category.get('href')

            item.set_callback(list_playlists,
                              item_id=item_id,
                              category_url=category_url,
                              page=1)
            item_post_treatment(item)
            yield item


@Route.register
def list_shows(plugin, item_id, category_url, **kwargs):
    """Build categories listing"""
    resp = urlquick.get(category_url)
    root = resp.parse()

    for show in root.iterfind(".//div[@class='widget-header']"):
        item = Listitem()
        item.label = show.find('h3').text
        show_url = show.find('a').get('href')

        item.set_callback(list_videos,
                          item_id=item_id,
                          page=1,
                          category_url=show_url)
        item_post_treatment(item)
        yield item


@Route.register
def list_playlists(plugin, item_id, page, category_url, **kwargs):
    """Build playlists listing"""
    resp = urlquick.get(category_url + '?paged=%s' % page)
    root = resp.parse()

    for playlist in root.iterfind(".//article"):
        item = Listitem()
        item.label = playlist.find('.//h2').find('a').get('title')
        if playlist.find('.//img').get('data-src'):
            item.art['thumb'] = item.art['landscape'] = playlist.find('.//img').get('data-src')
        else:
            item.art['thumb'] = item.art['landscape'] = playlist.find('.//img').get('src')
        videos_url = URL_ROOT + playlist.find('.//h2').find('a').get('href')

        item.set_callback(list_playlist_videos,
                          item_id=item_id,
                          videos_url=videos_url)
        item_post_treatment(item)
        yield item

    # More videos...
    yield Listitem.next_page(item_id=item_id,
                             category_url=category_url,
                             page=page + 1)


@Resolver.register
def list_playlist_videos(plugin, item_id, videos_url, **kwargs):
    """Build playlist videos listing"""
    resp = urlquick.get(videos_url)
    root = resp.parse()

    playlist_items = []

    for video in root.find(".//div[@class='spots-overflow']").iterfind(".//article"):
        item = Listitem()
        item.label = video.find('.//h2').text
        if video.find('.//img').get('data-src'):
            item.art['thumb'] = item.art['landscape'] = video.find('.//img').get('data-src')
        else:
            item.art['thumb'] = item.art['landscape'] = video.find('.//img').get('src')

        video_id = video.find(".//a").get('data-src')
        video_id = re.compile('player=7&pod=(.*?)[\"\&]').findall(
            video_id)[0]

        info_video_json = urlquick.get(INFO_VIDEO % video_id).text
        info_video_json = json.loads(info_video_json)

        stream_id = re.compile('images/(.*).jpg').findall(
            info_video_json["thumbnail_url_static"])[0].split('/')[1]

        all_datas_videos_path = []
        for quality in QUALITIES_STREAM:
            all_datas_videos_path.append(INFO_STREAM % (quality, stream_id))

        item.set_callback(all_datas_videos_path[-1],
                          is_playable=True)

        playlist_items.append(item)

    return playlist_items


@Route.register
def list_videos(plugin, item_id, page, category_url, **kwargs):
    """Build videos listing"""
    resp = urlquick.get(category_url + '?paged=%s' % page)
    root = resp.parse()

    for video in root.iterfind(".//article"):
        item = Listitem()
        item.label = video.find('.//h2').find('a').get('title')
        if video.find('.//img').get('data-src'):
            item.art['thumb'] = item.art['landscape'] = video.find('.//img').get('data-src')
        else:
            item.art['thumb'] = item.art['landscape'] = video.find('.//img').get('src')
        video_url = URL_ROOT + video.find('.//h2').find('a').get('href')

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

    info_video_html = urlquick.get(video_url,
                                   headers={
                                       'User-Agent': web_utils.get_random_ua()
                                   },
                                   max_age=-1).text
    video_id = re.compile('player=7&pod=(.*?)[\"\&]').findall(
        info_video_html)[0]

    info_video_json = urlquick.get(INFO_VIDEO % video_id).text
    info_video_json = json.loads(info_video_json)

    stream_id = re.compile('images/(.*).jpg').findall(
        info_video_json["thumbnail_url_static"])[0].split('/')[1]

    desired_quality = Script.setting.get_string('quality')
    all_datas_videos_quality = []
    all_datas_videos_path = []
    for quality in QUALITIES_STREAM:
        all_datas_videos_quality.append(quality)
        all_datas_videos_path.append(INFO_STREAM % (quality, stream_id))

    url = ''
    if desired_quality == "DIALOG":
        seleted_item = xbmcgui.Dialog().select(
            plugin.localize(LABELS['choose_video_quality']),
            all_datas_videos_quality)
        if seleted_item == -1:
            url = ''
        url = all_datas_videos_path[seleted_item]
    elif desired_quality == "BEST":
        url_best = ''
        for data_video in all_datas_videos_path:
            url_best = data_video
        url = url_best
    else:
        url = all_datas_videos_path[0]

    if download_mode:
        return download.download_video(url)
    return url
