# -*- coding: utf-8 -*-
# Copyright: (c) 2017, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals

import json
import re

import urlquick
from codequick import Listitem, Resolver, Route

from resources.lib import resolver_proxy
from resources.lib.menu_utils import item_post_treatment

URL_ROOT = 'https://www.robtv.be'

URL_LIVE = 'https://live.zendzend.com/cmaf/29375_395477/master.m3u8?HLS_version=ts'


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    return resolver_proxy.get_stream_with_quality(plugin, URL_LIVE, manifest_type="hls")


@Route.register
def list_programs(plugin, item_id, **kwargs):
    # Show news (this is missing in the programs list)
    program_title = 'Nieuws'
    item = Listitem()
    item.label = program_title
    item.set_callback(list_videos,
                      item_id=item_id,
                      program_url='/nieuws',
                      page='1')
    item_post_treatment(item)
    yield item

    # Load programs
    resp = urlquick.get(URL_ROOT + '/programmas')
    root = resp.parse()

    for program_datas in root.iterfind(".//article"):
        program_title = program_datas.find('.//a').get('title')
        program_url = program_datas.find('.//a').get('href')

        if program_datas.find('.//img') is not None:
            program_image = program_datas.find('.//img').get('src')
        else:
            program_image = program_datas.find('.//div[@class="height300"]').get('style').split('(')[1].strip('( )')

        item = Listitem()
        item.label = program_title
        if program_image:
            item.art['thumb'] = item.art['landscape'] = program_image
        item.set_callback(list_videos,
                          item_id=item_id,
                          program_url=program_url,
                          page='1')
        item_post_treatment(item)
        yield item


@Route.register(autosort=False, content_type="videos")
def list_videos(plugin, item_id, program_url, page, **kwargs):
    if page == '1':
        resp = urlquick.get(URL_ROOT + program_url, max_age=-1)
    else:
        resp = urlquick.get(URL_ROOT + program_url, max_age=-1, params={
            'pagina': page,
        })
    root = resp.parse()

    for video_datas in root.iterfind(".//article"):

        # Skip articles that are not a real article
        if video_datas.get('role') != 'article':
            continue

        video_title = video_datas.find('.//a').get('title')
        video_description = video_datas.find('.//div[@class="desc"]/div[@class="ellipsis"]').text
        video_url = video_datas.find('.//a').get('href')
        video_image = video_datas.find('.//img').get('src')
        publication_date = video_datas.find('.//span[@class="date"]').text.strip()

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = item.art['landscape'] = video_image
        item.info['plot'] = video_description
        item.info.date(publication_date, "%d/%m/%Y")
        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_url=video_url)
        item_post_treatment(item, is_playable=True)
        yield item

    if root.find('.//div[@id="infiniteNav"]/div[@class="next"]') is not None or root.find('.//div[@id="infiniteNav"]/a[@class="next"]') is not None:
        yield Listitem.next_page(
            item_id=item_id, program_url=program_url, page=str(int(page) + 1))


@Resolver.register
def get_video_url(plugin, item_id, video_url, **kwargs):
    # Extract video_id
    resp = urlquick.get(URL_ROOT + video_url)
    video_id = re.compile(r'videoId: "(.*?)"').search(resp.text)
    if not video_id:
        plugin.notify('ERROR', plugin.localize(30718))
        return False

    # Download stream info
    resp = urlquick.get('https://content.tmgvideo.nl/playlist/item=%s/playlist.json' % video_id.group(1))
    json_parser = json.loads(resp.text)

    sources = json_parser['items'][0]['locations']['progressive']

    # Sort descending so the best source is selected
    best_source = sorted(sources, key=lambda x: x['width'], reverse=True)[0]

    return best_source['sources'][0]['src']
