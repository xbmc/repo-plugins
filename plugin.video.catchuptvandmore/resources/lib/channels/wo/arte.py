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
from resources.lib import download
from resources.lib.menu_utils import item_post_treatment
from resources.lib import resolver_proxy

import json
import re
import urlquick
from kodi_six import xbmcgui

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


@Route.register
def list_categories(plugin, item_id, **kwargs):
    """
    Build categories listing
    - Tous les programmes
    - Séries
    - Informations
    - ...
    """
    resp = urlquick.get(URL_ROOT % DESIRED_LANGUAGE.lower())
    json_value = re.compile(r'_INITIAL_STATE__ \= (.*?)\}\;').findall(
        resp.text)[0]
    # print 'json_value : ' + repr(json_value)
    json_parser = json.loads(json_value + '}')

    for category_datas in json_parser['categories']:
        category_title = category_datas['label']
        category_url = category_datas['url']

        item = Listitem()
        item.label = category_title
        item.set_callback(list_sub_categories,
                          item_id=item_id,
                          category_url=category_url)
        item_post_treatment(item)
        yield item


@Route.register
def list_sub_categories(plugin, item_id, category_url, **kwargs):
    """
    Build programs listing
    - Les feux de l'amour
    - ...
    """

    resp = urlquick.get(category_url)
    json_value = re.compile(r'_INITIAL_STATE__ \= (.*?)\}\;').findall(
        resp.text)[0]
    json_parser = json.loads(json_value + '}')

    value_code = json_parser['pages']['currentCode']
    for sub_category_datas in json_parser['pages']['list'][value_code][
            'zones']:
        if 'subcategory' in sub_category_datas['code']['name']:
            sub_category_title = sub_category_datas['title']
            sub_category_url = sub_category_datas['link']['url']

            item = Listitem()
            item.label = sub_category_title
            item.set_callback(list_videos_sub_category,
                              item_id=item_id,
                              sub_category_url=sub_category_url)
            item_post_treatment(item)
            yield item

        elif 'genres' in sub_category_datas['code']['name']:
            sub_category_title = sub_category_datas['title']
            sub_category_code_name = sub_category_datas['code']['name']
            sub_category_url = category_url

            item = Listitem()
            item.label = sub_category_title

            item.set_callback(list_programs_concert,
                              item_id=item_id,
                              sub_category_code_name=sub_category_code_name,
                              sub_category_url=sub_category_url)
            item_post_treatment(item)
            yield item

        elif 'banner' in sub_category_datas['code']['name']:
            continue

        elif 'playlists' in sub_category_datas['code']['name'] or \
                'collections' in sub_category_datas['code']['name'] or \
                'magazines' in sub_category_datas['code']['name'] or \
                'ARTE_CONCERT' in sub_category_datas['code']['name'] or \
                'highlights_category' in sub_category_datas['code']['name'] or \
                '-' in sub_category_datas['code']['name'] or \
                'collection_videos' in sub_category_datas['code']['name'] or \
                'collection_subcollection' in sub_category_datas['code']['name']:
            if sub_category_datas['data']:
                sub_category_title = sub_category_datas['title']
                sub_category_code_name = sub_category_datas['code']['name']
                sub_category_url = category_url

                item = Listitem()
                item.label = sub_category_title

                item.set_callback(list_programs,
                                  item_id=item_id,
                                  sub_category_title=sub_category_title,
                                  sub_category_code_name=sub_category_code_name,
                                  sub_category_url=sub_category_url)
                item_post_treatment(item)
                yield item

        # else:
        #     # Add Notification (Category Not known)
        #     return None


@Route.register
def list_programs(plugin, item_id, sub_category_title, sub_category_code_name, sub_category_url,
                  **kwargs):
    """
    Build programs listing
    - Les feux de l'amour
    - ...
    """

    if '/api/' in sub_category_url:
        resp = urlquick.get(sub_category_url.replace('https://api-internal.arte.tv', 'https://www.arte.tv/guide'))
        json_parser = json.loads(resp.text)
        # for video_datas in json_parser['data']:
        for program_datas in json_parser['data']:
            if program_datas["kind"]["isCollection"]:
                program_title = program_datas['title']
                program_url = program_datas['url']
                program_image = ''
                if program_datas['images']['landscape'] is not None:
                    if 'resolutions' in program_datas['images']['landscape']:
                        for image_datas in program_datas['images']['landscape'][
                                'resolutions']:
                            program_image = image_datas['url']
                elif program_datas['images']['square'] is not None:
                    if 'resolutions' in program_datas['images']['square']:
                        for image_datas in program_datas['images']['square'][
                                'resolutions']:
                            program_image = image_datas['url']

                item = Listitem()
                item.label = program_title
                item.art['thumb'] = item.art['landscape'] = program_image
                item.set_callback(
                    list_sub_categories,
                    item_id=item_id,
                    category_url=program_url)
                item_post_treatment(item)
                yield item
            elif program_datas['programId'] is not None and 'RC-' in program_datas['programId']:
                program_title = program_datas['title']
                program_id = program_datas['programId']
                program_image = ''
                if program_datas['images']['landscape'] is not None:
                    if 'resolutions' in program_datas['images']['landscape']:
                        for image_datas in program_datas['images']['landscape'][
                                'resolutions']:
                            program_image = image_datas['url']
                elif program_datas['images']['square'] is not None:
                    if 'resolutions' in program_datas['images']['square']:
                        for image_datas in program_datas['images']['square'][
                                'resolutions']:
                            program_image = image_datas['url']

                item = Listitem()
                item.label = program_title
                item.art['thumb'] = item.art['landscape'] = program_image
                item.set_callback(
                    list_videos_program,
                    item_id=item_id,
                    sub_category_code_name=sub_category_code_name,
                    program_id=program_id)
                item_post_treatment(item)
                yield item
            else:
                if program_datas['subtitle'] is not None:
                    video_title = program_datas['title'] + ' - ' + program_datas[
                        'subtitle']
                else:
                    video_title = program_datas['title']
                video_id = program_datas['programId']
                video_image = ''
                if program_datas['images']['landscape'] is not None:
                    if 'resolutions' in program_datas['images']['landscape']:
                        for video_image_datas in program_datas['images'][
                                'landscape']['resolutions']:
                            video_image = video_image_datas['url']
                elif program_datas['images']['square'] is not None:
                    if 'resolutions' in program_datas['images']['square']:
                        for image_datas in program_datas['images']['square'][
                                'resolutions']:
                            program_image = image_datas['url']
                video_duration = program_datas["duration"]
                video_plot = program_datas.get("shortDescription", '')

                item = Listitem()
                item.label = video_title
                item.art['thumb'] = item.art['landscape'] = video_image
                item.info['duration'] = video_duration
                item.info['plot'] = video_plot

                item.set_callback(get_video_url,
                                  item_id=item_id,
                                  video_id=video_id)
                item_post_treatment(item,
                                    is_playable=True,
                                    is_downloadable=True)
                yield item

        if json_parser['nextPage'] is not None:
            yield Listitem.next_page(
                item_id=item_id,
                sub_category_title=sub_category_title,
                sub_category_code_name=sub_category_code_name,
                sub_category_url=json_parser['nextPage'])
    else:
        resp = urlquick.get(sub_category_url)
        json_value = re.compile(r'_INITIAL_STATE__ \= (.*?)\}\;').findall(
            resp.text)[0]
        json_parser = json.loads(json_value + '}')

        value_code = json_parser['pages']['currentCode']
        for sub_category_datas in json_parser['pages']['list'][value_code][
                'zones']:
            if (sub_category_datas['code']['name'] == sub_category_code_name and
                    sub_category_title == sub_category_datas['title']):

                for program_datas in sub_category_datas['data']:
                    if program_datas["kind"]["isCollection"]:
                        program_title = program_datas['title']
                        program_url = program_datas['url']
                        program_image = ''
                        if program_datas['images']['landscape'] is not None:
                            if 'resolutions' in program_datas['images']['landscape']:
                                for image_datas in program_datas['images']['landscape'][
                                        'resolutions']:
                                    program_image = image_datas['url']
                        elif program_datas['images']['square'] is not None:
                            if 'resolutions' in program_datas['images']['square']:
                                for image_datas in program_datas['images']['square'][
                                        'resolutions']:
                                    program_image = image_datas['url']

                        item = Listitem()
                        item.label = program_title
                        item.art['thumb'] = item.art['landscape'] = program_image
                        item.set_callback(
                            list_sub_categories,
                            item_id=item_id,
                            category_url=program_url)
                        item_post_treatment(item)
                        yield item
                    elif program_datas['programId'] is not None and 'RC-' in program_datas['programId']:
                        program_title = program_datas['title']
                        program_id = program_datas['programId']
                        program_image = ''
                        if program_datas['images']['landscape'] is not None:
                            if 'resolutions' in program_datas['images']['landscape']:
                                for image_datas in program_datas['images']['landscape'][
                                        'resolutions']:
                                    program_image = image_datas['url']
                        elif program_datas['images']['square'] is not None:
                            if 'resolutions' in program_datas['images']['square']:
                                for image_datas in program_datas['images']['square'][
                                        'resolutions']:
                                    program_image = image_datas['url']

                        item = Listitem()
                        item.label = program_title
                        item.art['thumb'] = item.art['landscape'] = program_image
                        item.set_callback(
                            list_videos_program,
                            item_id=item_id,
                            sub_category_code_name=sub_category_code_name,
                            program_id=program_id)
                        item_post_treatment(item)
                        yield item
                    else:
                        if program_datas['subtitle'] is not None:
                            video_title = program_datas['title'] + ' - ' + program_datas[
                                'subtitle']
                        else:
                            video_title = program_datas['title']
                        video_id = program_datas['programId']
                        video_image = ''
                        if program_datas['images']['landscape'] is not None:
                            if 'resolutions' in program_datas['images']['landscape']:
                                for video_image_datas in program_datas['images'][
                                        'landscape']['resolutions']:
                                    video_image = video_image_datas['url']
                        elif program_datas['images']['square'] is not None:
                            if 'resolutions' in program_datas['images']['square']:
                                for image_datas in program_datas['images']['square'][
                                        'resolutions']:
                                    program_image = image_datas['url']
                        video_duration = program_datas["duration"]
                        video_plot = program_datas.get("shortDescription", '')

                        item = Listitem()
                        item.label = video_title
                        item.art['thumb'] = item.art['landscape'] = video_image
                        item.info['duration'] = video_duration
                        item.info['plot'] = video_plot

                        item.set_callback(get_video_url,
                                          item_id=item_id,
                                          video_id=video_id)
                        item_post_treatment(item,
                                            is_playable=True,
                                            is_downloadable=True)
                        yield item

                if sub_category_datas['nextPage'] is not None:
                    yield Listitem.next_page(
                        item_id=item_id,
                        sub_category_title=sub_category_title,
                        sub_category_code_name=sub_category_code_name,
                        sub_category_url=sub_category_datas['nextPage'])


@Route.register
def list_programs_concert(plugin, item_id, sub_category_code_name, sub_category_url,
                          **kwargs):
    """
    Build programs listing
    - Les feux de l'amour
    - ...
    """
    resp = urlquick.get(sub_category_url)
    json_value = re.compile(r'_INITIAL_STATE__ \= (.*?)\}\;').findall(
        resp.text)[0]
    json_parser = json.loads(json_value + '}')

    value_code = json_parser['pages']['currentCode']
    for sub_category_datas in json_parser['pages']['list'][value_code][
            'zones']:
        if sub_category_datas['code']['name'] == sub_category_code_name:
            for program_datas in sub_category_datas['data']:
                program_title = program_datas['title']
                program_url = program_datas['url']
                program_image = ''
                for image_datas in program_datas['images']['landscape'][
                        'resolutions']:
                    program_image = image_datas['url']

                item = Listitem()
                item.label = program_title
                item.art['thumb'] = item.art['landscape'] = program_image
                item.set_callback(
                    list_videos_program_concert,
                    item_id=item_id,
                    program_url=program_url)
                item_post_treatment(item)
                yield item


@Route.register
def list_videos_sub_category(plugin, item_id, sub_category_url,
                             **kwargs):

    if '/api/' in sub_category_url:
        resp = urlquick.get(sub_category_url.replace('https://api-internal.arte.tv', 'https://www.arte.tv/guide'))
        json_parser = json.loads(resp.text)
        for video_datas in json_parser['data']:
            if video_datas['subtitle'] is not None:
                video_title = video_datas['title'] + ' - ' + video_datas[
                    'subtitle']
            else:
                video_title = video_datas['title']
            video_id = video_datas['programId']
            video_image = ''
            if 'resolutions' in video_datas['images']['landscape']:
                for video_image_datas in video_datas['images'][
                        'landscape']['resolutions']:
                    video_image = video_image_datas['url']
            video_duration = video_datas["duration"]
            video_plot = video_datas.get("shortDescription", '')

            item = Listitem()
            item.label = video_title
            item.art['thumb'] = item.art['landscape'] = video_image
            item.info['duration'] = video_duration
            item.info['plot'] = video_plot

            item.set_callback(get_video_url,
                              item_id=item_id,
                              video_id=video_id)
            item_post_treatment(item,
                                is_playable=True,
                                is_downloadable=True)
            yield item

        if json_parser['nextPage'] is not None:
            yield Listitem.next_page(item_id=item_id,
                                     sub_category_url=json_parser['nextPage'])
    else:
        resp = urlquick.get(sub_category_url)
        json_value = re.compile(r'_INITIAL_STATE__ \= (.*?)\}\;').findall(
            resp.text)[0]
        json_parser = json.loads(json_value + '}')

        value_code = json_parser['pages']['currentCode']
        for sub_category_datas in json_parser['pages']['list'][value_code][
                'zones']:
            if 'videos_subcategory' == sub_category_datas['code']['name']:
                for video_datas in sub_category_datas['data']:
                    if video_datas['subtitle'] is not None:
                        video_title = video_datas['title'] + ' - ' + video_datas[
                            'subtitle']
                    else:
                        video_title = video_datas['title']
                    video_id = video_datas['programId']
                    video_image = ''
                    if 'resolutions' in video_datas['images']['landscape']:
                        for video_image_datas in video_datas['images'][
                                'landscape']['resolutions']:
                            video_image = video_image_datas['url']
                    video_duration = video_datas["duration"]
                    video_plot = video_datas.get("shortDescription", '')

                    item = Listitem()
                    item.label = video_title
                    item.art['thumb'] = item.art['landscape'] = video_image
                    item.info['duration'] = video_duration
                    item.info['plot'] = video_plot

                    item.set_callback(get_video_url,
                                      item_id=item_id,
                                      video_id=video_id)
                    item_post_treatment(item,
                                        is_playable=True,
                                        is_downloadable=True)
                    yield item

                if sub_category_datas['nextPage'] is not None:
                    yield Listitem.next_page(item_id=item_id,
                                             sub_category_url=sub_category_datas['nextPage'])


@Route.register
def list_videos_program(plugin, item_id, sub_category_code_name, program_id,
                        **kwargs):

    resp = urlquick.get(
        URL_VIDEOS_2 %
        (sub_category_code_name.upper(), program_id, DESIRED_LANGUAGE.lower()))
    json_parser = json.loads(resp.text)

    for video_datas in json_parser['videos']:
        if video_datas['subtitle'] is not None:
            video_title = video_datas['title'] + ' - ' + video_datas['subtitle']
        else:
            video_title = video_datas['title']
        video_id = video_datas['programId']
        vudeo_image = video_datas['imageUrl']
        video_duration = video_datas["durationSeconds"]
        video_plot = video_datas["shortDescription"]
        date_value = video_datas["videoRightsBegin"].split(' ')
        day = date_value[1]
        try:
            month = CORRECT_MONTH[date_value[2]]
        except Exception:
            month = '00'
        year = date_value[3]
        date_value = '-'.join((year, month, day))

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = item.art['landscape'] = vudeo_image
        item.info['duration'] = video_duration
        item.info['plot'] = video_plot
        item.info.date(date_value, '%Y-%m-%d')

        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_id=video_id)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item


@Route.register
def list_videos_program_concert(plugin, item_id, program_url,
                                **kwargs):

    if '/api/' in program_url:
        resp = urlquick.get(program_url.replace('https://api-internal.arte.tv', 'https://www.arte.tv/guide').replace(" ", ""))
        json_parser = json.loads(resp.text)
        for video_datas in json_parser['data']:
            if video_datas['subtitle'] is not None:
                video_title = video_datas['title'] + ' - ' + video_datas[
                    'subtitle']
            else:
                video_title = video_datas['title']
            video_id = video_datas['programId']
            video_image = ''
            if 'resolutions' in video_datas['images']['landscape']:
                for video_image_datas in video_datas['images'][
                        'landscape']['resolutions']:
                    video_image = video_image_datas['url']
            video_duration = video_datas["duration"]
            video_plot = video_datas.get("shortDescription", '')

            item = Listitem()
            item.label = video_title
            item.art['thumb'] = item.art['landscape'] = video_image
            item.info['duration'] = video_duration
            item.info['plot'] = video_plot

            item.set_callback(get_video_url,
                              item_id=item_id,
                              video_id=video_id)
            item_post_treatment(item,
                                is_playable=True,
                                is_downloadable=True)
            yield item

        if json_parser['nextPage'] is not None:
            yield Listitem.next_page(item_id=item_id,
                                     program_url=json_parser['nextPage'])
    else:
        resp = urlquick.get(program_url.replace(" ", ""))
        json_value = re.compile(r'_INITIAL_STATE__ \= (.*?)\}\;').findall(
            resp.text)[0]
        json_parser = json.loads(json_value + '}')

        value_code = json_parser['pages']['currentCode']
        videos_datas = json_parser['pages']['list'][value_code]['zones'][0]
        for video_datas in videos_datas['data']:
            if video_datas['subtitle'] is not None:
                video_title = video_datas['title'] + ' - ' + video_datas[
                    'subtitle']
            else:
                video_title = video_datas['title']
            video_id = video_datas['programId']
            video_image = ''
            if 'resolutions' in video_datas['images']['landscape']:
                for video_image_datas in video_datas['images'][
                        'landscape']['resolutions']:
                    video_image = video_image_datas['url']
            video_duration = video_datas["duration"]
            video_plot = video_datas.get("shortDescription", '')

            item = Listitem()
            item.label = video_title
            item.art['thumb'] = item.art['landscape'] = video_image
            item.info['duration'] = video_duration
            item.info['plot'] = video_plot

            item.set_callback(get_video_url,
                              item_id=item_id,
                              video_id=video_id)
            item_post_treatment(item,
                                is_playable=True,
                                is_downloadable=True)
            yield item

        if videos_datas['nextPage'] is not None:
            yield Listitem.next_page(item_id=item_id,
                                     program_url=videos_datas['nextPage'])


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

    resp = urlquick.get(URL_TOKEN)
    token = re.compile(r'token\"\:\"(.*?)\"').findall(resp.text)[0]

    headers = {
        'Authorization': 'Bearer %s' % token
    }
    resp2 = urlquick.get(URL_LIVE_ARTE % final_language.lower(), headers=headers)
    json_parser = json.loads(resp2.text)
    # return json_parser["data"]["attributes"]["streams"][0]["url"]

    # To uncomment if issue
    url_stream = json_parser["data"]["attributes"]["streams"][0]["url"]
    manifest = urlquick.get(
        url_stream,
        headers={'User-Agent': web_utils.get_random_ua()},
        max_age=-1)
    lines = manifest.text.splitlines()
    final_url = ''
    for k in range(0, len(lines) - 1):
        if 'RESOLUTION=' in lines[k]:
            final_url = lines[k + 1]

    return final_url
