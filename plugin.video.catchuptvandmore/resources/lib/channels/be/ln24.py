# -*- coding: utf-8 -*-
# Copyright: (c) 2019, SylvainCecchetto
# Copyright: (c) 2022, darodi
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals

import re

import urlquick
# noinspection PyUnresolvedReferences
from codequick import Listitem, Resolver, Route, Script
# noinspection PyUnresolvedReferences
from codequick.utils import urljoin_partial

from resources.lib import resolver_proxy
from resources.lib.addon_utils import Quality
from resources.lib.menu_utils import item_post_treatment

URL_ROOT = 'https://www.ln24.be/'
url_constructor = urljoin_partial(URL_ROOT)
URL_LIVE = url_constructor('direct')

# "media_sources": {
#     "live": {"src": "https:\/\/live.digiteka.com\/1\/bEg0RmFLb1JMYXRI\/dGhqbmIw\/hls\/live\/playlist.m3u8",
#              "id": "b7wfnkvf"}}
PATTERN_VIDEO_M3U8 = re.compile(r'\"src\":\s*\"(.*?\.m3u8)\"')

# "media_sources": {
#     "mp4": {
#         "mp4_720": "https:\/\/ngs15c.digiteka.com\/720p\/...2f074e4ae.mp4",
#         "mp4_480": "https:\/\/ngs27c.digiteka.com\/480p\/...c03f229b3.mp4",
#         "mp4_360": "https:\/\/ngs14c.digiteka.com\/360p\/...1fb8fcbcb.mp4",
#         "mp4_240": "https:\/\/ngs21c.digiteka.com\/240p\/...c11e385a5.mp4"
#     }
# },
PATTERN_VIDEO_BEST = re.compile(r'"mp4_720":\s*"([^"]*\.mp4)"')
PATTERN_VIDEO_WORST = re.compile(r'"mp4_240":\s*"([^"]*\.mp4)"')


@Route.register
def list_programs(plugin, item_id, **kwargs):
    item = Listitem.search(list_videos_search)
    item.label = plugin.localize(30715)
    item_post_treatment(item)
    yield item

    resp = urlquick.get(url_constructor("emissions"))
    root_elem = resp.parse("div", attrs={"class": "view-content"})
    results = root_elem.iterfind(".//article")
    for article in results:
        anchor = article.find(".//a[@rel='bookmark']")
        if anchor is None:
            continue

        item = Listitem()
        label = anchor.text
        item.label = re.sub(r'(^\s*|\s{2})', '', label)
        url = url_constructor(anchor.get("href"))
        image = article.find(".//img")
        if image is not None:
            item.art["thumb"] = url_constructor(image.get("src"))

        item.set_callback(video_list, url=url)
        yield item


@Route.register
def list_videos_search(plugin, search_query, **kwargs):
    if search_query is None or len(search_query) == 0:
        return False

    for i in video_list(plugin, url_constructor("recherche?ft=%s") % search_query):
        yield i


@Route.register
def video_list(plugin, url):
    resp = urlquick.get(url)

    root_elem = resp.parse("div", attrs={"class": "view-content"})
    results = root_elem.iterfind(".//article")

    for article in results:

        item = Listitem()

        date = article.findtext(".//time")
        if date is not None:
            trimmed_date = re.sub(r'\s', '', date)
            item.info.date(trimmed_date, "%d.%m.%y")

        found_url = url_constructor(article.find(".//a").get("href"))

        label = article.findtext(".//h3//span")
        if label is None:
            label = article.findtext(".//h3//a")
        item.label = re.sub(r'(^\s*|\s{2})', '', label)
        image = article.find(".//img")
        if image is not None:
            item.art["thumb"] = url_constructor(image.get("src"))

        if "/emission/" in found_url:
            item.set_callback(video_list, url=found_url)
        else:
            item.set_callback(play_video, url=found_url)
        yield item

    pagination_container = resp.parse("div", attrs={"class": "region region-content"})
    next_tag = pagination_container.find(".//ul[@class='pagination js-pager__items']"
                                         "//li[@class='pager__item pager__item--next']//a")
    if next_tag is not None:
        next_url = re.sub(r'\?.*', '', url) + next_tag.get('href')
        yield Listitem.next_page(url=next_url, callback=video_list)


@Resolver.register
def play_video(plugin, url):
    resp = urlquick.get(url)
    try:
        root_elem = resp.parse("video", attrs={"id": "ln24-video"})
        video_url = root_elem.find(".//source").get('src')
        return resolver_proxy.get_stream_with_quality(plugin, video_url=video_url, manifest_type="hls")
    except Exception:
        root_elem = resp.parse("div", attrs={"class": "row video_embed"})
        frame_url = root_elem.find(".//iframe").get('src')
        resp2 = urlquick.get("https:" + frame_url)

        quality = Script.setting.get_string('quality')
        if quality == Quality['WORST']:
            mp4_videos = PATTERN_VIDEO_WORST.findall(resp2.text)
        else:
            mp4_videos = PATTERN_VIDEO_BEST.findall(resp2.text)

        if len(mp4_videos) == 0:
            return False

        video_url = mp4_videos[0].replace("\\", "")
        return video_url


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    resp = urlquick.get(URL_LIVE)
    root_elem = resp.parse("div", attrs={"role": "main"})
    frame_url = root_elem.find(".//iframe").get('src')
    resp2 = urlquick.get("https:" + frame_url)

    m3u8_array = PATTERN_VIDEO_M3U8.findall(resp2.text)
    if len(m3u8_array) == 0:
        return False
    video_url = m3u8_array[0].replace("\\", "")

    return resolver_proxy.get_stream_with_quality(plugin, video_url=video_url, manifest_type="hls")
