# -*- coding: utf-8 -*-
# Copyright: (c) 2017, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals

import json
import re

import urlquick
from codequick import Listitem, Resolver, Route, Script
from resources.lib import resolver_proxy, web_utils
from resources.lib.menu_utils import item_post_treatment

# TO DO
#   Most recent
#   Most viewed
#   Add some videos Arte Concerts

URL_ROOT = 'https://www.arte.tv/%s/'
# Language

URL_TOKEN = 'https://static-cdn.arte.tv/guide/manifest.js'

URL_LIVE_ARTE = 'https://api.arte.tv/api/player/v2/config/%s/LIVE'
# Langue, ...

# URL_VIDEOS = 'http://www.arte.tv/hbbtvv2/services/web/index.php/OPA/v3/videos/subcategory/%s/page/%s/limit/100/%s'
# VideosCode, Page, language

URL_VIDEOS_2 = 'http://www.arte.tv/hbbtvv2/services/web/index.php/OPA/v3/videos/collection/%s/%s/%s'
# VideosCode, Page, language

DESIRED_LANGUAGE = Script.setting['arte.language']

CORRECT_MONTH = {
    'Jan': '01',
    'Feb': '02',
    'Mar': '03',
    'Apr': '04',
    'May': '05',
    'Jun': '06',
    'Jul': '07',
    'Aug': '08',
    'Sep': '09',
    'Oct': '10',
    'Nov': '11',
    'Dec': '12'
}


def extract_json_from_html(url):
    html = urlquick.get(url).text
    json_value = re.compile(r'application/json">(.*?)\}<').findall(html)[0]
    return json.loads(json_value + '}')


@Route.register
def list_categories(plugin, item_id, **kwargs):
    """
    Build categories listing
    - Tous les programmes
    - Séries
    - Informations
    - ...
    """
    url = URL_ROOT % DESIRED_LANGUAGE.lower()
    return list_zone(plugin, item_id, url)


@Route.register
def list_zone(plugin, item_id, url):
    j = extract_json_from_html(url)
    zones = j['props']['pageProps']['initialPage']['zones']
    for zone in zones:
        # Avoid empty folders
        if not zone['data']:
            continue
        # Avoid infinite loop
        if len(zone['data']) == 1 and zone['data'][0]['url'] == url:
            continue

        item = Listitem()
        item.label = zone['title']
        item.info['plot'] = zone['description']

        item.set_callback(list_data,
                          item_id=item_id,
                          url=url,
                          zone_id=zone['id'])
        item_post_treatment(item)
        yield item


@Route.register
def list_data(plugin, item_id, url, zone_id):
    j = extract_json_from_html(url)
    zones = j['props']['pageProps']['initialPage']['zones']
    for zone in zones:
        if zone_id == zone['id']:
            data = zone['data']
            break
    for data in zone['data']:
        title = data['title']
        if 'subtitle' in data and data['subtitle']:
            title += ' - ' + data['subtitle']

        item = Listitem()
        item.label = title
        item.info['plot'] = data.get('shortDescription', None)

        images = data['images']
        thumb = None
        fanart = None
        if 'square' in images:
            try:
                thumb = data['images']['square']['resolutions'][-1]['url']
            except Exception:
                pass
        if 'portrait' in images and thumb is None:
            try:
                thumb = data['images']['portrait']['resolutions'][-1]['url']
            except Exception:
                pass
        try:
            fanart = data['images']['landscape']['resolutions'][-1]['url']
        except Exception:
            pass
        if fanart:
            item.art['fanart'] = item.art['thumb'] = fanart
        if thumb:
            item.art['thumb'] = thumb

        item.info['duration'] = data.get('duration', None)

        try:
            item.info.date(data['availability']['start'].split('T')[0], '%Y-%m-%d')
        except Exception:
            pass

        if data['kind']['code'].lower() in ['shows', 'show']:
            item.set_callback(get_video_url, item_id=item_id, video_id=data['programId'])
            item_post_treatment(
                item,
                is_playable=True,
                is_downloadable=True)
        else:
            # Assume it's a folder
            item.set_callback(list_zone,
                              item_id=item_id,
                              url=data['url'])
            item_post_treatment(item)
        yield item


# @Route.register
# def list_sub_categories(plugin, item_id, category_url, **kwargs):
#     """
#     Build programs listing
#     - Les feux de l'amour
#     - ...
#     """
#     json_parser = extract_json_from_html(category_url)
#     # zones = json_parser['props']['pageProps']['initialPage']['zones']
#     value_code = json_parser['pages']['currentCode']

#     for sub_category_datas in json_parser['pages']['list'][value_code]['zones']:
#         if 'subcategory' in sub_category_datas['code']['name']:
#             sub_category_title = sub_category_datas['title']
#             sub_category_url = sub_category_datas['link']['url']

#             item = Listitem()
#             item.label = sub_category_title
#             item.set_callback(list_videos_sub_category,
#                               item_id=item_id,
#                               sub_category_url=sub_category_url)
#             item_post_treatment(item)
#             yield item

#         elif 'genres' in sub_category_datas['code']['name']:
#             sub_category_title = sub_category_datas['title']
#             sub_category_code_name = sub_category_datas['code']['name']
#             sub_category_url = category_url

#             item = Listitem()
#             item.label = sub_category_title

#             item.set_callback(list_programs_concert,
#                               item_id=item_id,
#                               sub_category_code_name=sub_category_code_name,
#                               sub_category_url=sub_category_url)
#             item_post_treatment(item)
#             yield item

#         elif 'banner' in sub_category_datas['code']['name']:
#             continue

#         elif 'playlists' in sub_category_datas['code']['name'] or \
#                 'collections' in sub_category_datas['code']['name'] or \
#                 'magazines' in sub_category_datas['code']['name'] or \
#                 'ARTE_CONCERT' in sub_category_datas['code']['name'] or \
#                 'highlights_category' in sub_category_datas['code']['name'] or \
#                 '-' in sub_category_datas['code']['name'] or \
#                 'collection_videos' in sub_category_datas['code']['name'] or \
#                 'collection_subcollection' in sub_category_datas['code']['name']:
#             if sub_category_datas['data']:
#                 sub_category_title = sub_category_datas['title']
#                 sub_category_code_name = sub_category_datas['code']['name']
#                 sub_category_url = category_url

#                 item = Listitem()
#                 item.label = sub_category_title

#                 item.set_callback(list_programs,
#                                   item_id=item_id,
#                                   sub_category_title=sub_category_title,
#                                   sub_category_code_name=sub_category_code_name,
#                                   sub_category_url=sub_category_url)
#                 item_post_treatment(item)
#                 yield item

#         # else:
#         #     # Add Notification (Category Not known)
#         #     return None


# @Route.register
# def list_programs(plugin, item_id, sub_category_title, sub_category_code_name, sub_category_url,
#                   **kwargs):
#     """
#     Build programs listing
#     - Les feux de l'amour
#     - ...
#     """

#     if '/api/' in sub_category_url:
#         resp = urlquick.get(sub_category_url.replace('https://api-internal.arte.tv', 'https://www.arte.tv/guide'))
#         json_parser = json.loads(resp.text)
#         # for video_datas in json_parser['data']:
#         for program_datas in json_parser['data']:

#             if program_datas["kind"]["isCollection"]:
#                 program_title = program_datas['title']
#                 program_url = program_datas['url']
#                 program_image = ''
#                 if (program_datas['images']['landscape'] is not None and 'resolutions' in program_datas['images']['landscape']):
#                     for image_datas in program_datas['images']['landscape']['resolutions']:
#                         program_image = image_datas['url']
#                 elif (program_datas['images']['square'] is not None and 'resolutions' in program_datas['images']['square']):
#                     for image_datas in program_datas['images']['square']['resolutions']:
#                         program_image = image_datas['url']

#                 item = Listitem()
#                 item.label = program_title
#                 item.art['thumb'] = item.art['landscape'] = program_image
#                 item.set_callback(
#                     list_sub_categories,
#                     item_id=item_id,
#                     category_url=program_url)
#                 item_post_treatment(item)
#                 yield item

#             if program_datas['programId'] is not None and 'RC-' in program_datas['programId']:
#                 program_title = program_datas['title']
#                 program_id = program_datas['programId']
#                 program_image = ''
#                 if (program_datas['images']['landscape'] is not None and 'resolutions' in program_datas['images']['landscape']):
#                     for image_datas in program_datas['images']['landscape']['resolutions']:
#                         program_image = image_datas['url']
#                 elif (program_datas['images']['square'] is not None and 'resolutions' in program_datas['images']['square']):
#                     for image_datas in program_datas['images']['square']['resolutions']:
#                         program_image = image_datas['url']

#                 item = Listitem()
#                 item.label = program_title
#                 item.art['thumb'] = item.art['landscape'] = program_image
#                 item.set_callback(
#                     list_videos_program,
#                     item_id=item_id,
#                     sub_category_code_name=sub_category_code_name,
#                     program_id=program_id)
#                 item_post_treatment(item)
#                 yield item

#             if program_datas['subtitle']:
#                 video_title = '{title} - {subtitle}'.format(**program_datas)
#             else:
#                 video_title = program_datas['title']
#             video_id = program_datas['programId']
#             video_image = ''
#             if (program_datas['images']['landscape'] is not None and 'resolutions' in program_datas['images']['landscape']):
#                 for video_image_datas in program_datas['images']['landscape']['resolutions']:
#                     video_image = video_image_datas['url']
#             elif (program_datas['images']['square'] is not None and 'resolutions' in program_datas['images']['square']):
#                 for image_datas in program_datas['images']['square']['resolutions']:
#                     program_image = image_datas['url']
#             video_duration = program_datas["duration"]
#             video_plot = program_datas.get("shortDescription", '')

#             item = Listitem()
#             item.label = video_title
#             item.art['thumb'] = item.art['landscape'] = video_image
#             item.info['duration'] = video_duration
#             item.info['plot'] = video_plot

#             item.set_callback(get_video_url,
#                               item_id=item_id,
#                               video_id=video_id)
#             item_post_treatment(item,
#                                 is_playable=True,
#                                 is_downloadable=True)
#             yield item

#         if json_parser['nextPage'] is not None:
#             yield Listitem.next_page(
#                 item_id=item_id,
#                 sub_category_title=sub_category_title,
#                 sub_category_code_name=sub_category_code_name,
#                 sub_category_url=json_parser['nextPage'])
#     else:
#         resp = urlquick.get(sub_category_url)
#         json_value = re.compile(r'_INITIAL_STATE__ \= (.*?)\}\;').findall(resp.text)[0]
#         json_parser = json.loads(json_value + '}')

#         value_code = json_parser['pages']['currentCode']
#         for sub_category_datas in json_parser['pages']['list'][value_code]['zones']:
#             if (sub_category_datas['code']['name'] != sub_category_code_name or
#                     sub_category_title != sub_category_datas['title']):
#                 continue

#             for program_datas in sub_category_datas['data']:
#                 if program_datas["kind"]["isCollection"]:
#                     program_title = program_datas['title']
#                     program_url = program_datas['url']
#                     program_image = ''
#                     if (program_datas['images']['landscape'] is not None and 'resolutions' in program_datas['images']['landscape']):
#                         for image_datas in program_datas['images']['landscape']['resolutions']:
#                             program_image = image_datas['url']
#                     elif (program_datas['images']['square'] is not None and 'resolutions' in program_datas['images']['square']):
#                         for image_datas in program_datas['images']['square']['resolutions']:
#                             program_image = image_datas['url']

#                     item = Listitem()
#                     item.label = program_title
#                     item.art['thumb'] = item.art['landscape'] = program_image
#                     item.set_callback(
#                         list_sub_categories,
#                         item_id=item_id,
#                         category_url=program_url)
#                     item_post_treatment(item)
#                     yield item

#                 if program_datas['programId'] is not None and 'RC-' in program_datas['programId']:
#                     program_title = program_datas['title']
#                     program_id = program_datas['programId']
#                     program_image = ''
#                     if (program_datas['images']['landscape'] is not None and 'resolutions' in program_datas['images']['landscape']):
#                         for image_datas in program_datas['images']['landscape']['resolutions']:
#                             program_image = image_datas['url']
#                     elif (program_datas['images']['square'] is not None and 'resolutions' in program_datas['images']['square']):
#                         for image_datas in program_datas['images']['square']['resolutions']:
#                             program_image = image_datas['url']

#                     item = Listitem()
#                     item.label = program_title
#                     item.art['thumb'] = item.art['landscape'] = program_image
#                     item.set_callback(
#                         list_videos_program,
#                         item_id=item_id,
#                         sub_category_code_name=sub_category_code_name,
#                         program_id=program_id)
#                     item_post_treatment(item)
#                     yield item

#                 if program_datas['subtitle']:
#                     video_title = '{title} - {subtitle}'.format(**program_datas)
#                 else:
#                     video_title = program_datas['title']
#                 video_id = program_datas['programId']
#                 video_image = ''
#                 if (program_datas['images']['landscape'] is not None and 'resolutions' in program_datas['images']['landscape']):
#                     for video_image_datas in program_datas['images']['landscape']['resolutions']:
#                         video_image = video_image_datas['url']
#                 elif (program_datas['images']['square'] is not None and 'resolutions' in program_datas['images']['square']):
#                     for image_datas in program_datas['images']['square']['resolutions']:
#                         program_image = image_datas['url']
#                 video_duration = program_datas["duration"]
#                 video_plot = program_datas.get("shortDescription", '')

#                 item = Listitem()
#                 item.label = video_title
#                 item.art['thumb'] = item.art['landscape'] = video_image
#                 item.info['duration'] = video_duration
#                 item.info['plot'] = video_plot

#                 item.set_callback(get_video_url,
#                                   item_id=item_id,
#                                   video_id=video_id)
#                 item_post_treatment(item,
#                                     is_playable=True,
#                                     is_downloadable=True)
#                 yield item

#             if sub_category_datas['nextPage'] is not None:
#                 yield Listitem.next_page(
#                     item_id=item_id,
#                     sub_category_title=sub_category_title,
#                     sub_category_code_name=sub_category_code_name,
#                     sub_category_url=sub_category_datas['nextPage'])


# @Route.register
# def list_programs_concert(plugin, item_id, sub_category_code_name, sub_category_url,
#                           **kwargs):
#     """
#     Build programs listing
#     - Les feux de l'amour
#     - ...
#     """
#     resp = urlquick.get(sub_category_url)
#     json_value = re.compile(r'_INITIAL_STATE__ \= (.*?)\}\;').findall(resp.text)[0]
#     json_parser = json.loads(json_value + '}')

#     value_code = json_parser['pages']['currentCode']
#     for sub_category_datas in json_parser['pages']['list'][value_code]['zones']:
#         if sub_category_datas['code']['name'] != sub_category_code_name:
#             continue

#         for program_datas in sub_category_datas['data']:
#             program_title = program_datas['title']
#             program_url = program_datas['url']
#             program_image = ''
#             for image_datas in program_datas['images']['landscape']['resolutions']:
#                 program_image = image_datas['url']

#             item = Listitem()
#             item.label = program_title
#             item.art['thumb'] = item.art['landscape'] = program_image
#             item.set_callback(
#                 list_videos_program_concert,
#                 item_id=item_id,
#                 program_url=program_url)
#             item_post_treatment(item)
#             yield item


# @Route.register
# def list_videos_sub_category(plugin, item_id, sub_category_url,
#                              **kwargs):

#     if '/api/' in sub_category_url:
#         resp = urlquick.get(sub_category_url.replace('https://api-internal.arte.tv', 'https://www.arte.tv/guide'))
#         json_parser = json.loads(resp.text)
#         for video_datas in json_parser['data']:
#             if video_datas['subtitle']:
#                 video_title = '{title} - {subtitle}'.format(**video_datas)
#             else:
#                 video_title = video_datas['title']
#             video_id = video_datas['programId']
#             video_image = ''
#             if 'resolutions' in video_datas['images']['landscape']:
#                 for video_image_datas in video_datas['images']['landscape']['resolutions']:
#                     video_image = video_image_datas['url']
#             video_duration = video_datas["duration"]
#             video_plot = video_datas.get("shortDescription", '')

#             item = Listitem()
#             item.label = video_title
#             item.art['thumb'] = item.art['landscape'] = video_image
#             item.info['duration'] = video_duration
#             item.info['plot'] = video_plot

#             item.set_callback(get_video_url,
#                               item_id=item_id,
#                               video_id=video_id)
#             item_post_treatment(item,
#                                 is_playable=True,
#                                 is_downloadable=True)
#             yield item

#         if json_parser['nextPage'] is not None:
#             yield Listitem.next_page(item_id=item_id,
#                                      sub_category_url=json_parser['nextPage'])
#     else:
#         resp = urlquick.get(sub_category_url)
#         json_value = re.compile(r'_INITIAL_STATE__ \= (.*?)\}\;').findall(resp.text)[0]
#         json_parser = json.loads(json_value + '}')

#         value_code = json_parser['pages']['currentCode']
#         for sub_category_datas in json_parser['pages']['list'][value_code]['zones']:
#             if 'videos_subcategory' != sub_category_datas['code']['name']:
#                 continue

#             for video_datas in sub_category_datas['data']:
#                 if video_datas['subtitle']:
#                     video_title = '{title} - {subtitle}'.format(**video_datas)
#                 else:
#                     video_title = video_datas['title']
#                 video_id = video_datas['programId']
#                 video_image = ''
#                 if 'resolutions' in video_datas['images']['landscape']:
#                     for video_image_datas in video_datas['images']['landscape']['resolutions']:
#                         video_image = video_image_datas['url']
#                 video_duration = video_datas["duration"]
#                 video_plot = video_datas.get("shortDescription", '')

#                 item = Listitem()
#                 item.label = video_title
#                 item.art['thumb'] = item.art['landscape'] = video_image
#                 item.info['duration'] = video_duration
#                 item.info['plot'] = video_plot

#                 item.set_callback(get_video_url,
#                                   item_id=item_id,
#                                   video_id=video_id)
#                 item_post_treatment(item,
#                                     is_playable=True,
#                                     is_downloadable=True)
#                 yield item

#                 if sub_category_datas['nextPage'] is None:
#                     continue

#                 yield Listitem.next_page(item_id=item_id,
#                                          sub_category_url=sub_category_datas['nextPage'])


# @Route.register
# def list_videos_program(plugin, item_id, sub_category_code_name, program_id,
#                         **kwargs):

#     resp = urlquick.get(
#         URL_VIDEOS_2 %
#         (sub_category_code_name.upper(), program_id, DESIRED_LANGUAGE.lower()))
#     json_parser = json.loads(resp.text)

#     for video_datas in json_parser['videos']:
#         if video_datas['subtitle']:
#             video_title = '{title} - {subtitle}'.format(**video_datas)
#         else:
#             video_title = video_datas['title']
#         video_id = video_datas['programId']
#         vudeo_image = video_datas['imageUrl']
#         video_duration = video_datas["durationSeconds"]
#         video_plot = video_datas["shortDescription"]
#         date_value = video_datas["videoRightsBegin"].split(' ')
#         day = date_value[1]
#         try:
#             month = CORRECT_MONTH[date_value[2]]
#         except Exception:
#             month = '00'
#         year = date_value[3]
#         date_value = '-'.join((year, month, day))

#         item = Listitem()
#         item.label = video_title
#         item.art['thumb'] = item.art['landscape'] = vudeo_image
#         item.info['duration'] = video_duration
#         item.info['plot'] = video_plot
#         item.info.date(date_value, '%Y-%m-%d')

#         item.set_callback(get_video_url,
#                           item_id=item_id,
#                           video_id=video_id)
#         item_post_treatment(item, is_playable=True, is_downloadable=True)
#         yield item


# @Route.register
# def list_videos_program_concert(plugin, item_id, program_url,
#                                 **kwargs):

#     if '/api/' in program_url:
#         resp = urlquick.get(program_url.replace('https://api-internal.arte.tv', 'https://www.arte.tv/guide').replace(" ", ""))
#         json_parser = json.loads(resp.text)
#         for video_datas in json_parser['data']:
#             if video_datas['subtitle']:
#                 video_title = '{title} - {subtitle}'.format(**video_datas)
#             else:
#                 video_title = video_datas['title']
#             video_id = video_datas['programId']
#             video_image = ''
#             if 'resolutions' in video_datas['images']['landscape']:
#                 for video_image_datas in video_datas['images']['landscape']['resolutions']:
#                     video_image = video_image_datas['url']
#             video_duration = video_datas["duration"]
#             video_plot = video_datas.get("shortDescription", '')

#             item = Listitem()
#             item.label = video_title
#             item.art['thumb'] = item.art['landscape'] = video_image
#             item.info['duration'] = video_duration
#             item.info['plot'] = video_plot

#             item.set_callback(get_video_url,
#                               item_id=item_id,
#                               video_id=video_id)
#             item_post_treatment(item,
#                                 is_playable=True,
#                                 is_downloadable=True)
#             yield item

#         if json_parser['nextPage'] is not None:
#             yield Listitem.next_page(item_id=item_id,
#                                      program_url=json_parser['nextPage'])
#     else:
#         resp = urlquick.get(program_url.replace(" ", ""))
#         json_value = re.compile(r'_INITIAL_STATE__ \= (.*?)\}\;').findall(resp.text)[0]
#         json_parser = json.loads(json_value + '}')

#         value_code = json_parser['pages']['currentCode']
#         videos_datas = json_parser['pages']['list'][value_code]['zones'][0]
#         for video_datas in videos_datas['data']:
#             if video_datas['subtitle']:
#                 video_title = '{title} - {subtitle}'.format(**video_datas)
#             else:
#                 video_title = video_datas['title']
#             video_id = video_datas['programId']
#             video_image = ''
#             if 'resolutions' in video_datas['images']['landscape']:
#                 for video_image_datas in video_datas['images']['landscape']['resolutions']:
#                     video_image = video_image_datas['url']
#             video_duration = video_datas["duration"]
#             video_plot = video_datas.get("shortDescription", '')

#             item = Listitem()
#             item.label = video_title
#             item.art['thumb'] = item.art['landscape'] = video_image
#             item.info['duration'] = video_duration
#             item.info['plot'] = video_plot

#             item.set_callback(get_video_url,
#                               item_id=item_id,
#                               video_id=video_id)
#             item_post_treatment(item,
#                                 is_playable=True,
#                                 is_downloadable=True)
#             yield item

#         if videos_datas['nextPage'] is not None:
#             yield Listitem.next_page(item_id=item_id,
#                                      program_url=videos_datas['nextPage'])


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_id,
                  download_mode=False,
                  **kwargs):

    return resolver_proxy.get_arte_video_stream(plugin,
                                                DESIRED_LANGUAGE.lower(),
                                                video_id,
                                                download_mode)


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    final_language = kwargs.get('language', DESIRED_LANGUAGE)

    try:
        resp = urlquick.get(URL_TOKEN)
        token = re.compile(r'token\"\:\"(.*?)\"').findall(resp.text)[0]
    except Exception:
        token = 'MzYyZDYyYmM1Y2Q3ZWRlZWFjMmIyZjZjNTRiMGY4MzY4NzBhOWQ5YjE4MGQ1NGFiODJmOTFlZDQwN2FkOTZjMQ'

    headers = {
        'Authorization': 'Bearer %s' % token
    }
    resp2 = urlquick.get(URL_LIVE_ARTE % final_language.lower(), headers=headers)
    json_parser = json.loads(resp2.text)
    # return json_parser["data"]["attributes"]["streams"][0]["url"]

    # To uncomment if issue
    url_stream = json_parser["data"]["attributes"]["streams"][0]["url"]
    # manifest = urlquick.get(
    #     url_stream,
    #     headers={'User-Agent': web_utils.get_random_ua()},
    #     max_age=-1)
    # lines = manifest.text.splitlines()
    # final_url = ''
    # for k in range(0, len(lines) - 1):
    #     if 'RESOLUTION=' in lines[k]:
    #         final_url = lines[k + 1]

    return url_stream
