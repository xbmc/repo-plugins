# -*- coding: utf-8 -*-
# Copyright: (c) 2018, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
from builtins import str
import re

from codequick import Listitem, Resolver, Route
import urlquick

from resources.lib import resolver_proxy, web_utils
from resources.lib.menu_utils import item_post_treatment


# TODO Info replays (date, duration, ...)


URL_ROOT = 'https://www.ktotv.com'

URL_SHOWS = URL_ROOT + '/emissions'


@Route.register
def list_categories(plugin, item_id, **kwargs):
    """
    Build categories listing
    - Tous les programmes
    - Séries
    - Informations
    - ...
    """
    resp = urlquick.get(URL_SHOWS)
    root = resp.parse("div",
                      attrs={"id": "accordion-horizontal"})

    for category_datas in root.iterfind("./div"):
        category_title = category_datas.find(".//h2").text

        item = Listitem()
        item.label = category_title
        item.set_callback(list_sub_categories,
                          item_id=item_id,
                          category_title=category_title)
        item_post_treatment(item)
        yield item


@Route.register
def list_sub_categories(plugin, item_id, category_title, **kwargs):
    """
    Build programs listing
    - Les feux de l'amour
    - ...
    """
    resp = urlquick.get(URL_SHOWS)
    root = resp.parse("div",
                      attrs={"id": "accordion-horizontal"})

    for category_datas in root.iterfind("./div"):
        if category_title in category_datas.find(".//h2").text:
            for sub_category_datas in category_datas.findall(".//div[@class='entry-section clearfix']"):
                sub_category_title = sub_category_datas.find("./p/strong").text

                item = Listitem()
                item.label = sub_category_title
                item.set_callback(list_programs,
                                  item_id=item_id,
                                  category_title=category_title,
                                  sub_category_title=sub_category_title)
                item_post_treatment(item)
                yield item


@Route.register
def list_programs(plugin, item_id, category_title, sub_category_title, **kwargs):
    """
    Build programs listing
    - Les feux de l'amour
    - ...
    """
    resp = urlquick.get(URL_SHOWS)
    root = resp.parse("div",
                      attrs={"id": "accordion-horizontal"})

    for category_datas in root.iterfind("./div"):
        if category_title in category_datas.find(".//h2").text:
            for sub_category_datas in category_datas.findall(".//div[@class='entry-section clearfix']"):
                if sub_category_title in sub_category_datas.find("./p/strong").text:
                    for program_datas in sub_category_datas.findall(".//li"):
                        program_title = program_datas.find('./a').text
                        program_url = URL_ROOT + program_datas.find('./a').get('href')

                        item = Listitem()
                        item.label = program_title
                        item.set_callback(list_videos,
                                          item_id=item_id,
                                          program_url=program_url,
                                          page='1')
                        item_post_treatment(item)
                        yield item


@Route.register
def list_videos(plugin, item_id, program_url, page, **kwargs):

    resp = urlquick.get(program_url + '/%s' % page)
    root = resp.parse()

    for video_datas in root.iterfind(
            ".//div[@class='col-xl-2 col-lg-3 col-md-4 col-sm-6 col-xs-12 withSynopsis playlist-hover single']"):
        video_title = video_datas.find('.//h5/a').text
        video_image_info = video_datas.find(".//a[@class='image']").get('style')
        video_image = re.compile(
            r'url\(\'(.*?)\'').findall(video_image_info)[0]
        video_plot = ''
        if video_datas.find('.//p') is not None:
            video_plot = video_datas.find('.//p').text
        video_url = URL_ROOT + video_datas.find('.//a').get('href')

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = item.art['landscape'] = video_image
        item.info['plot'] = video_plot

        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_url=video_url)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item

    yield Listitem.next_page(item_id=item_id,
                             program_url=program_url,
                             page=str(int(page) + 1))


@Resolver.register
def get_video_url(plugin,
                  video_url,
                  download_mode=False,
                  **kwargs):

    resp = urlquick.get(video_url,
                        headers={'User-Agent': web_utils.get_random_ua()},
                        max_age=-1)
    video_id = re.compile(r'www.youtube.com/embed/(.*?)[\?\"]').findall(
        resp.text)[0]

    return resolver_proxy.get_stream_youtube(plugin, video_id, download_mode)


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_ROOT,
                        headers={'User-Agent': web_utils.get_random_ua()},
                        max_age=-1)
    list_url_stream = re.compile(r'window.direct_video.src \= \'(.*?)\'').findall(resp.text)
    video_url = ''
    for url_stream_data in list_url_stream:
        if 'm3u8' in url_stream_data:
            video_url = url_stream_data
    return resolver_proxy.get_stream_with_quality(plugin, video_url, manifest_type="hls")
