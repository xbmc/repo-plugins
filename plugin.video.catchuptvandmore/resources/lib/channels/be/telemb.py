# -*- coding: utf-8 -*-
# Copyright: (c) 2017, SylvainCecchetto, 2024, darodi
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals

import json
import re
from builtins import str

import urlquick
# noinspection PyUnresolvedReferences
from codequick import Listitem, Resolver, Route

from resources.lib import download, resolver_proxy, web_utils
from resources.lib.menu_utils import item_post_treatment

# TO DO
# Fix Download Mode

URL_ROOT = 'https://www.telemb.be'

URL_LIVE = URL_ROOT + '/direct'

LIVE_PLAYER = 'https://tvlocales-player.freecaster.com/embed/%s.json'

PATTERN_M3U8 = re.compile(r'file\":\"(.*?)\"')

# example "live_token": "95d2f6c9-e85f-4388-8e9c-5962aaaa206f",
PATTERN_LIVE_TOKEN = re.compile(r'\"live_token\":\s*\"(.*?)\",')


@Route.register
def list_programs(plugin, item_id, **kwargs):
    resp = urlquick.get(URL_ROOT)
    root = resp.parse()
    root2 = root.findall(".//li[@class='we-mega-menu-li dropdown-menu']")[3]

    for program_datas in root2.iterfind(".//li[@class='we-mega-menu-li']"):
        program_title = program_datas.find('.//a').text.strip()
        program_url = URL_ROOT + program_datas.find('.//a').get('href')

        item = Listitem()
        item.label = program_title
        item.set_callback(list_videos,
                          item_id=item_id,
                          program_url=program_url,
                          page='0')
        item_post_treatment(item)
        yield item


@Route.register
def list_videos(plugin, item_id, program_url, page, **kwargs):
    resp = urlquick.get(program_url + '?page=%s' % page)
    root = resp.parse()
    root2 = root.findall(".//div[@class='view-content']")[1]

    for video_datas in root2.iterfind(".//div[@class='views-row']"):
        video_title = video_datas.find('.//a').text
        video_image = URL_ROOT + video_datas.find('.//img').get('src')
        video_url = URL_ROOT + video_datas.find('.//a').get('href')

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = item.art['landscape'] = video_image

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
                  item_id,
                  video_url,
                  download_mode=False,
                  **kwargs):
    resp = urlquick.get(video_url, max_age=-1)
    root = resp.parse()
    video_id_url = root.findall('.//iframe')[1].get('src')

    resp2 = urlquick.get(video_id_url, max_age=-1)
    final_video_url = 'https://tvl-vod.l3.freecaster.net' + re.compile(
        r'freecaster\.net(.*?)\"').findall(resp2.text)[0] + '/master.m3u8'
    if download_mode:
        return download.download_video(final_video_url)
    return final_video_url


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    headers = {
        "User-Agent": web_utils.get_random_ua(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "referrer": "https://www.telemb.be/",
    }
    resp = urlquick.get(URL_LIVE, headers=headers, max_age=-1)
    live_tokens = PATTERN_LIVE_TOKEN.findall(resp.text)
    if len(live_tokens) == 0:
        return False
    resp2 = urlquick.get(LIVE_PLAYER % live_tokens[0], max_age=-1)
    video_url = json.loads(resp2.text)['video']['src'][0]['src']

    return resolver_proxy.get_stream_with_quality(plugin, video_url, manifest_type="hls")
