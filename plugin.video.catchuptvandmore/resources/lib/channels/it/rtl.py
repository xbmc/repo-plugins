# -*- coding: utf-8 -*-
# Copyright: (c) 2022, darodi
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals

import json
import re

import urlquick
# noinspection PyUnresolvedReferences
from codequick import Listitem, Resolver, Route, Script

from resources.lib import web_utils, resolver_proxy
from resources.lib.addon_utils import get_item_media_path
from resources.lib.menu_utils import item_post_treatment
from resources.lib.web_utils import html_parser

PATTERN_BACKGROUND_IMAGE_URL = re.compile(r'url\(\s*(.*?)\s*\)')

URL_ROOT = "https://play.rtl.it"

DEFAULT_IMAGE = get_item_media_path('channels/it/rtl-1025-radiovisione.png')


@Route.register
def list_lives(plugin, item_id, **kwargs):
    root = urlquick.get(URL_ROOT,
                        headers={'User-Agent': web_utils.get_random_ua()},
                        max_age=-1).parse()
    channels = root.findall(".//div[@data-media-type='SectionItem']")

    if len(channels) == 0:
        return False

    for channel in channels:

        live_image = DEFAULT_IMAGE

        live_url_anchor = channel.find('.//a')
        if live_url_anchor is None:
            continue

        channel_url = URL_ROOT + live_url_anchor.get('href')

        resp = urlquick.get(channel_url).parse()
        json_media_object = None
        buttons = resp.findall(".//div[@class='rtl-play-info-container']//button")
        for button in buttons:
            if button.findtext('.//span') == 'Radiovisione':
                resp2 = urlquick.get(button.get('data-media-url'))
                json_media_object = resp2.json()
                break

        if json_media_object is None:
            continue

        media_info = json_media_object['data']['mediaInfo']
        live_plot = live_title = media_info['title']

        style = resp.find('.//picture/img').get('style')
        img_array = PATTERN_BACKGROUND_IMAGE_URL.findall(style)
        if len(img_array) > 0:
            live_image = img_array[0]

        url = media_info['uri']

        item = Listitem()
        item.label = live_title
        item.art['thumb'] = item.art['landscape'] = live_image
        item.info['plot'] = live_plot
        item.set_callback(get_live_url, url=url)
        item_post_treatment(item, is_playable=True)
        yield item


@Resolver.register
def get_live_url(plugin, url, **kwargs):
    return resolver_proxy.get_stream_with_quality(plugin, video_url=url, manifest_type="hls")
