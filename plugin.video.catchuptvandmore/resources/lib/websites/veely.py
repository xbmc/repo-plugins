# -*- coding: utf-8 -*-
# Copyright: (c) 2022, darodi
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals

import re
from xml.etree import ElementTree

import urlquick
# noinspection PyUnresolvedReferences
from codequick import Listitem, Resolver, Route
# noinspection PyUnresolvedReferences
from codequick.utils import urljoin_partial, strip_tags

from resources.lib import resolver_proxy
from resources.lib.web_utils import get_random_ua, unquote_plus

DATA_PLAYER_PREFIX = "data-player-"
DATA_PREFIX = "data-"

URL_ROOT = 'https://veely.tv/'
url_constructor = urljoin_partial(URL_ROOT)

URL_LIVE = url_constructor('live')
URL_ON_DEMAND = url_constructor('explore/6165')

SSMP_API = "https://mm-v2.simplestream.com/ssmp/api.php?id=%s&env=%s"
STREAM_API = "https://v2-streams-elb.simplestreamcdn.com/api/%s/stream/%s?key=%s&platform=firefox"

SEASON_EPISODE_PATTERN = re.compile(r'S(\d+)\s.*Ep(\d+)')
DURATION_PATTERN = re.compile(r'(\d+) min')

GENERIC_HEADERS = {"User-Agent": get_random_ua()}


@Route.register
def website_root(plugin, item_id, **kwargs):
    resp = urlquick.get(URL_ROOT, headers=GENERIC_HEADERS, max_age=-1)

    # Home page carousels
    for i in yield_carousels(URL_ROOT):
        yield i

    # Navbar
    root_nav = resp.parse("ul", attrs={"class": "nav navbar-nav"})
    for url_tag in root_nav.iterfind("li/a"):
        item = Listitem()
        item.label = url_tag.get("aria-label")
        url = url_tag.get("href")
        if url == '/' or url == '/apps' or url == '/tvguide' or url == '/live/':
            continue

        item.set_callback(list_programs, url=url)
        yield item


def yield_carousels(url):
    main = urlquick.get(url, headers=GENERIC_HEADERS, max_age=-1).parse("main")

    found_plot = main.find(".//div[@class='series-hero__infoblock']")
    found_image = main.find(".//div[@class='series-hero__carousel']//img")

    for div in main.findall(".//div"):

        if div.get("class") is None \
                or ("carousel" not in div.get("class").split(' ')
                    and "series-carousels" not in div.get("class").split(' ')):
            continue

        elif "series-carousels" in div.get("class").split(' '):
            series = div.findall("./h2")
            inner_divs = div.findall("./div")
            i = 0
            for serie in series:
                episodes_div = inner_divs[i].find("./div")
                item = Listitem()
                i += 1
                item.label = serie.text

                if found_plot is None:
                    item.info['plot'] = item.label
                elif found_plot.text is not None:
                    item.info['plot'] = found_plot.text
                elif found_plot.find(".//p") is None:
                    item.info['plot'] = item.label
                else:
                    item.info['plot'] = found_plot.find(".//p").text

                if found_image is not None:
                    item.art["thumb"] = append_schema(found_image.get("src"))

                items = list_carousel_items(episodes_div, item.info['plot'])
                if len(items) == 0:
                    continue
                item.set_callback(list_items, items=items)
                yield item
        else:
            item = Listitem()
            title = div.get("data-carousel-title")
            if title is None:
                continue
            item.label = title
            items = list_carousel_items(div)
            if len(items) == 0:
                continue
            item.set_callback(list_items, items=items)
            yield item


def list_carousel_items(div, plot=None):
    items = []
    for anchor_tag in div.iterfind("a"):
        if anchor_tag.get("class") is None or "thumbnail" not in anchor_tag.get("class").split(' '):
            continue

        item = Listitem()
        item.label = anchor_tag.find(".//div[@class='title-info']//h3").text
        url = "%s" % anchor_tag.get("href")
        img_src = anchor_tag.find(".//img").get("data-src")
        item.art["thumb"] = append_schema(img_src)

        if plot is not None:
            item.info['plot'] = plot

        season_episode_tag = anchor_tag.find(".//p[@class='details']//span[@class='pull-left']")
        if season_episode_tag is not None and season_episode_tag.text is not None:
            season_episode = SEASON_EPISODE_PATTERN.findall(season_episode_tag.text)
            if len(season_episode) > 0:
                item.info['mediatype'] = "episode"
                episode_str = season_episode[0][1]
                item.info['episode'] = int(episode_str)
                season_str = season_episode[0][0]
                item.info['season'] = int(season_str)
                item.label = "S" + season_str + "E" + episode_str + " - " + item.label

        duration_tag = anchor_tag.find(".//p[@class='details']//span[@class='duration pull-right']")
        if duration_tag is not None:
            duration_html = ElementTree.tostring(duration_tag, encoding='utf8', method='html')
            duration = DURATION_PATTERN.findall(strip_tags(str(duration_html)))
            if len(duration) > 0:
                item.info['duration'] = int(duration[0]) * 60

        if "/watch/" in url or "/live/" in url:
            if "/live/" in url:
                item.info['plot'] = item.label
                item.label = unquote_plus(url.split('/')[len(url.split('/')) - 1])
            item.set_callback(play_video, url=url)
        else:
            item.set_callback(list_programs, url=url)
        items.append(item)
    return items


@Route.register
def list_items(plugin, items, **kwargs):
    for item in items:
        yield item


@Route.register
def list_programs(plugin, url, **kwargs):
    program = url_constructor(url)

    if (URL_ON_DEMAND == program) or (URL_ON_DEMAND + '/' == program):
        resp = urlquick.get(program, headers=GENERIC_HEADERS, max_age=-1)
        root_elem = resp.parse("main").find(".//div[@class='container-fluid']")
        for url_tag in root_elem.iterfind(".//a"):
            if url_tag.get("class") is None or "thumbnail" not in url_tag.get("class"):
                continue
            item = Listitem()
            item.label = url_tag.find(".//img").get("alt")
            item.info['plot'] = item.label
            tag_url = url_tag.get("href")
            img_src = url_tag.find(".//img").get("data-src")
            item.art["thumb"] = append_schema(img_src)
            item.set_callback(list_programs, url=tag_url)
            yield item
    elif (URL_LIVE != program) and (URL_LIVE + '/' != program):
        for i in yield_carousels(program):
            yield i


def append_schema(url):
    if not url.startswith("http://") and not url.startswith("https://"):
        url = re.sub(r'/$', '', URL_ROOT) + ("" if url.startswith("/") else "/") + url
    return url


@Resolver.register
def play_video(plugin, url, **kwargs):
    full_url = url_constructor(url)

    player_path = ".//div[@id='vod-player']"
    prefix = DATA_PREFIX
    resource = "show"

    if "/live/" in url:
        player_path = ".//div[@id='live-player-root']"
        prefix = DATA_PLAYER_PREFIX
        resource = "live"

    main = urlquick.get(full_url, headers=GENERIC_HEADERS, max_age=-1).parse("main")
    player = main.find(player_path)

    data_id = player.get("%sid" % prefix)
    data_env = player.get("%senv" % prefix)
    data_uvid = player.get("%suvid" % prefix)
    data_key = player.get("%skey" % prefix)
    data_token = player.get("%stoken" % prefix)
    data_expiry = player.get("%sexpiry" % prefix)
    urlquick.get(SSMP_API % (data_id, data_env), headers=GENERIC_HEADERS, max_age=-1).json()

    headers = {
        "User-Agent": get_random_ua(),
        "Uvid": data_uvid,
        "Token": data_token,
        "Token-Expiry": data_expiry,
        "referrer": URL_ROOT,
    }

    json_api = urlquick.get(STREAM_API % (resource, data_uvid, data_key), headers=headers, max_age=-1).json()
    stream_url = json_api["response"]["stream"]
    stream_url = re.sub(r'\.m3u8.*', '.m3u8', stream_url)

    return resolver_proxy.get_stream_with_quality(plugin, video_url=stream_url)
