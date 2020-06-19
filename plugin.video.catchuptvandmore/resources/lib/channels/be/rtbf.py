# -*- coding: utf-8 -*-
"""
    Catch-up TV & More
    Copyright (C) 2017  SylvainCecchetto

    This file is part of Catch-up TV & More.

    Catch-up TV & More is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    Catch-up TV & More is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along
    with Catch-up TV & More; if not, write to the Free Software Foundation,
    Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""

# The unicode_literals import only has
# an effect on Python 2.
# It makes string literals as unicode like in Python 3
from __future__ import unicode_literals

from codequick import Route, Resolver, Listitem, utils, Script


from resources.lib import web_utils
from resources.lib import resolver_proxy
from resources.lib import download
from resources.lib.menu_utils import item_post_treatment

import htmlement
import re
import json
import time
import urlquick

# TO DO
# Add geoblock (info in JSON)
# Add Quality Mode

URL_EMISSIONS_AUVIO = 'https://www.rtbf.be/auvio/emissions'

URL_JSON_EMISSION_BY_ID = 'https://www.rtbf.be/api/media/video?' \
                          'method=getVideoListByEmissionOrdered&args[]=%s'
# emission_id

URL_CATEGORIES = 'https://www.rtbf.be/news/api/menu?site=media'

URL_SUB_CATEGORIES = 'https://www.rtbf.be/news/api/block?data[0][uuid]=%s&data[0][type]=widget&data[0][settings][id]=%s'
# data-uuid and part of data-uuid

URL_VIDEO_BY_ID = 'https://www.rtbf.be/auvio/embed/media?id=%s&autoplay=1'
# Video Id

URL_ROOT_IMAGE_RTBF = 'https://ds1.static.rtbf.be'

URL_JSON_LIVE = 'https://www.rtbf.be/api/partner/generic/live/' \
                'planninglist?target_site=media&origin_site=media&category_id=0&' \
                'start_date=&offset=0&limit=15&partner_key=%s&v=8'

URL_JSON_LIVE_CHANNEL = 'http://www.rtbf.be/api/partner/generic/live/' \
                        'planningcurrent?v=8&channel=%s&target_site=mediaz&partner_key=%s'

# partener_key

URL_ROOT_LIVE = 'https://www.rtbf.be/auvio/direct#/'


def get_partener_key():
    # Get partener key
    resp = urlquick.get(URL_ROOT_LIVE)
    list_js_files = re.compile(
        r'<script type="text\/javascript" src="(.*?)">').findall(resp.text)

    # Brute force :)
    partener_key_value = ''
    for js_file in list_js_files:
        resp2 = urlquick.get(js_file)
        partener_key_datas = re.compile('partner_key: \'(.+?)\'').findall(
            resp2.text)
        if len(partener_key_datas) > 0:
            partener_key_value = partener_key_datas[0]
            break
    # print 'partener_key_value : ' + partener_key_value
    return partener_key_value


def format_hours(date, **kwargs):
    """Format hours"""
    date_list = date.split('T')
    date_hour = date_list[1][:5]
    return date_hour


def format_day(date, **kwargs):
    """Format day"""
    date_list = date.split('T')
    date_dmy = date_list[0].replace('-', '/')
    return date_dmy


def replay_entry(plugin, item_id, **kwargs):
    """
    First executed function after replay_bridge
    """
    return list_categories(plugin, item_id)


@Route.register
def list_categories(plugin, item_id, **kwargs):

    item = Listitem()
    item.label = plugin.localize(30717)
    item.set_callback(list_programs, item_id=item_id)
    item_post_treatment(item)
    yield item

    resp = urlquick.get(URL_CATEGORIES)
    json_parser = json.loads(resp.text)

    for item_datas in json_parser["item"]:
        if item_datas["@attributes"]["id"] == 'category':
            for category_datas in item_datas["item"]:
                if 'category-' in category_datas["@attributes"]["id"]:
                    category_title = category_datas["@attributes"]["name"]
                    category_url = category_datas["@attributes"]["url"]

                    item = Listitem()
                    item.label = category_title
                    item.set_callback(list_sub_categories,
                                      item_id=item_id,
                                      category_url=category_url)
                    item_post_treatment(item)
                    yield item


@Route.register
def list_programs(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_EMISSIONS_AUVIO)
    root = resp.parse()

    for program_datas in root.iterfind(
            ".//article[@class='rtbf-media-item rtbf-media-item--program-wide col-xxs-12 col-xs-6 col-md-4 col-lg-3 ']"
    ):
        program_title = program_datas.find('.//a').get('title')
        program_image = ''
        list_program_image_datas = program_datas.find('.//img').get(
            'data-srcset').split(' ')
        for program_image_data in list_program_image_datas:
            if 'jpg' in program_image_data:
                if ',' in program_image_data:
                    program_image = program_image_data.split(',')[1]
                else:
                    program_image = program_image_data
        program_id = program_datas.get('data-id')

        item = Listitem()
        item.label = program_title

        item.art['thumb'] = item.art['landscape'] = program_image
        item.set_callback(list_videos_program,
                          item_id=item_id,
                          program_id=program_id)
        item_post_treatment(item)
        yield item


@Route.register
def list_videos_program(plugin, item_id, program_id, **kwargs):

    resp = urlquick.get(URL_JSON_EMISSION_BY_ID % program_id)
    json_parser = json.loads(resp.text)

    for video_datas in json_parser['data']:

        if video_datas["subtitle"]:
            video_title = video_datas["title"] + ' - ' + video_datas["subtitle"]
        else:
            video_title = video_datas["title"]
        video_image = URL_ROOT_IMAGE_RTBF + video_datas["thumbnail"][
            "full_medium"]
        video_plot = ''
        if video_datas["description"]:
            video_plot = video_datas["description"]
        video_duration = video_datas["durations"]
        date_value = time.strftime('%d-%m-%Y',
                                   time.localtime(video_datas["liveFrom"]))
        video_id = video_datas["id"]

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = item.art['landscape'] = video_image
        item.info['plot'] = video_plot
        item.info['duration'] = video_duration
        item.info.date(date_value, '%d-%m-%Y')

        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_id=video_id)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item


@Route.register
def list_sub_categories(plugin, item_id, category_url, **kwargs):

    resp = urlquick.get(category_url)
    root = resp.parse()

    for sub_category_datas in root.iterfind(
            ".//section[@class='js-item-container']"):

        if sub_category_datas.find('.//h2').text is not None:
            sub_category_title = sub_category_datas.find('.//h2').text.strip()
        else:
            sub_category_title = sub_category_datas.find(
                './/h2/a').text.strip()
        sub_category_id = sub_category_datas.get('id')

        item = Listitem()
        item.label = sub_category_title
        item.set_callback(list_videos_sub_category,
                          item_id=item_id,
                          category_url=category_url,
                          sub_category_id=sub_category_id)
        item_post_treatment(item)
        yield item

    list_data_uuid = re.compile(r'data-uuid\=\"(.*?)\"').findall(resp.text)
    for sub_category_data_uuid in list_data_uuid:
        resp2 = urlquick.get(
            URL_SUB_CATEGORIES %
            (sub_category_data_uuid, sub_category_data_uuid.split('-')[1]))
        json_parser = json.loads(resp2.text)
        if sub_category_data_uuid in json_parser["blocks"]:

            parser = htmlement.HTMLement()
            parser.feed(json_parser["blocks"][sub_category_data_uuid])
            root_2 = parser.close()

            for sub_category_dl_data in root_2.iterfind(
                    ".//section[@class='js-item-container']"):

                if sub_category_dl_data.find('.//h2').text is not None:
                    sub_category_dl_title = sub_category_dl_data.find(
                        './/h2').text.strip()
                else:
                    sub_category_dl_title = sub_category_dl_data.find(
                        './/h2/a').text.strip()
                sub_category_dl_id = sub_category_dl_data.get('id')

                item = Listitem()
                item.label = sub_category_dl_title
                item.set_callback(
                    list_videos_sub_category_dl,
                    item_id=item_id,
                    sub_category_data_uuid=sub_category_data_uuid,
                    sub_category_id=sub_category_dl_id)
                item_post_treatment(item)
                yield item


@Route.register
def list_videos_sub_category(plugin, item_id, category_url, sub_category_id,
                             **kwargs):

    resp = urlquick.get(category_url)
    root = resp.parse()

    for sub_category_datas in root.iterfind(
            ".//section[@class='js-item-container']"):
        if sub_category_datas.get('id') == sub_category_id:
            list_videos_datas = sub_category_datas.findall('.//article')

            for video_datas in list_videos_datas:

                if video_datas.get('data-card') is not None:
                    json_parser = json.loads(video_datas.get('data-card'))
                    if json_parser["isVideo"]:
                        if "mediaId" in json_parser:
                            video_title = json_parser["title"] + ' - ' + json_parser["subtitle"]
                            video_image = json_parser["illustration"]["format1248"]
                            video_id = json_parser["mediaId"]

                            item = Listitem()
                            item.label = video_title
                            item.art['thumb'] = item.art['landscape'] = video_image

                            item.set_callback(get_video_url,
                                              item_id=item_id,
                                              video_id=video_id)
                            item_post_treatment(item,
                                                is_playable=True,
                                                is_downloadable=True)
                            yield item


@Route.register
def list_videos_sub_category_dl(plugin, item_id, sub_category_data_uuid,
                                sub_category_id, **kwargs):

    resp = urlquick.get(
        URL_SUB_CATEGORIES %
        (sub_category_data_uuid, sub_category_data_uuid.split('-')[1]))
    json_parser = json.loads(resp.text)

    parser = htmlement.HTMLement()
    parser.feed(json_parser["blocks"][sub_category_data_uuid])
    root = parser.close()

    for sub_category_dl_datas in root.iterfind(
            ".//section[@class='js-item-container']"):
        if sub_category_dl_datas.get('id') == sub_category_id:
            list_videos_datas = sub_category_dl_datas.findall('.//article')

            for video_datas in list_videos_datas:
                if video_datas.get('data-card') is not None:
                    data_card = video_datas.get('data-card')
                    if data_card:
                        json_parser = json.loads(data_card)
                        if json_parser["isVideo"]:
                            if "mediaId" in json_parser:
                                video_title = json_parser["title"] + ' - ' + json_parser["subtitle"]
                                video_image = json_parser["illustration"]["format1248"]
                                video_id = json_parser["mediaId"]

                                item = Listitem()
                                item.label = video_title
                                item.art['thumb'] = item.art['landscape'] = video_image

                                item.set_callback(get_video_url,
                                                  item_id=item_id,
                                                  video_id=video_id)
                                item_post_treatment(item,
                                                    is_playable=True,
                                                    is_downloadable=True)
                                yield item


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_id,
                  download_mode=False,
                  **kwargs):

    resp = urlquick.get(URL_VIDEO_BY_ID % video_id, max_age=-1)
    json_parser = json.loads(
        re.compile('data-media=\"(.*?)\"').findall(resp.text)[0].replace(
            '&quot;', '"'))

    if json_parser["urlHls"] is None:
        if 'youtube.com' in json_parser["url"]:
            video_id = json_parser["url"].rsplit('/', 1)[1]
            return resolver_proxy.get_stream_youtube(plugin, video_id,
                                                     download_mode)
        else:
            return json_parser["url"]
    else:
        stream_url = json_parser["urlHls"]
        if 'drm' in stream_url:
            stream_url = json_parser["urlHlsAes128"]

    if download_mode:
        return download.download_video(stream_url)
    return stream_url


def multi_live_entry(plugin, item_id, **kwargs):
    """
    First executed function after replay_bridge
    """
    return list_lives(plugin, item_id)


def live_entry(plugin, item_id, **kwargs):
    """
    First executed function after live_bridge
    """
    return set_live_url(plugin, item_id, item_id.upper())


@Resolver.register
def set_live_url(plugin, item_id, video_id, **kwargs):

    resp = urlquick.get(URL_JSON_LIVE_CHANNEL % (item_id, get_partener_key()), max_age=-1)
    json_parser = json.loads(resp.text)

    if "url_streaming" in json_parser:
        live_url = json_parser["url_streaming"]["url_hls"]
    live_channel_title = json_parser["channel"]["label"]
    # start_time_value = format_hours(json_parser["start_date"])
    # end_time_value = format_hours(json_parser["end_date"])
    # date_value = format_day(json_parser["start_date"])
    live_title = live_channel_title + " - " + json_parser["title"]
    if json_parser['subtitle']:
        live_title += " - " + json_parser['subtitle']
    live_plot = json_parser["description"]
    live_image = json_parser["images"]["illustration"]["16x9"]["1248x702"]

    item = Listitem()
    item.label = live_title
    item.art['thumb'] = item.art['landscape'] = live_image
    item.info['plot'] = live_plot
    item.set_callback(get_live_url, item_id=item_id, live_url=live_url)
    item_post_treatment(item, is_playable=True)
    yield item


@Route.register
def list_lives(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_JSON_LIVE % (get_partener_key()), max_age=-1)
    json_parser = json.loads(resp.text)

    for live_datas in json_parser:

        if "url_streaming" in live_datas:
            # check if we can add prochainnement if stream is not present
            live_url = live_datas["url_streaming"]["url_hls"]

        if type(live_datas["channel"]) is dict:
            live_channel_title = live_datas["channel"]["label"]
        else:
            live_channel_title = 'Exclu Auvio'
        if live_channel_title in ['La Une', 'La Deux', 'La Trois']:
            continue
        start_time_value = format_hours(live_datas["start_date"])
        end_time_value = format_hours(live_datas["end_date"])
        date_value = format_day(live_datas["start_date"])
        live_title = live_channel_title + " - " + live_datas["title"]
        if live_datas['subtitle']:
            live_title += " - " + live_datas['subtitle']
        live_plot = 'Début le %s à %s (CET)' % (date_value, start_time_value) + \
            '\n\r' + 'Fin le %s à %s (CET)' % (date_value, end_time_value) + '\n\r' + \
            'Accessibilité: ' + live_datas["geolock"]["title"] + '\n\r' + \
            live_datas["description"]
        live_image = live_datas["images"]["illustration"]["16x9"]["1248x702"]

        item = Listitem()
        item.label = live_title
        item.art['thumb'] = item.art['landscape'] = live_image
        item.info['plot'] = live_plot
        # commented this line because othrewie sorting is made by date and then by title
        # and doesn't help to find the direct
        # item.info.date(date_time_value, '%Y/%m/%d')
        item.set_callback(get_live_url, item_id=item_id, live_url=live_url)
        item_post_treatment(item, is_playable=True)
        yield item


@Resolver.register
def get_live_url(plugin, item_id, live_url, **kwargs):

    if 'drm' in live_url:
        return live_url.replace('_drm.m3u8', '_aes.m3u8')
    return live_url
