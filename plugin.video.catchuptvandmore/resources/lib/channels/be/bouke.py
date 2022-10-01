# -*- coding: utf-8 -*-
# Copyright: (c) 2022, darodi
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import re

import json
# noinspection PyUnresolvedReferences
from codequick import Listitem, Resolver, Route
# noinspection PyUnresolvedReferences
from codequick.utils import urljoin_partial
import urlquick
from resources.lib import resolver_proxy
from resources.lib.addon_utils import get_item_media_path
from resources.lib.web_utils import html_parser, unquote_plus, get_random_ua

URL_ROOT = 'https://www.bouke.media/'
url_constructor = urljoin_partial(URL_ROOT)

URL_LIVE = url_constructor('direct')

LIVE_PLAYER = 'https://tvlocales-player.freecaster.com/embed/%s.json'

# <script src="https://bouke.fcst.tv/embed/3733922.js?id=video_3733922&amp;autoplay=false"></script>
PATTERN_VIDEO_URL = re.compile(r'script src=\"(.*?/embed/.+.js.*?)\"')

# \"src\":[\"https:\\\/\\\/bouke-vod.freecaster.com\\\/vod\\\/bouke\\\/2NFCKxV842\\\/master.m3u8\"
PATTERN_VIDEO_M3U8 = re.compile(r'\\\"src\\\":\[\\\"(.*?\.m3u8)\\\"')

HEADERS = {
    "User-Agent": get_random_ua(),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
    "Pragma": "no-cache",
    "Cache-Control": "no-cache",
    "referrer": "https://www.bouke.media/",
}


@Route.register
def list_programs(plugin, item_id, **kwargs):
    resp = urlquick.get(url_constructor("/"), headers=HEADERS)
    root_elem = resp.parse("ul", attrs={"block": "block-main-nav-page"})
    for url_tag in root_elem.iterfind("li/a"):
        item = Listitem()
        item.label = url_tag.text
        url = url_tag.get("href")
        if url == '/':
            continue

        item.art["thumb"] = get_item_media_path('channels/be/bouke.png')
        item.set_callback(video_list, url=url)
        yield item


@Route.register
def video_list(plugin, url):
    resp = urlquick.get(url_constructor(url), headers=HEADERS)

    root_elem = resp.parse("section", attrs={"id": "block-tv-theme-content"})
    results = root_elem.iterfind(".//article[@role='article']")

    for article in results:
        item = Listitem()

        date = article.findtext(".//time")
        if date is not None:
            trimmed_date = re.sub(r'\s', '', date)
            item.info.date(trimmed_date, "%d/%m/%Y")  # 21/03/2022

        video_url = article.find(".//a").get("href")

        content = article.find(".//div[@class='content']")
        item.label = content.findtext(".//h2//span")

        plot_containers = content.iterfind(".//div[@class]")
        for plot_container in plot_containers:
            if 'field-type-text-with-summary' in plot_container.get('class'):
                item.info['plot'] = plot_container.findtext(".//div[@class='field-item']")
                break

        image = article.find(".//img").get("src")
        item.art["thumb"] = url_constructor(image)
        item.set_callback(play_video, url=video_url)
        yield item

    next_tag = root_elem.find(".//ul[@class='js-pager__items pager']//a[@rel='next']")
    if next_tag is not None:
        next_url = re.sub(r'\?.*', '', url) + next_tag.get("href")
        yield Listitem.next_page(url=next_url, callback=video_list)


@Resolver.register
def play_video(plugin, url):
    resp = urlquick.get(url_constructor(url), headers=HEADERS, max_age=-1)
    player_urls = PATTERN_VIDEO_URL.findall(resp.text)
    if len(player_urls) == 0:
        return False

    player_url = html_parser.unescape(player_urls[0])
    resp2 = urlquick.get(player_url, max_age=-1)
    m3u8_array = PATTERN_VIDEO_M3U8.findall(resp2.text)
    if len(m3u8_array) == 0:
        return False
    video_url = m3u8_array[0].replace("\\", "")

    return resolver_proxy.get_stream_with_quality(plugin, video_url=video_url, manifest_type="hls")


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    resp = urlquick.get(URL_LIVE, headers=HEADERS, max_age=-1)
    live_data = re.compile(r"live_token\":\"(.*?)\"").findall(resp.text)[0]
    resp2 = urlquick.get(LIVE_PLAYER % live_data, max_age=-1)
    video_url = json.loads(resp2.text)['video']['src'][0]['src']

    return resolver_proxy.get_stream_with_quality(plugin, video_url, manifest_type="hls")
