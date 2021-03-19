# -*- coding: utf-8 -*-
# Copyright: (c) 2017, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
from builtins import str
import re

from codequick import Listitem, Resolver, Route, utils
import urlquick

from resources.lib import resolver_proxy
from resources.lib.menu_utils import item_post_treatment

# TO DO
# Play Spanish Videos

URL_ROOT = utils.urljoin_partial('https://www.tetesaclaques.tv')


@Route.register
def website_root(plugin, item_id, **kwargs):
    """Add modes in the listing"""
    resp = urlquick.get(URL_ROOT(''))
    root = resp.parse("li", attrs={"id": "menu-videos"})

    for category in root.iterfind(".//li"):
        if 'clips_espagnol' not in category.find('.//a').get('href'):
            item = Listitem()
            if 'personnages' in category.find('.//a').get('href'):
                value_next = 'list_shows'
            else:
                value_next = 'list_videos_1'
            item.label = category.find('.//a').text

            category_url = URL_ROOT(category.find('.//a').get('href'))

            item.set_callback(eval(value_next),
                              item_id=item_id,
                              category_url=category_url,
                              page=1)
            item_post_treatment(item)
            yield item


@Route.register
def list_shows(plugin, item_id, category_url, page, **kwargs):
    """Build categories listing"""

    resp = urlquick.get(category_url)
    root = resp.parse("div", attrs={"class": "personnages"})

    for personnage in root.iterfind(".//a"):
        item = Listitem()
        item.label = personnage.get('title')
        item.art['thumb'] = item.art['landscape'] = URL_ROOT(personnage.find('.//img').get('src'))
        show_url = URL_ROOT(personnage.get('href'))

        item.set_callback(list_videos_2,
                          item_id=item_id,
                          category_url=show_url)
        item_post_treatment(item)
        yield item


@Route.register
def list_videos_1(plugin, item_id, category_url, page, **kwargs):
    """Build videos listing"""
    resp = urlquick.get(category_url + '/par_date/%s' % str(page))

    at_least_one_item = False
    if 'serietele' in category_url or 'zarbi' in category_url:
        root = resp.parse("div", attrs={"class": "serieTele"})

        for episode in root.iterfind(".//div"):
            if episode.find('.//a') is not None and \
                    episode.find(".//img[@class='thumb']") is not None:

                at_least_one_item = True
                item = Listitem()

                item.label = episode.find(".//span[@class='saison-episode']"
                                          ).text.strip() + ' ' + episode.find(
                                              './/img').get('alt')
                video_url = URL_ROOT(episode.find('.//a').get('href'))
                item.art['thumb'] = item.art['landscape'] = URL_ROOT(episode.find('.//img').get('src'))

                item.set_callback(get_video_url,
                                  item_id=item_id,
                                  video_url=video_url)
                item_post_treatment(item,
                                    is_playable=True,
                                    is_downloadable=True)
                yield item

    else:
        root = resp.parse()

        for episode in root.iterfind(".//a[@class='lienThumbCollection']"):
            at_least_one_item = True
            item = Listitem()
            item.label = episode.find('.//img').get('alt')
            video_url = URL_ROOT(episode.get('href'))
            item.art['thumb'] = item.art['landscape'] = URL_ROOT(episode.find('.//img').get('src'))

            item.set_callback(get_video_url,
                              item_id=item_id,
                              video_url=video_url)
            item_post_treatment(item, is_playable=True, is_downloadable=True)
            yield item

    if at_least_one_item:
        # More videos...
        yield Listitem.next_page(item_id=item_id,
                                 category_url=category_url,
                                 page=page + 1)
    else:
        plugin.notify(plugin.localize(30718), '')
        yield False


@Route.register
def list_videos_2(plugin, item_id, category_url, **kwargs):
    """Build videos listing"""
    resp = urlquick.get(category_url)
    root = resp.parse()

    for episode in root.iterfind(".//a[@class='lienThumbCollection']"):
        item = Listitem()
        item.label = episode.find('.//img').get('alt')
        video_url = URL_ROOT(episode.get('href'))
        item.art['thumb'] = item.art['landscape'] = URL_ROOT(episode.find('.//img').get('src'))

        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_url=video_url)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_url,
                  download_mode=False,
                  **kwargs):
    """Get video URL and start video player"""

    video_html = urlquick.get(video_url).text
    if re.compile('AtedraVideo.video_id = "(.*?)"').findall(video_html):
        video_id = re.compile('AtedraVideo.video_id = "(.*?)"').findall(
            video_html)[0]

    else:
        # TO DO Espagnol Video / Return 404 (TO REMOVE)
        return False

    return resolver_proxy.get_stream_youtube(plugin, video_id, download_mode)
