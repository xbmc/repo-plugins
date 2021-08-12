# -*- coding: utf-8 -*-
# Copyright: (c) 2019, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
from builtins import str
import re

from codequick import Listitem, Resolver, Route
import urlquick

from resources.lib import resolver_proxy
from resources.lib.menu_utils import item_post_treatment


URL_ROOT = "https://www.africa24tv.com"


@Route.register
def list_categories(plugin, item_id, **kwargs):
    """
    Build categories listing
    - ...
    """
    category_emission_url = URL_ROOT + "/fr/a24-nos-emissions"
    item = Listitem()
    item.label = "Emissions"
    item.set_callback(
        list_programs,
        item_id=item_id,
        category_emission_url=category_emission_url)
    item_post_treatment(item)
    yield item

    resp = urlquick.get(URL_ROOT)
    root = resp.parse("section", attrs={"class": "block block-project-menu"})

    for category_datas in root.iterfind(".//li"):
        category_title = category_datas.find("a").get("title")
        category_url = URL_ROOT + category_datas.find("a").get("href")

        item = Listitem()
        item.label = category_title
        item.set_callback(
            list_videos_category,
            item_id=item_id,
            category_url=category_url,
            page="0")
        item_post_treatment(item)
        yield item


@Route.register
def list_programs(plugin, item_id, category_emission_url, **kwargs):
    """
    Build programs listing
    - ...
    """
    resp = urlquick.get(category_emission_url)
    root = resp.parse()

    for program_datas in root.iterfind(".//div"):
        if program_datas.get("class") is not None:
            if "col-xs-12 col-md-12 col-sm-12 col-lg-12" in program_datas.get(
                    "class"):
                program_title = program_datas.findall(".//span/a")[1].text
                program_image = program_datas.find(".//img").get("src")
                program_url = URL_ROOT + program_datas.find(".//a").get("href")
                program_plot = ""
                if program_datas.find(".//p") is not None:
                    program_plot = program_datas.find(".//p").text

                item = Listitem()
                item.label = program_title
                item.art['thumb'] = item.art['landscape'] = program_image
                item.info["plot"] = program_plot
                item.set_callback(
                    list_videos,
                    item_id=item_id,
                    program_url=program_url,
                    page="0")
                item_post_treatment(item)
                yield item


@Route.register
def list_videos(plugin, item_id, program_url, page, **kwargs):

    resp = urlquick.get(program_url + "?page=%s" % page)
    root = resp.parse("aside", attrs={"class": "col-xs-12 col-lg-12 col-sm-12"})

    for video_datas in root.findall(".//div"):
        if video_datas.get("class") is not None:
            if "col-xs-12 col-md-12 col-lg-12" in video_datas.get(
                    "class"):
                video_title = video_datas.findall(".//span/a")[1].text
                video_image = video_datas.find(".//img").get("src")
                video_url = URL_ROOT + video_datas.find(".//a").get("href")

                item = Listitem()
                item.label = video_title
                item.art['thumb'] = item.art['landscape'] = video_image

                item.set_callback(
                    get_video_url,
                    item_id=item_id,
                    video_url=video_url,
                )
                item_post_treatment(
                    item, is_playable=True, is_downloadable=True)
                yield item

    yield Listitem.next_page(
        item_id=item_id, program_url=program_url, page=str(int(page) + 1))


@Route.register
def list_videos_category(plugin, item_id, category_url, page, **kwargs):

    resp = urlquick.get(category_url + "?page=%s" % page)
    root = resp.parse()

    for video_datas in root.iterfind(".//div"):
        if video_datas.get("class") is not None:
            if "col-xs-12 col-md-12 col-lg-12" in video_datas.get("class"):
                video_title = video_datas.findall(".//span/a")[1].text
                video_image = video_datas.find(".//img").get("src")
                video_url = URL_ROOT + video_datas.find(".//a").get("href")
                video_plot = ""
                if video_datas.find(".//p") is not None:
                    video_plot = video_datas.find(".//p").text

                item = Listitem()
                item.label = video_title
                item.art['thumb'] = item.art['landscape'] = video_image
                item.info["plot"] = video_plot

                item.set_callback(
                    get_video_url,
                    item_id=item_id,
                    video_url=video_url,
                )
                item_post_treatment(
                    item, is_playable=True, is_downloadable=True)
                yield item

    yield Listitem.next_page(
        item_id=item_id, category_url=category_url, page=str(int(page) + 1))


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_url,
                  download_mode=False,
                  **kwargs):

    resp = urlquick.get(video_url)
    video_id = re.compile(r"youtube\.com\/embed\/(.*?)\"").findall(
        resp.text)[0]
    return resolver_proxy.get_stream_youtube(plugin, video_id, download_mode)


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_ROOT)
    live_id = re.compile(r"youtube\.com\/embed\/(.*?)\"").findall(resp.text)[0]
    return resolver_proxy.get_stream_youtube(plugin, live_id, False)
