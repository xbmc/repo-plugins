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

from resources.lib.labels import LABELS
from resources.lib import web_utils
from resources.lib import resolver_proxy
from resources.lib import download

from bs4 import BeautifulSoup as bs

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
# partener_key

URL_ROOT_LIVE = 'https://www.rtbf.be/auvio/direct#/'


def get_partener_key():
    # Get partener key
    resp = urlquick.get(URL_ROOT_LIVE)
    list_js_files = re.compile(
         r'<script type="text\/javascript" src="(.*?)">'
         ).findall(resp.text)

    # Brute force :)
    partener_key_value = ''
    for js_file in list_js_files:
        resp2 = urlquick.get(js_file)
        partener_key_datas = re.compile(
            'partner_key: \'(.+?)\'').findall(resp2.text)
        if len(partener_key_datas) > 0:
            partener_key_value = partener_key_datas[0]
            break
    print 'partener_key_value : ' + partener_key_value
    return partener_key_value


def format_hours(date):
    """Format hours"""
    date_list = date.split('T')
    date_hour = date_list[1][:5]
    return date_hour


def format_day(date):
    """Format day"""
    date_list = date.split('T')
    date_dmy = date_list[0].replace('-', '/')
    return date_dmy


def replay_entry(plugin, item_id):
    """
    First executed function after replay_bridge
    """
    return list_categories(plugin, item_id)


@Route.register
def list_categories(plugin, item_id):

    item = Listitem()
    item.label = plugin.localize(LABELS['All programs'])
    item.set_callback(
        list_programs,
        item_id=item_id)
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
                    item.set_callback(
                        list_sub_categories,
                        item_id=item_id,
                        category_url=category_url)
                    yield item


@Route.register
def list_programs(plugin, item_id):

    resp = urlquick.get(URL_EMISSIONS_AUVIO)
    root_soup = bs(resp.text, 'html.parser')
    list_programs_datas = root_soup.find_all(
        'article', class_="rtbf-media-item col-xxs-12 col-xs-6 col-md-4 col-lg-3 ")

    for program_datas in list_programs_datas:
        program_title = program_datas.find('h4').text
        program_image = ''
        list_program_image_datas = program_datas.find('img').get('data-srcset').split(' ')
        for program_image_data in list_program_image_datas:
            if 'jpg' in program_image_data:
                if ',' in program_image_data:
                    program_image = program_image_data.split(',')[1]
                else:
                    program_image = program_image_data
        program_id = program_datas.get('data-id')

        item = Listitem()
        item.label = program_title
        item.art['thumb'] = program_image
        item.set_callback(
            list_videos_program,
            item_id=item_id,
            program_id=program_id)
        yield item


@Route.register
def list_videos_program(plugin, item_id, program_id):

    resp = urlquick.get(URL_JSON_EMISSION_BY_ID % program_id)
    json_parser = json.loads(resp.text)

    for video_datas in json_parser['data']:

        if video_datas["subtitle"]:
            video_title = video_datas["title"] + ' - ' + video_datas["subtitle"]
        else:
            video_title = video_datas["title"]
        video_image = URL_ROOT_IMAGE_RTBF + video_datas["thumbnail"]["full_medium"]
        video_plot = ''
        if video_datas["description"]:
            video_plot = video_datas["description"]
        video_duration = video_datas["durations"]
        date_value = time.strftime(
            '%d-%m-%Y', time.localtime(video_datas["liveFrom"]))
        video_id = video_datas["id"]

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = video_image
        item.info['plot'] = video_plot
        item.info['duration'] = video_duration
        item.info.date(date_value, '%d-%m-%Y')

        item.context.script(
            get_video_url,
            plugin.localize(LABELS['Download']),
            item_id=item_id,
            video_id=video_id,
            video_label=LABELS[item_id] + ' - ' + item.label,
            download_mode=True)

        item.set_callback(
            get_video_url,
            item_id=item_id,
            video_id=video_id)
        yield item


@Route.register
def list_sub_categories(plugin, item_id, category_url):

    resp = urlquick.get(category_url)
    root_soup = bs(resp.text, 'html.parser')
    list_sub_categories_datas = root_soup.find_all(
        'section', class_="js-item-container")

    for sub_category_datas in list_sub_categories_datas:

        sub_category_title = " ".join(sub_category_datas.find('h2').text.split())
        sub_category_id = sub_category_datas.get('id')

        item = Listitem()
        item.label = sub_category_title
        item.set_callback(
            list_videos_sub_category,
            item_id=item_id,
            category_url=category_url,
            sub_category_id=sub_category_id)
        yield item

    list_sub_categories_to_dl = root_soup.find_all(
        'div', class_=re.compile("js-widget js-widget-"))

    for sub_category_to_dl in list_sub_categories_to_dl:
        sub_category_data_uuid = sub_category_to_dl.find('b').get('data-uuid')
        resp2 = urlquick.get(
            URL_SUB_CATEGORIES % (sub_category_data_uuid, sub_category_data_uuid.split('-')[1]))
        json_parser = json.loads(resp2.text)
        if sub_category_data_uuid in json_parser["blocks"]:
            sub_category_dl_value = json_parser["blocks"][sub_category_data_uuid]
            sub_category_dl_soup = bs(sub_category_dl_value, 'html.parser')
            list_sub_category_dl_datas = sub_category_dl_soup.find_all(
                'section', class_="js-item-container")

            for sub_category_dl_data in list_sub_category_dl_datas:

                sub_category_dl_title = " ".join(sub_category_dl_data.find('h2').text.split())
                sub_category_dl_id = sub_category_dl_data.get('id')

                item = Listitem()
                item.label = sub_category_dl_title
                item.set_callback(
                    list_videos_sub_category_dl,
                    item_id=item_id,
                    sub_category_data_uuid=sub_category_data_uuid,
                    sub_category_id=sub_category_dl_id)
                yield item


@Route.register
def list_videos_sub_category(plugin, item_id, category_url, sub_category_id):

    resp = urlquick.get(category_url)
    root_soup = bs(resp.text, 'html.parser')
    list_sub_categories_datas = root_soup.find_all(
        'section', class_="js-item-container")

    for sub_category_datas in list_sub_categories_datas:
        if sub_category_datas.get('id') == sub_category_id:
            list_videos_datas = sub_category_datas.find_all('article')

            for video_datas in list_videos_datas:

                if video_datas.get('data-type') == 'media':
                    if video_datas.find('h4'):
                        video_title = video_datas.find('h3').find(
                            'a').get('title') + ' - ' + \
                            video_datas.find('h4').text
                    else:
                        video_title = video_datas.find('h3').find('a').get('title')
                    video_image = ''
                    image_datas = video_datas.find('img').get(
                        'data-srcset').split(',')
                    for image_data in image_datas:
                        video_image = image_data.split(' ')[0]
                    video_id = video_datas.get('data-id')

                    item = Listitem()
                    item.label = video_title
                    item.art['thumb'] = video_image

                    item.context.script(
                        get_video_url,
                        plugin.localize(LABELS['Download']),
                        item_id=item_id,
                        video_id=video_id,
                        video_label=LABELS[item_id] + ' - ' + item.label,
                        download_mode=True)

                    item.set_callback(
                        get_video_url,
                        item_id=item_id,
                        video_id=video_id)
                    yield item


@Route.register
def list_videos_sub_category_dl(plugin, item_id, sub_category_data_uuid, sub_category_id):

    resp = urlquick.get(URL_SUB_CATEGORIES % (sub_category_data_uuid, sub_category_data_uuid.split('-')[1]))
    json_parser = json.loads(resp.text)

    sub_category_dl_value = json_parser["blocks"][sub_category_data_uuid]
    sub_category_dl_soup = bs(sub_category_dl_value, 'html.parser')
    list_sub_category_dl_datas = sub_category_dl_soup.find_all(
        'section', class_="js-item-container")

    for sub_category_dl_datas in list_sub_category_dl_datas:
        if sub_category_dl_datas.get('id') == sub_category_id:
            list_videos_datas = sub_category_dl_datas.find_all('article')

            for video_datas in list_videos_datas:

                if video_datas.get('data-type') == 'media':
                    if video_datas.find('h4'):
                        video_title = video_datas.find('h3').find(
                            'a').get('title') + ' - ' + \
                            video_datas.find('h4').text
                    else:
                        video_title = video_datas.find('h3').find('a').get('title')
                    video_image = ''
                    image_datas = video_datas.find('img').get(
                        'data-srcset').split(',')
                    for image_data in image_datas:
                        video_image = image_data.split(' ')[0]
                    video_id = video_datas.get('data-id')

                    item = Listitem()
                    item.label = video_title
                    item.art['thumb'] = video_image

                    item.context.script(
                        get_video_url,
                        plugin.localize(LABELS['Download']),
                        item_id=item_id,
                        video_id=video_id,
                        video_label=LABELS[item_id] + ' - ' + item.label,
                        download_mode=True)

                    item.set_callback(
                        get_video_url,
                        item_id=item_id,
                        video_id=video_id)
                    yield item


@Resolver.register
def get_video_url(
        plugin, item_id, video_id, download_mode=False, video_label=None):

    resp = urlquick.get(URL_VIDEO_BY_ID % video_id, max_age=-1)
    json_parser = json.loads(re.compile('data-media=\"(.*?)\"').findall(
        resp.text)[0].replace('&quot;', '"'))

    if json_parser["urlHls"] is None:
        if 'youtube.com' in json_parser["url"]:
            video_id = json_parser["url"].rsplit('/', 1)[1]
            return resolver_proxy.get_stream_youtube(
                plugin, video_id, download_mode, video_label)
        else:
            return json_parser["url"]
    else:
        stream_url = json_parser["urlHls"]
        if 'drm' in stream_url:
            stream_url = json_parser["urlHlsAes128"]

    if download_mode:
        return download.download_video(stream_url, video_label)
    return stream_url


def multi_live_entry(plugin, item_id):
    """
    First executed function after replay_bridge
    """
    return list_lives(plugin, item_id)


@Route.register
def list_lives(plugin, item_id):

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

        start_time_value = format_hours(live_datas["start_date"])
        end_time_value = format_hours(live_datas["end_date"])
        date_value = format_day(live_datas["start_date"])
        live_title = live_channel_title + " - " + live_datas["title"]
        live_plot = 'Début le %s à %s (CET)' % (date_value, start_time_value) + \
            '\n\r' + 'Fin le %s à %s (CET)' % (date_value, end_time_value) + '\n\r' + \
            live_datas["description"]
        live_image = live_datas["images"]["illustration"]["16x9"]["1248x702"]

        item = Listitem()
        item.label = live_title
        item.art['thumb'] = live_image
        item.info['plot'] = live_plot
        item.info.date(date_value, '%Y/%m/%d')
        item.set_callback(
            get_live_url,
            item_id=item_id,
            live_url=live_url)
        yield item


@Resolver.register
def get_live_url(plugin, item_id, live_url):

    if 'drm' in live_url:
        return live_url.replace('_drm.m3u8', '_aes.m3u8')
    return live_url
