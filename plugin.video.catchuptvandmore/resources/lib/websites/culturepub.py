# -*- coding: utf-8 -*-
# Copyright: (c) 2017, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import re

from codequick import Listitem, Resolver, Route
import urlquick

from resources.lib import download, web_utils
from resources.lib.menu_utils import item_post_treatment


URL_ROOT = 'http://www.culturepub.fr'

URL_PLAYER = 'http://play.culturepub.fr'

INFO_STREAM = URL_PLAYER + '/play/player?player=7&pod=%s'
# IdStream

URL_STREAM = URL_PLAYER + '%s'
# VideoStream


@Route.register
def website_root(plugin, item_id, **kwargs):
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
        video_id = re.compile(r'player=7&pod=(.*?)[\"\&]').findall(
            video_id)[0]

        resp = urlquick.get(INFO_STREAM % video_id)
        stream_id = re.compile(r'src\: \'(.*?)\'').findall(resp.text)[0]

        final_stream_url = URL_STREAM % stream_id.replace('vtt', 'm3u8')

        item.set_callback(final_stream_url,
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
    video_id = re.compile(r'player=7&pod=(.*?)[\"\&]').findall(
        info_video_html)[0]
    resp = urlquick.get(INFO_STREAM % video_id)
    stream_id = re.compile(r'src\: \'(.*?)\'').findall(resp.text)[0]

    final_stream_url = URL_STREAM % stream_id.replace('vtt', 'm3u8')

    if download_mode:
        return download.download_video(final_stream_url)
    return final_stream_url
