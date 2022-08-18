# -*- coding: utf-8 -*-
# Copyright: (c) JUL1EN094, SPM, SylvainCecchetto
# Copyright: (c) 2016, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
from builtins import str
import re

from codequick import Listitem, Resolver, Route
import urlquick

from resources.lib import resolver_proxy, web_utils
from resources.lib.menu_utils import item_post_treatment


# TODO
# Get First-diffusion (date of replay Video)
# Add search button

URL_ROOT = 'https://www.publicsenat.fr'

URL_LIVE_SITE = URL_ROOT + '/direct'

URL_CATEGORIES = URL_ROOT + '/recherche/type/episode/field_theme/%s?sort_by=pse_search_date_publication'
# categoriesId

CATEGORIES = {
    'politique-4127': 'Politique',
    'societe-4126': 'Société',
    'debat-4128': 'Débat',
    'parlementaire-53511': 'Parlementaire'
}


@Route.register
def list_categories(plugin, item_id, **kwargs):
    """
    Build categories listing
    - Tous les programmes
    - Séries
    - Informations
    - ...
    """
    for category_id, category_name in list(CATEGORIES.items()):
        category_url = URL_CATEGORIES % category_id

        item = Listitem()
        item.label = category_name
        item.set_callback(list_videos,
                          item_id=item_id,
                          category_url=category_url,
                          page='0')
        item_post_treatment(item)
        yield item


@Route.register
def list_videos(plugin, item_id, category_url, page, **kwargs):

    replay_paged_url = category_url + '&page=' + page
    resp = urlquick.get(replay_paged_url)
    root = resp.parse("div", attrs={"class": "view-content"})

    for video_datas in root.iterfind(".//article"):
        if len(video_datas.findall(".//div[@class='wrapper-duree']")) > 0:
            list_texts = video_datas.findall(
                ".//div[@class='field-item even']")
            if len(list_texts) > 2:
                if list_texts[2].text is not None:
                    video_title = list_texts[1].text + ' - ' + list_texts[2].text
                else:
                    video_title = list_texts[1].text
            elif len(list_texts) > 1:
                video_title = list_texts[1].text
            else:
                video_title = ''
            video_image = video_datas.find('.//img').get('src')
            video_plot = ''
            if len(list_texts) > 3:
                video_plot = list_texts[3].text
            video_duration = int(
                video_datas.findall(".//div[@class='wrapper-duree']")
                [0].text) * 60
            video_url = URL_ROOT + video_datas.findall('.//a')[1].get('href')

            item = Listitem()
            item.label = video_title
            item.art['thumb'] = item.art['landscape'] = video_image
            item.info['duration'] = video_duration
            item.info['plot'] = video_plot

            item.set_callback(get_video_url,
                              item_id=item_id,
                              video_url=video_url)
            item_post_treatment(item, is_playable=True, is_downloadable=True)
            yield item

    yield Listitem.next_page(item_id=item_id,
                             category_url=category_url,
                             page=str(int(page) + 1))


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_url,
                  download_mode=False,
                  **kwargs):

    resp = urlquick.get(video_url,
                        headers={'User-Agent': web_utils.get_random_ua()},
                        max_age=-1)
    video_id = re.compile(
        r'www.dailymotion.com/embed/video/(.*?)[\?\"]').findall(resp.text)[0]
    return resolver_proxy.get_stream_dailymotion(plugin, video_id,
                                                 download_mode)


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_LIVE_SITE,
                        headers={'User-Agent': web_utils.get_random_ua()},
                        max_age=-1)
    video_id = re.compile(
        r'www.dailymotion.com/embed/video/(.*?)[\?\"]').findall(resp.text)[0]
    return resolver_proxy.get_stream_dailymotion(plugin, video_id, False)
