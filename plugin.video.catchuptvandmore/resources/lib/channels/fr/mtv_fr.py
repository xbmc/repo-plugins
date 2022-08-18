# -*- coding: utf-8 -*-
# Copyright: (c) 2017, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import json
import re

from codequick import Listitem, Resolver, Route
import urlquick

from resources.lib import resolver_proxy
from resources.lib.menu_utils import item_post_treatment


# TO DO
# Add More Videos button
# Add Other Country contents

URL_ROOT = 'http://www.mtv.fr'
# Contents

URL_JSON_MTV = URL_ROOT + '/feeds/triforce/manifest/v8?url=%s'
# URL

URL_EMISSION = URL_ROOT + '/emissions/'

URL_VIDEOS = URL_ROOT + '/dernieres-videos'


@Route.register
def list_categories(plugin, item_id, **kwargs):

    # Prepare All videos
    resp = urlquick.get(URL_JSON_MTV % URL_VIDEOS)
    json_parser = json.loads(resp.text)
    category_title = plugin.localize(30701)
    category_url = json_parser["manifest"]["zones"]["t4_lc_promo1"]["feed"]

    item = Listitem()
    item.label = category_title
    item.set_callback(list_videos, item_id=item_id, next_url=category_url)
    item_post_treatment(item)
    yield item

    # Get Letters
    resp2 = urlquick.get(URL_JSON_MTV % URL_EMISSION)
    json_parser2 = json.loads(resp2.text)
    list_letter_datas_url = json_parser2["manifest"]["zones"]["t5_lc_promo1"][
        "feed"]
    resp3 = urlquick.get(list_letter_datas_url)
    json_parser3 = json.loads(resp3.text)

    for letter_datas in json_parser3["result"]["shows"]:
        letter_title = letter_datas["key"]

        item = Listitem()
        item.label = letter_title
        item.set_callback(list_programs,
                          item_id=item_id,
                          letter_title=letter_title)
        item_post_treatment(item)
        yield item


@Route.register
def list_programs(plugin, item_id, letter_title, **kwargs):

    resp2 = urlquick.get(URL_JSON_MTV % URL_EMISSION)
    json_parser2 = json.loads(resp2.text)
    list_letter_datas_url = json_parser2["manifest"]["zones"]["t5_lc_promo1"][
        "feed"]
    resp3 = urlquick.get(list_letter_datas_url)
    json_parser3 = json.loads(resp3.text)

    for letter_datas in json_parser3["result"]["shows"]:
        if letter_title == letter_datas["key"]:
            for program_datas in letter_datas["value"]:
                program_title = program_datas["title"]
                resp4 = urlquick.get(URL_JSON_MTV % program_datas["url"])
                json_parser4 = json.loads(resp4.text)
                program_url = json_parser4["manifest"]["zones"][
                    "t5_lc_promo1"]["feed"]

                item = Listitem()
                item.label = program_title
                item.set_callback(list_videos,
                                  item_id=item_id,
                                  next_url=program_url)
                item_post_treatment(item)
                yield item


@Route.register
def list_videos(plugin, item_id, next_url, **kwargs):

    resp = urlquick.get(next_url)
    json_parser = json.loads(resp.text)

    if 'data' in json_parser["result"]:
        for video_datas in json_parser["result"]["data"]["items"]:
            video_title = video_datas["title"]
            video_plot = video_datas["description"]
            video_url = video_datas["canonicalURL"]
            if 'images' in video_datas:
                video_image = video_datas["images"]["url"]
            else:
                video_image = ''

            item = Listitem()
            item.label = video_title
            item.art['thumb'] = item.art['landscape'] = video_image
            item.info['plot'] = video_plot

            item.set_callback(get_video_url,
                              item_id=item_id,
                              video_url=video_url)
            item_post_treatment(item, is_playable=True, is_downloadable=True)
            yield item

        if 'nextPageURL' in json_parser["result"]:
            yield Listitem.next_page(
                item_id=item_id, next_url=json_parser["result"]["nextPageURL"])


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_url,
                  download_mode=False,
                  **kwargs):

    resp = urlquick.get(video_url)
    video_id = re.compile(r'itemId":"(.*?)"').findall(resp.text)[0]
    video_uri = 'mgid:arc:video:mtv.fr:' + video_id
    return resolver_proxy.get_mtvnservices_stream(plugin, video_uri,
                                                  download_mode)
