# -*- coding: utf-8 -*-
# Copyright: (c) 2017, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
from builtins import str
import re

from codequick import Listitem, Resolver, Route
import urlquick

from resources.lib import download
from resources.lib.menu_utils import item_post_treatment


# TO DO

URL_ROOT = 'https://bx1.be'

URL_LIVE = URL_ROOT + '/lives/direct-tv/'

URL_EMISSIONS = URL_ROOT + '/emissions'


@Route.register
def list_programs(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_EMISSIONS)
    root = resp.parse()

    for program_datas in root.iterfind(".//article[@class='news__article']"):

        program_title = program_datas.find('.//h3').text
        program_image = program_datas.find('.//img').get('src')
        program_url = program_datas.find(".//a").get("href")

        item = Listitem()
        item.label = program_title
        item.art['thumb'] = item.art['landscape'] = program_image
        item.set_callback(list_videos,
                          item_id=item_id,
                          program_url=program_url,
                          page='1')
        item_post_treatment(item)
        yield item


@Route.register
def list_videos(plugin, item_id, program_url, page, **kwargs):

    resp = urlquick.get(program_url + 'page/%s/' % page)
    root = resp.parse("div", attrs={"class": "articles"})

    for video_datas in root.iterfind(".//article"):
        video_title = video_datas.find(
            './/h3').text.strip() + ' - ' + video_datas.find('.//span').text
        video_image = video_datas.find('.//img').get('src')
        video_url = video_datas.find('.//a').get('href')

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = item.art['landscape'] = video_image

        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_url=video_url)
        item_post_treatment(item, is_playable=True, is_downloadable=True)

        yield item

    root_change_pages = resp.parse()
    if root_change_pages.find(".//ol[@class='wp-paginate font-inherit']") is not None:
        change_page_node = root_change_pages.find(".//ol[@class='wp-paginate font-inherit']")
        if change_page_node.find(".//a[@class='next']") is not None:
            yield Listitem.next_page(
                item_id=item_id, program_url=program_url, page=str(int(page) + 1))


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_url,
                  download_mode=False,
                  **kwargs):

    resp = urlquick.get(video_url)
    stream_url = re.compile(r'file: "(.*?)m3u8').findall(resp.text)[0]
    final_video_url = stream_url.replace('" + "', '') + 'm3u8'

    if download_mode:
        return download.download_video(final_video_url)
    return final_video_url


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_LIVE)
    return re.compile(r'"file": "(.*?)"').findall(resp.text)[0]
