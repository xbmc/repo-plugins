# -*- coding: utf-8 -*-
# Copyright: (c) 2016-2020, Team Catch-up TV & More
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals

import json
import re

import urlquick
# noinspection PyUnresolvedReferences
from codequick import Listitem, Resolver, Route
# noinspection PyUnresolvedReferences
from codequick.utils import urljoin_partial

from resources.lib import resolver_proxy
from resources.lib.menu_utils import item_post_treatment

URL_ROOT = 'https://www.telesambre.be'

url_constructor = urljoin_partial(URL_ROOT)

URL_LIVE = url_constructor('/direct')

LIVE_PLAYER = 'https://tvlocales-player.freecaster.com/embed/%s.json'

# <script src="https://telesambre.fcst.tv/embed/3139342.js?id=video_3139342&amp;autoplay=true&amp;muted=true"></script>
PATTERN_VIDEO_JS = re.compile(r'<script src=\"(.*?/embed/.*?\.js).*\">')

# \"src\":[\"https:\\\/\\\/telesambre-vod.freecaster.com\\\/vod\\\/telesambre\\\/YhmqWrJ623\\\/master.m3u8\"
PATTERN_VIDEO_M3U8 = re.compile(r'\\\"src\\\":\[\\\"(.*?\.m3u8)\\\"')

# \"src\":[\"https:\\\/\\\/telesambre-vod.freecaster.com\\\/vod\\\/telesambre\\\/TVL00049BA-720p.mp4\"]
PATTERN_VIDEO_MP4 = re.compile(r'\\\"src\\\":\[\\\"(.*?\.mp4)\\\"')


@Route.register
def list_root(plugin, item_id, **kwargs):
    menus = [
        ('Info locales', '/dernieres-actu', list_categories),
        ('Sport', '/sports', list_categories),
        ('Culture', '/culture', list_categories),
        ('Nos émissions', '/nos-emissions', list_emissions)
    ]

    for (label, url, callback) in menus:
        item = Listitem()
        item.label = label
        item.set_callback(callback, item_id, url)
        item_post_treatment(item)
        yield item


@Route.register
def list_categories(plugin, item_id, url, **kwargs):
    resp = urlquick.get(url_constructor(url), max_age=-1)
    root_elem = resp.parse("div", attrs={"class": "views-element-container"})

    for article in root_elem.iterfind(".//article"):
        item = Listitem()

        # date = article.findtext(".//span[@class='post-created']")
        # if date is not None:
        #     trimmed_date = re.sub(r'\s', '', date)
        #     item.info.date(trimmed_date, "%d/%m/%Y")  # 03 octobre 2022  # TODO

        item.label = article.findtext(".//span[@property='schema:name']")
        item.info['plot'] = article.findtext(".//div[@class='post-body']")
        image = article.find(".//img").get("src")
        item.art["thumb"] = url_constructor(image)

        # bypass video if no js player found
        video_url = url_constructor(article.find(".//a").get("href"))
        resp2 = urlquick.get(video_url)
        js_player_array = PATTERN_VIDEO_JS.findall(resp2.text)
        if len(js_player_array) == 0:
            continue

        item.set_callback(play_video, url=js_player_array[0])
        yield item

    pager = resp.parse("nav", attrs={"class": "pager"})
    next_tag = pager.find(".//ul//li//a[@rel='next']")
    if next_tag is not None:
        next_url = re.sub(r'\?.*', '', url) + next_tag.get("href")
        yield Listitem.next_page(url=next_url, item_id=item_id, callback=list_categories)


@Route.register
def list_emissions(plugin, item_id, url, **kwargs):
    resp = urlquick.get(url_constructor(url), max_age=-1)
    root_elem = resp.parse("div", attrs={"class": "views-element-container"})

    for emission in root_elem.iterfind(".//span[@class='field-content']"):

        anchor = emission.find(".//a")
        if anchor is None:
            continue

        emission_url = url_constructor(anchor.get("href"))
        if "/emission/" in emission_url:
            callback = list_emission_videos
            item_url = emission_url
        else:
            callback = play_video
            # bypass video if no js player found
            resp2 = urlquick.get(emission_url)
            js_player_array = PATTERN_VIDEO_JS.findall(resp2.text)
            if len(js_player_array) == 0:
                continue
            item_url = js_player_array[0]

        for i in create_item(emission, item_id, item_url, callback):
            yield i


def create_item(emission, item_id, item_url, callback):
    item = Listitem()
    # date = emission.findtext(".//span[@class='post-created']")
    # if date is not None:
    #     trimmed_date = re.sub(r'\s', '', date)
    #     item.info.date(trimmed_date, "%d/%m/%Y")  # 03 octobre 2022  # TODO
    item.label = emission.findtext(".//div[@class='post-title']")
    if item.label is None or item.label == '':
        item.label = emission.findtext(".//div[@class='post-title']//a")
    item.info['plot'] = item.label
    image = emission.find(".//img").get("src")
    item.art["thumb"] = url_constructor(image)
    item.set_callback(callback, item_id=item_id, url=item_url)
    yield item


@Route.register
def list_emission_videos(plugin, item_id, url, **kwargs):
    resp = urlquick.get(url_constructor(url), max_age=-1)
    root_elem = resp.parse()
    container = root_elem.find(".//div[@class='views-element-container']")
    for video in container.iterfind(".//div[@class='video-block']"):

        anchor = video.find(".//a")
        if anchor is None:
            continue

        # bypass video if no js player found
        emission_url = url_constructor(anchor.get("href"))
        resp2 = urlquick.get(emission_url)
        js_player_array = PATTERN_VIDEO_JS.findall(resp2.text)
        if len(js_player_array) == 0:
            continue
        item_url = js_player_array[0]
        for i in create_item(video, item_id, item_url, play_video):
            yield i

    pager = root_elem.find(".//nav[@class='pager']")
    if pager:
        next_tag = pager.find(".//ul//li//a[@rel='next']")
        if next_tag:
            next_url = re.sub(r'\?.*', '', url) + next_tag.get("href")
            yield Listitem.next_page(url=next_url, item_id=item_id, callback=list_emission_videos)


@Resolver.register
def play_video(plugin, url, **kwargs):
    resp = urlquick.get(url)

    m3u8_array = PATTERN_VIDEO_M3U8.findall(resp.text)
    if len(m3u8_array) == 0:
        mp4_array = PATTERN_VIDEO_MP4.findall(resp.text)
        if len(mp4_array) == 0:
            return False
        else:
            return mp4_array[0].replace("\\", "")
    else:
        video_url = m3u8_array[0].replace("\\", "")
        return resolver_proxy.get_stream_with_quality(plugin, video_url=video_url, manifest_type="hls")


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    resp = urlquick.get(URL_LIVE, max_age=-1)
    root = resp.parse()

    live_data = root.findall(".//div[@class='freecaster-player']")[0].get('data-fc-token')
    resp2 = urlquick.get(LIVE_PLAYER % live_data, max_age=-1)
    video_url = json.loads(resp2.text)['video']['src'][0]['src']

    return resolver_proxy.get_stream_with_quality(plugin, video_url, manifest_type="hls")
