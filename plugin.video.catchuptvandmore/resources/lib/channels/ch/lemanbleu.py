# -*- coding: utf-8 -*-
# Copyright: (c) 2019, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
from builtins import str
import re

from codequick import Listitem, Resolver, Route, Script
from kodi_six import xbmcgui
import urlquick

from resources.lib import download, resolver_proxy
from resources.lib.addon_utils import Quality
from resources.lib.menu_utils import item_post_treatment


URL_ROOT = 'https://www.lemanbleu.ch'

URL_LIVE_M3U8 = 'https://naxoo.vedge.infomaniak.com/livecast/ik:naxoo/manifest.m3u8'

URL_REPLAY = URL_ROOT + '/fr/Toutes-les-emissions.html'
URL_VIDEOS = URL_ROOT + '/Scripts/Modules/CustomView/List.aspx?idn=9667&name=ReplaySearch&EmissionID=%s&pg=%s'

QUALITIES_STREAM = ['sd', 'md', 'hq', 'hd']


@Route.register
def list_programs(plugin, item_id, **kwargs):
    # TODO: page structure may have changed
    resp = urlquick.get(URL_REPLAY)
    root = resp.parse("ul", attrs={"id": "itemFilters"})

    for program_datas in root.iterfind(".//li"):
        program_title = program_datas.find('.//a').text
        program_id = re.compile(r'this\,(.*?)\)').findall(
            program_datas.find('.//a').get('onclick'))[0]

        item = Listitem()
        item.label = program_title
        item.set_callback(list_videos,
                          item_id=item_id,
                          program_id=program_id,
                          page='1')
        item_post_treatment(item)
        yield item


@Route.register
def list_videos(plugin, item_id, program_id, page, **kwargs):

    resp = urlquick.get(URL_VIDEOS % (program_id, page))
    root = resp.parse()

    for video_datas in root.iterfind(".//li[@class='item']"):
        video_title = video_datas.find('.//h3').text
        video_image = URL_ROOT + video_datas.find('.//img').get('src')
        video_plot = video_datas.find('.//p').text
        video_url = URL_ROOT + video_datas.find('.//a').get('href')
        date_value = video_datas.find(".//span[@class='date']").text.split(
            ' ')[1]

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = item.art['landscape'] = video_image
        item.info['plot'] = video_plot
        item.info.date(date_value, '%d.%m.%Y')

        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_url=video_url)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item

    yield Listitem.next_page(item_id=item_id,
                             program_id=program_id,
                             page=str(int(page) + 1))


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_url,
                  download_mode=False,
                  **kwargs):

    resp = urlquick.get(video_url, max_age=-1)
    stream_url = re.compile(r'og:video" content="(.*?)"').findall(
        resp.text)[0]

    desired_quality = Script.setting.get_string('quality')
    all_datas_videos_quality = []
    all_datas_videos_path = []
    for quality in QUALITIES_STREAM:
        all_datas_videos_quality.append(quality)
        if quality == 'sd':
            all_datas_videos_path.append(
                stream_url.replace('mp4-231', 'mp4-322'))
        elif quality == 'md':
            all_datas_videos_path.append(
                stream_url.replace('mp4-231', 'mp4-323'))
        elif quality == 'hq':
            all_datas_videos_path.append(
                stream_url.replace('mp4-231', 'mp4-12'))
        else:
            all_datas_videos_path.append(stream_url)

    url = ''
    if desired_quality == Quality['DIALOG']:
        selected_item = xbmcgui.Dialog().select(
            plugin.localize(30709),
            all_datas_videos_quality)
        if selected_item == -1:
            return False
        url = all_datas_videos_path[selected_item]
    elif desired_quality == Quality['BEST']:
        url = all_datas_videos_path[-1]
    else:
        url = all_datas_videos_path[0]

    if download_mode:
        return download.download_video(url)
    return url


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    return resolver_proxy.get_stream_with_quality(
        plugin,
        video_url=URL_LIVE_M3U8,
        manifest_type="hls"
    )
