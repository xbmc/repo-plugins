# -*- coding: utf-8 -*-
# Copyright: (c) 2018, SylvainCecchetto
# Copyright: (c) 2022, darodi
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals

import re

import urlquick
# noinspection PyUnresolvedReferences
from codequick import Listitem, Resolver, Route
# noinspection PyUnresolvedReferences
from codequick.utils import urljoin_partial, strip_tags, ensure_native_str

from resources.lib import download, resolver_proxy
from resources.lib.addon_utils import get_item_media_path
from resources.lib.menu_utils import item_post_treatment

URL_ROOT = 'https://www.nrj.be/'
url_constructor = urljoin_partial(URL_ROOT)
URL_VIDEOS = url_constructor('replay/videos')
URL_LIVE = url_constructor('live')

URL_STREAM = 'https://services.brid.tv/services/get/video/%s/%s.json'
PATTERN_NEXT_URL = re.compile(r'\([\'|"](.*?)[\'|"]\)')


@Route.register
def list_categories(plugin, item_id, **kwargs):
    sections = urlquick.get(URL_VIDEOS).parse("main").iterfind(".//section//section")
    for section in sections:
        if section.find(".//h2") is None:
            continue

        item = Listitem()
        item.label = section.findtext(".//h2")
        item.art["thumb"] = get_item_media_path('channels/be/nrjhitstvbe.png')
        item.set_callback(list_videos_in_section, item_id=item_id, section=section)
        yield item


@Route.register
def list_videos_in_section(plugin, item_id, section, **kwargs):
    for i in list_videos(item_id, section):
        yield i

    next_btn = section.find(".//a[@class='btn btn-dark']")
    if next_btn is not None:
        item = Listitem()
        item.label = next_btn.text
        item.art['thumb'] = item.art['landscape'] = get_item_media_path('channels/be/nrjhitstvbe.png')
        next_url = url_constructor(next_btn.get('href'))
        item.set_callback(get_more_videos, item_id=item_id, url=next_url)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item


def list_videos(item_id, section):
    for video_data in section.iterfind(".//a[@class='nrj-card']"):

        video_image = None
        try:
            video_image = video_data.find(".//img").get("src")
        except Exception:
            try:
                video_image_data = video_data.find(".//div[@class='nrj-card__pict']").get('style')
                video_image = re.compile(r'url\((.*?)\)').findall(video_image_data)[0]
            except Exception:
                pass

        video_url = url_constructor(video_data.get('href'))

        item = Listitem()
        try:
            item.label = video_data.findtext(".//div[@class='nrj-card__text']", default='')
        except Exception:
            try:
                item.label = video_data.findtext(".//div[@class='nrj-card__text-small']", default='')
            except Exception:
                continue

        if len(item.label) == 0:
            try:
                item.label = video_data.findtext(".//div[@class='nrj-card__text-small']")
            except Exception:
                continue

        if video_image is not None:
            item.art['thumb'] = item.art['landscape'] = video_image

        item.set_callback(get_video_url, item_id=item_id, video_url=video_url)
        yield item


@Route.register
def get_more_videos(plugin, item_id, url, **kwargs):
    root = urlquick.get(url).parse("main")

    for i in list_videos(item_id, root):
        yield i

    next_btn = root.find(".//nav/ul/li[last()]/button")
    if next_btn is not None:
        on_click = next_btn.get("onclick")
        if on_click is not None:
            found_match = PATTERN_NEXT_URL.search(on_click)
            if found_match is not None:
                next_url = re.sub(r'\?.*', '', url) + found_match.group(1)
                if url != next_url:
                    yield Listitem.next_page(item_id=item_id, url=next_url)


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_url,
                  download_mode=False,
                  **kwargs):
    # Create session
    session_urlquick = urlquick.Session()
    main = session_urlquick.get(video_url, max_age=-1).parse("main")
    player = main.find(".//div[@data-video-id][@data-video-player-id]")
    data_video_id = player.get('data-video-id')
    data_video_player_id = player.get('data-video-player-id')
    json_parser = session_urlquick.get(URL_STREAM % (data_video_player_id, data_video_id), max_age=-1).json()
    source_dict = json_parser["Video"][0]["source"]
    if len(source_dict) == 0:
        return False
    video_quality = ''
    for stream_datas_quality in source_dict:
        video_quality = stream_datas_quality
    video_url2 = source_dict[video_quality]
    if not video_url2.startswith("http"):
        video_url2 = "https:" + video_url2
    if download_mode:
        return download.download_video(video_url2)
    if video_url2.endswith(".m3u8"):

        # SSL certificate error -> verify=False
        return resolver_proxy.get_stream_with_quality(plugin,
                                                      video_url=video_url2,
                                                      manifest_type="hls",
                                                      verify=False)
    return video_url2


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    return get_video_url(plugin,
                         item_id,
                         URL_LIVE,
                         **kwargs)
