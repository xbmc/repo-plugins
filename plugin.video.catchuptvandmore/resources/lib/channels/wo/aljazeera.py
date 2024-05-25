# -*- coding: utf-8 -*-
# Copyright: (c) 2023, darodi
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals

import re

import xbmcgui
# noinspection PyUnresolvedReferences
from codequick import Listitem, Resolver, Route, Script
# noinspection PyUnresolvedReferences
from codequick.utils import urljoin_partial, bold
import urlquick

from resources.lib import resolver_proxy

POLICY_KEY = "BCpkADawqM2WV_cMXnGg7cQ_h8ZF7RlC8EyY4uVca2LT3ze4PrU4MCCuj3F7TA2rOsSXAXgLDcWKavBi2M5_R7HRDOAnsQ1OX4yzxA00cLv37ggu76kll4P_eX4"

SITE_EN = urljoin_partial("https://www.aljazeera.com")
SITE_AR = urljoin_partial("https://www.aljazeera.net")

# "embedUrl": "https://www.youtube.com/embed/G0km6msYigw"
PATTERN_VIDEO_YOUTUBE = re.compile(r'\"https?://.*?youtube\.com/embed/(.*?)\"')

# "embedUrl": "https://players.brightcove.net/665001584001/nUW9Zv8wm_default/index.html?videoId=6318458146112"
PATTERN_VIDEO_BRIGHTCOVE = re.compile(r'\"https?://.*?brightcove\.net/(.*?)/(.*?)/index.html\?videoId=(.*?)\"')


@Route.register
def list_programs(plugin, item_id, **kwargs):
    for i in yield_from_site(site=SITE_EN, videos_path='/videos/'):
        yield i

    # TODO all shows on english site

    for i in yield_from_site(site=SITE_AR, videos_path="/video"):
        yield i


def yield_from_site(site, videos_path):
    resp = urlquick.get(site(videos_path))
    featured_news = resp.parse("main", attrs={"id": "featured-news-container"})
    item = Listitem()
    item.label = bold(featured_news.findtext(".//h2"))
    items = []
    for article in featured_news.iterfind(".//li/article"):
        article_item = Listitem()
        article_item.label = article.findtext('.//h3/a/span')
        url = site(article.find(".//h3/a").get("href"))
        article_item.info['plot'] = article.findtext(".//p")
        article_item.art["thumb"] = site(article.find('.//img').get("src"))
        article_item.set_callback(play_video, url=url)
        items.append(article_item)
    if len(items) > 0:
        item.set_callback(list_items, items=items)
        yield item
    news = resp.parse("section", attrs={"id": "news-feed-container"})

    if site == SITE_EN:
        for section in news.iterfind("./section"):
            item = Listitem()
            item.label = bold(section.findtext(".//h3"))
            items = []
            for slide in section.iterfind(".//div[@aria-roledescription='slide']"):
                slide_item = Listitem()
                slide_item.label = slide.findtext('.//h4/a/span')
                url = site(slide.find(".//h4/a").get("href"))
                slide_item.info['plot'] = slide.findtext(".//p")
                slide_item.art["thumb"] = site(slide.find('.//img').get("src"))
                slide_item.set_callback(play_video, url=url)
                items.append(slide_item)
            if len(items) > 0:
                item.set_callback(list_items, items=items)
                yield item

    if site == SITE_AR:
        item = Listitem()
        item.label = bold(news.findtext(".//h2"))
        items = []
        for article in news.iterfind(".//article"):
            slide_item = Listitem()
            slide_item.label = article.findtext('.//h3/a/span')
            url = site(article.find(".//h3/a").get("href"))
            slide_item.info['plot'] = article.findtext(".//p")
            slide_item.art["thumb"] = site(article.find('.//img').get("src"))
            slide_item.set_callback(play_video, url=url)
            items.append(slide_item)
        if len(items) > 0:
            item.set_callback(list_items, items=items)
            yield item


@Route.register
def list_items(plugin, items):
    for item in items:
        yield item


@Resolver.register
def play_video(plugin, url):
    resp = urlquick.get(url)

    youtube_id = PATTERN_VIDEO_YOUTUBE.findall(resp.text)
    if len(youtube_id) > 0:
        video_url = youtube_id[0]
        return resolver_proxy.get_stream_youtube(plugin, video_url, False)

    brightcove = PATTERN_VIDEO_BRIGHTCOVE.findall(resp.text)
    if len(brightcove) > 0:
        account = brightcove[0][0]
        data_video_id = brightcove[0][2]
        return resolver_proxy.get_brightcove_video_json(plugin, account, None, data_video_id,
                                                        policy_key=POLICY_KEY,
                                                        download_mode=False, subtitles=None)
    return False


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    # label, function_name, video_id
    channels = [
        ('English', 'get_stream_youtube', 'GEumHK0hfdo'),
        ('الوثائقية', 'get_stream_youtube', 'TiPYdMXt_XI'),
        ('قناة مباشر', 'get_stream_youtube', 'eksOMqVMINo'),
        ('البث الحي', 'get_brightcove_video_json', '')
    ]

    selected_item = xbmcgui.Dialog().select(Script.localize(30174), list(map(lambda x: x[0], channels)))
    if selected_item == -1:
        return False

    selected_item = channels[selected_item]
    function_name = selected_item[1]
    if function_name == 'get_stream_youtube':
        return resolver_proxy.get_stream_youtube(plugin, selected_item[2], False)

    return resolver_proxy.get_brightcove_video_json(plugin, "665001584001", None, "5146642090001",
                                                    policy_key=POLICY_KEY,
                                                    download_mode=False, subtitles=None)
