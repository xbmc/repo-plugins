# -*- coding: utf-8 -*-
# Copyright: (c) 2019, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import re
try:  # Python 3
    from urllib.parse import unquote_plus
except ImportError:  # Python 2
    from urllib import unquote_plus

from codequick import Listitem, Resolver, Route
import urlquick

from resources.lib import download, resolver_proxy
from resources.lib.menu_utils import item_post_treatment


# TO DO
# Add Replay

URL_ROOT = 'https://www.canalc.be'

URL_LIVE = URL_ROOT + '/live/'

URL_EMISSIONS = URL_ROOT + '/nos-emissions-2/'


@Route.register
def list_programs(plugin, item_id, **kwargs):

    program_title = 'Le dernier JT'
    program_url = URL_ROOT + '/category/jt-complet/'
    item = Listitem()
    item.label = program_title
    item.set_callback(list_videos,
                      item_id=item_id,
                      program_url=program_url,
                      page='1')
    item_post_treatment(item)
    yield item

    program_title = 'L\'actu par communes'
    program_url = URL_ROOT + '/lactu-par-communes/'
    item = Listitem()
    item.label = program_title
    item.set_callback(list_communes,
                      item_id=item_id,
                      program_url=program_url,
                      page='1')
    item_post_treatment(item)
    yield item

    resp = urlquick.get(URL_EMISSIONS)
    root = resp.parse("tbody")

    for program_datas in root.iterfind(".//a"):

        program_title = program_datas.find('.//img').get('alt')
        program_image = program_datas.find('.//img').get('src')
        if 'www.canalc.be' in program_datas.get("href"):
            program_url = program_datas.get("href").strip()
        else:
            program_url = URL_ROOT + program_datas.get("href")

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
def list_communes(plugin, item_id, program_url, page, **kwargs):

    return False


@Route.register
def list_videos(plugin, item_id, program_url, page, **kwargs):

    if page == '1':
        resp = urlquick.get(program_url)
    else:
        resp = urlquick.get(program_url + 'page/%s/' % page)
    root = resp.parse()

    for video_datas in root.iterfind(".//article"):
        if video_datas.find(".//h2") is not None:
            video_title = video_datas.find(
                './/h2/a').text
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

    if root.find(".//span[@class='pages']") is not None:
        yield Listitem.next_page(
            item_id=item_id, program_url=program_url, page=str(int(page) + 1))


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_url,
                  download_mode=False,
                  **kwargs):

    resp = urlquick.get(video_url)

    if len(re.compile(r'source src\=\"(.*?)\"').findall(resp.text)) > 0:
        stream_url = re.compile(
            r'source src\=\"(.*?)\"').findall(resp.text)[0]

        if download_mode:
            return download.download_video(stream_url)
        return stream_url

    video_id = re.compile(r'www.youtube.com\/embed\/(.*?)\"').findall(resp.text)[0]
    return resolver_proxy.get_stream_youtube(plugin, video_id, download_mode)


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_LIVE, max_age=-1)
    return unquote_plus(re.compile(r'sourceURL\"\:\"(.*?)\"').findall(resp.text)[0])
