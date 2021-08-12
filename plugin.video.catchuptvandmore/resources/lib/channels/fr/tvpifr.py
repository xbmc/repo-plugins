# -*- coding: utf-8 -*-
# Copyright: (c) 2019, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
from builtins import str
import re

from codequick import Listitem, Resolver, Route
import urlquick

from resources.lib import download
from resources.lib.menu_utils import item_post_treatment


URL_ROOT = 'http://www.tvpi.fr'


@Route.register
def list_categories(plugin, item_id, **kwargs):
    """
    Build categories listing
    - ...
    """
    item = Listitem()
    item.label = 'ACTUS'
    category_url = URL_ROOT + '/categorie/actus/'
    item.set_callback(list_videos_actus, item_id=item_id, category_url=category_url)
    item_post_treatment(item)
    yield item

    item = Listitem()
    item.label = 'VIDÉOS'
    category_url = URL_ROOT + '/autres-videos/'
    item.set_callback(list_videos, item_id=item_id, category_url=category_url, page='1')
    item_post_treatment(item)
    yield item


@Route.register
def list_videos_actus(plugin, item_id, category_url, **kwargs):

    resp = urlquick.get(category_url)
    root = resp.parse()

    for video_datas in root.iterfind(".//article"):
        video_title = video_datas.find(".//a[@class='lien']").text
        video_image = video_datas.find('.//img').get('src')
        video_url = video_datas.find('.//a').get('href')
        date_value = video_datas.find(".//header[@class='fullwidth']").text

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = item.art['landscape'] = video_image
        item.info.date(date_value, "%d-%m-%Y")
        item.set_callback(
            get_video_url,
            item_id=item_id,
            video_url=video_url)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item


@Route.register
def list_videos(plugin, item_id, category_url, page, **kwargs):

    resp = urlquick.get(category_url + 'page/%s' % page)
    root = resp.parse()

    for video_datas in root.iterfind(".//div[@class='texte']"):
        video_title = video_datas.find('.//a').text
        video_url = video_datas.find('.//a').get('href')
        date_value = video_datas.find(".//span[@class='date']").text

        item = Listitem()
        item.label = video_title
        item.info.date(date_value, "%d-%m-%Y")
        item.set_callback(
            get_video_url,
            item_id=item_id,
            video_url=video_url)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item

    yield Listitem.next_page(item_id=item_id, category_url=category_url, page=str(int(page) + 1))


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_url,
                  download_mode=False,
                  **kwargs):
    resp = urlquick.get(video_url)
    final_url = re.compile(
        r'file\'\: \'(.*?)\'').findall(resp.text)[0]

    if download_mode:
        return download.download_video(final_url)
    return final_url


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_ROOT)
    return re.compile(r'file\'\: \'(.*?)\'').findall(resp.text)[0]
