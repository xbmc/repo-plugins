# -*- coding: utf-8 -*-
# Copyright: (c) 2017, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
from builtins import str
import json
import re

from codequick import Listitem, Resolver, Route, utils
import urlquick
from kodi_six import xbmcgui

from resources.lib import download, resolver_proxy
from resources.lib.menu_utils import item_post_treatment

# TO DO
# Fix Bonus

URL_ROOT = utils.urljoin_partial('https://mytaratata.com')

URL_EMBED_FTV = 'http://api-embed.webservices.francetelevisions.fr/key/%s'
# Id Video
# http://embed.francetv.fr/?ue=fb23d5e2c7e5c020b2e710c5fe233aea

SHOW_INFO_FTV = 'https://api-embed.webservices.francetelevisions.fr/v2/key/%s'
# idEmbeded


@Route.register
def website_root(plugin, item_id, **kwargs):
    """Add modes in the listing"""
    resp = urlquick.get(URL_ROOT(''))
    root = resp.parse("ul", attrs={"class": "nav navbar-nav"})

    for category in root.iterfind(".//a"):
        item = Listitem()
        item.label = category.text
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

        item.set_callback(eval(value_next),
                          item_id=item_id,
                          category_url=category_url,
                          page=1)
        item_post_treatment(item)
        yield item


@Route.register
def list_shows_taratata(plugin, item_id, category_url, page, **kwargs):
    resp = urlquick.get(category_url + '/page/%s' % str(page))
    root = resp.parse()

    for live in root.iterfind(".//div[@class='col-md-6']"):
        item = Listitem()
        item.label = live.find('.//img').get('alt')
        item.art['thumb'] = item.art['landscape'] = live.find('.//img').get('src')
        show_url = URL_ROOT(live.find('.//a').get('href'))

        item.set_callback(list_videos, item_id=item_id, category_url=show_url)
        item_post_treatment(item)
        yield item

    # More videos...
    yield Listitem.next_page(item_id=item_id,
                             category_url=category_url,
                             page=page + 1)


@Route.register
def list_shows_artistes_1(plugin, item_id, category_url, page, **kwargs):
    # Build categories alphabet artistes
    resp = urlquick.get(category_url)
    root = resp.parse("ul", attrs={"class": "pagination pagination-artists"})

    for alphabet in root.iterfind(".//a"):
        item = Listitem()
        item.label = alphabet.text
        alphabet_url = URL_ROOT(alphabet.get('href'))

        item.set_callback(list_shows_artistes_2,
                          item_id=item_id,
                          category_url=alphabet_url)
        item_post_treatment(item)
        yield item


@Route.register
def list_shows_artistes_2(plugin, item_id, category_url, **kwargs):
    # Build list artistes
    resp = urlquick.get(category_url)
    root = resp.parse()

    for artiste in root.iterfind(".//div[@class='slot slot-artist']"):
        item = Listitem()
        item.label = artiste.find('.//img').get('alt')
        artiste_url = URL_ROOT(artiste.find('.//a').get('href'))
        item.art['thumb'] = item.art['landscape'] = 'https:' + artiste.find('.//img').get('src')

        item.set_callback(
            list_shows_artistes_3,
            item_id=item_id,
            category_url=artiste_url,
        )
        item_post_treatment(item)
        yield item


@Route.register
def list_shows_artistes_3(plugin, item_id, category_url, **kwargs):
    # Build Live and Bonus for an artiste
    resp = urlquick.get(category_url)
    root = resp.parse("ul", attrs={"class": "nav nav-tabs"})

    for videos in root.iterfind(".//a"):
        item = Listitem()
        if 'Infos' not in videos.text:
            item.label = videos.text
            videos_url = URL_ROOT(videos.get('href'))

        item.set_callback(list_videos,
                          item_id=item_id,
                          category_url=videos_url)
        item_post_treatment(item)
        yield item


@Route.register
def list_shows_bonus(plugin, item_id, category_url, page, **kwargs):
    # Build categories bonus
    resp = urlquick.get(category_url)
    root = resp.parse("ul", attrs={"class": "nav nav-pills"})

    for bonus in root.iterfind(".//a"):
        item = Listitem()
        item.label = bonus.text
        bonus_url = URL_ROOT(bonus.get('href'))

        item.set_callback(list_videos_bonus,
                          item_id=item_id,
                          category_url=bonus_url,
                          page=1)
        item_post_treatment(item)
        yield item


@Route.register
def list_videos(plugin, item_id, category_url, **kwargs):

    resp = urlquick.get(category_url)
    root = resp.parse()

    video_integral = root.find(".//div[@class='col-md-6']")
    if video_integral is not None:
        item = Listitem()
        item.label = video_integral.find('.//img').get('alt')
        video_url = URL_ROOT(video_integral.find('.//a').get('href'))
        item.art['thumb'] = item.art['landscape'] = video_integral.find('.//img').get('src')

        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_url=video_url)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item

    for video in root.iterfind(".//div[@class='col-md-3']"):

        item = Listitem()
        item.label = video.find('.//img').get('alt')
        video_url = URL_ROOT(video.find('.//a').get('href'))
        item.art['thumb'] = item.art['landscape'] = video.find('.//img').get('src')

        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_url=video_url)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item


@Route.register
def list_videos_bonus(plugin, item_id, category_url, page, **kwargs):

    resp = urlquick.get(category_url + '/page/%s' % str(page))
    root = resp.parse()

    at_least_one_item = False

    video_integral = root.find(".//div[@class='col-md-6']")
    if video_integral is not None:
        at_least_one_item = True
        item = Listitem()
        item.label = video_integral.find('.//img').get('alt')
        video_url = URL_ROOT(video_integral.find('.//a').get('href'))
        item.art['thumb'] = item.art['landscape'] = video_integral.find('.//img').get('src')

        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_url=video_url)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item

    for video in root.iterfind(".//div[@class='col-md-3']"):
        at_least_one_item = True
        item = Listitem()
        item.label = video.find('.//img').get('alt')
        video_url = URL_ROOT(video.find('.//a').get('href'))
        item.art['thumb'] = item.art['landscape'] = video.find('.//img').get('src')

        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_url=video_url)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item

    if page is not None and at_least_one_item:
        # More videos...
        yield Listitem.next_page(item_id=item_id,
                                 category_url=category_url,
                                 page=page + 1)
    else:
        plugin.notify(plugin.localize(30718), '')
        yield False


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_url,
                  download_mode=False,
                  **kwargs):
    """Get video URL and start video player"""
    url_selected = ''
    all_datas_videos_quality = []
    all_datas_videos_path = []
    videos_html = urlquick.get(video_url)
    root = videos_html.parse()
    root_videos = videos_html.parse("ul", attrs={"class": "nav nav-tabs"})

    for video in root_videos.iterfind(".//a"):
        if '#video-' in video.get('href'):
            # Find a better solution to strip
            if video.find('.//span') is not None:
                all_datas_videos_quality.append(video.text.strip() + ' ' +
                                                video.find('.//span').text)
            else:
                all_datas_videos_quality.append(video.text)
            # Get link
            value_jwplayer_id = video.get('data-jwplayer-id')
            # Case mp4
            url = ''
            if value_jwplayer_id != '':
                for stream in root.iterfind(".//div[@class='jwplayer']"):
                    if stream.get('id') == value_jwplayer_id:
                        url = stream.get('data-source')
            # Cas Yt
            else:
                video_id = re.compile('youtube.com/embed/(.*?)\?').findall(
                    videos_html.text)[0]
                url = resolver_proxy.get_stream_youtube(
                    plugin, video_id, False)

            all_datas_videos_path.append(url + '|referer=%s' % video_url)

        # Get link from FranceTV
        elif '#ftv-player-' in video.get('href'):
            # Get link
            value_ftvlayer_id = video.get('data-ftvplayer-id')
            for stream in root.iterfind(
                    ".//iframe[@class='embed-responsive-item']"):
                if stream.get('id') == value_ftvlayer_id:
                    url_id = stream.get('src')
            id_embeded = url_id.split('akamaihd.net/')[1]
            json_value = urlquick.get(SHOW_INFO_FTV % id_embeded)
            json_value_parser = json.loads(json_value.text)
            id_diffusion = json_value_parser["video_id"]
            return resolver_proxy.get_francetv_video_stream(
                plugin, id_diffusion, download_mode=download_mode)

    final_url = ''
    if len(all_datas_videos_quality) > 1:
        seleted_item = xbmcgui.Dialog().select(
            plugin.localize(30709),
            all_datas_videos_quality)
        if seleted_item == -1:
            return False
        url_selected = all_datas_videos_path[seleted_item]
        final_url = url_selected
    else:
        final_url = all_datas_videos_path[0]

    if download_mode:
        return download.download_video(final_url)

    return final_url
