# -*- coding: utf-8 -*-
"""
    Catch-up TV & More
    Original work (C) JUL1EN094, SPM, SylvainCecchetto
    Copyright (C) 2016  SylvainCecchetto

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

from builtins import str
from codequick import Route, Resolver, Listitem, utils, Script

from resources.lib.labels import LABELS
from resources.lib import web_utils
from resources.lib import resolver_proxy
from resources.lib import download
from resources.lib.listitem_utils import item_post_treatment, item2dict

import json
import re
import urlquick

# TO DO

# Info
# LCP contient deux sources de video pour les replays
# Old : play1.qbrick.com
# New : www.dailymotion.com

URL_ROOT = 'http://www.lcp.fr'

URL_LIVE_SITE = 'http://www.lcp.fr/le-direct'

URL_VIDEO_REPLAY = 'http://play1.qbrick.com/config/avp/v1/player/' \
                   'media/%s/darkmatter/%s/'
# VideoID, AccountId

CATEGORIES = {
    URL_ROOT + '/actualites': 'Actualités',
    URL_ROOT + '/emissions': 'Émissions',
    URL_ROOT + '/documentaires': 'Documentaires'
}

CORRECT_MONTH = {
    'janvier': '01',
    'février': '02',
    'mars': '03',
    'avril': '04',
    'mai': '05',
    'juin': '06',
    'juillet': '07',
    'août': '08',
    'septembre': '09',
    'octobre': '10',
    'novembre': '11',
    'décembre': '12'
}


def replay_entry(plugin, item_id, **kwargs):
    """
    First executed function after replay_bridge
    """
    return list_categories(plugin, item_id)


@Route.register
def list_categories(plugin, item_id, **kwargs):
    """
    Build categories listing
    - Tous les programmes
    - Séries
    - Informations
    - ...
    """
    for category_url, category_name in list(CATEGORIES.items()):

        if 'actualites' in category_url:
            item = Listitem()
            item.label = category_name
            item.set_callback(list_videos_actualites,
                              item_id=item_id,
                              next_url=category_url,
                              page='0')
            item_post_treatment(item)
            yield item
        if 'emissions' in category_url:
            item = Listitem()
            item.label = category_name
            item.set_callback(list_programs,
                              item_id=item_id,
                              next_url=category_url)
            item_post_treatment(item)
            yield item
        if 'documentaires' in category_url:
            item = Listitem()
            item.label = category_name
            item.set_callback(list_videos_documentaires,
                              item_id=item_id,
                              next_url=category_url)
            item_post_treatment(item)
            yield item


@Route.register
def list_programs(plugin, item_id, next_url, **kwargs):
    """
    Build programs listing
    - Journal de 20H
    - Cash investigation
    """
    resp = urlquick.get(next_url)
    root = resp.parse()

    for program_datas in root.iterfind(".//div[@class='content']"):
        program_title = program_datas.find('.//h2').text
        program_image = program_datas.find('.//img').get('src')
        program_url = URL_ROOT + program_datas.find('.//a').get('href')

        item = Listitem()
        item.label = program_title
        item.art['thumb'] = program_image
        item.set_callback(list_videos_program,
                          item_id=item_id,
                          next_url=program_url,
                          page='0')
        item_post_treatment(item)
        yield item


@Route.register
def list_videos_documentaires(plugin, item_id, next_url, **kwargs):

    resp = urlquick.get(next_url)
    root = resp.parse()

    for video_datas in root.iterfind(
            ".//div[@class='col-md-3 col-sm-6 col-xs-12']"):
        video_title = video_datas.find(
            ".//span[@class='rdf-meta element-hidden']").get('content')
        video_image = video_datas.find('.//img').get('src')
        video_duration = int(
            video_datas.find(".//div[@class='duration']").find('.//div').find(
                './/span').text) * 60
        video_url = URL_ROOT + video_datas.find('.//a').get('href')
        date_value = video_datas.find(".//span[@class='date']").text
        date = date_value.split(' ')
        day = date[0]
        try:
            month = CORRECT_MONTH[date[1]]
        except Exception:
            month = '00'
        year = date[2]
        date_value = year + '-' + month + '-' + day

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = video_image
        item.info['duration'] = video_duration
        item.info.date(date_value, '%Y-%m-%d')

        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_label=LABELS[item_id] + ' - ' + item.label,
                          video_url=video_url)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item


@Route.register
def list_videos_actualites(plugin, item_id, next_url, page, **kwargs):

    if page == '0':
        videos_actualites_url = next_url
    else:
        videos_actualites_url = next_url + '?page=' + page

    resp = urlquick.get(videos_actualites_url)
    root = resp.parse()

    for video_datas in root.iterfind(
            ".//div[@class='col-md-6 col-sm-6 col-xs-12']"):
        if len(video_datas.findall(".//svg[@class='icon icon-play2']")) > 0:
            video_title = video_datas.find(
                ".//span[@class='rdf-meta element-hidden']").get('content')
            video_image = video_datas.find('.//img').get('src')
            video_url = URL_ROOT + video_datas.find('.//a').get('href')
            date_value = video_datas.find(
                ".//div[@class='field field_submitted']").text
            date = date_value.split('/')
            date_value = date[2] + '-' + date[1] + '-' + date[0]

            item = Listitem()
            item.label = video_title
            item.art['thumb'] = video_image
            item.info.date(date_value, '%Y-%m-%d')

            item.set_callback(get_video_url,
                              item_id=item_id,
                              video_label=LABELS[item_id] + ' - ' + item.label,
                              video_url=video_url)
            item_post_treatment(item, is_playable=True, is_downloadable=True)
            yield item

    yield Listitem.next_page(item_id=item_id,
                             next_url=next_url,
                             page=str(int(page) + 1))


@Route.register
def list_videos_program(plugin, item_id, next_url, page, **kwargs):

    # Cas emission (2 cas) (-0) ou (sans -0)
    # 1ère page http://www.lcp.fr/emissions/evenements/replay-0
    # (url départ => http://www.lcp.fr/emissions/evenements-0)
    # 1ère page http://www.lcp.fr/emissions/evenements/replay-0?page=1
    # ainsi de suite
    # 1ère page : http://www.lcp.fr/emissions/en-voiture-citoyens/replay
    # (url départ => http://www.lcp.fr/emissions/en-voiture-citoyens)
    # 2ème page :
    # http://www.lcp.fr/emissions/en-voiture-citoyens/replay?page=1
    # ainsi de suite
    # TODO fix some cases http://www.lcp.fr/emissions/questions-au-gouvernement/replay-2 http://www.lcp.fr/emissions/questions-au-gouvernement-2

    if page == '0' and '-0' not in next_url:
        video_program_url = next_url + '/replay'
    elif int(page) > 0 and '-0' not in next_url:
        video_program_url = next_url + '/replay?page=' + page
    elif page == '0' and '-0' in next_url:
        video_program_url = next_url[:-2] + '/replay-0'
    elif int(page) > 0 and '-0' in next_url:
        video_program_url = next_url[:-2] + '/replay-0?page=' + page

    resp = urlquick.get(video_program_url)
    root = resp.parse()

    for video_datas in root.iterfind(
            ".//div[@class='col-md-3 col-sm-6 col-xs-12']"):
        video_title = video_datas.find(
            ".//span[@class='rdf-meta element-hidden']").get('content')
        video_image = video_datas.find('.//img').get('src')
        video_duration = int(
            video_datas.find(".//div[@class='duration']").find('.//div').find(
                './/span').text) * 60
        video_url = URL_ROOT + video_datas.find('.//a').get('href')
        date_value = video_datas.find(".//span[@class='date']").text
        date = date_value.split(' ')
        day = date[0]
        try:
            month = CORRECT_MONTH[date[1]]
        except Exception:
            month = '00'
        year = date[2]
        date_value = year + '-' + month + '-' + day

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = video_image
        item.info['duration'] = video_duration
        item.info.date(date_value, '%Y-%m-%d')

        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_label=LABELS[item_id] + ' - ' + item.label,
                          video_url=video_url)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item

    yield Listitem.next_page(item_id=item_id,
                             next_url=next_url,
                             page=str(int(page) + 1))


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_url,
                  download_mode=False,
                  video_label=False,
                  **kwargs):

    resp = urlquick.get(video_url,
                        headers={'User-Agent': web_utils.get_random_ua()},
                        max_age=-1)

    if 'dailymotion' in resp.text:
        video_id = re.compile(
            r'www.dailymotion.com/embed/video/(.*?)[\?\"]').findall(
                resp.text)[0]
        return resolver_proxy.get_stream_dailymotion(plugin, video_id,
                                                     download_mode,
                                                     video_label)
    else:
        # get videoId and accountId
        videoId, accountId = re.compile(r'embed/(.*?)/(.*?)/').findall(
            resp.text)[0]

        resp2 = urlquick.get(URL_VIDEO_REPLAY % (videoId, accountId),
                             headers={'User-Agent': web_utils.get_random_ua()},
                             max_age=-1)
        json_parser = json.loads(
            re.compile(r'\((.*?)\);').findall(resp2.text)[0])

        for playlist in json_parser['Playlist']:
            datas_video = playlist['MediaFiles']['M3u8']
            for data in datas_video:
                url = data['Url']

        if download_mode:
            return download.download_video(url, video_label)
        return url


def live_entry(plugin, item_id, item_dict, **kwargs):
    return get_live_url(plugin, item_id, item_id.upper(), item_dict)


@Resolver.register
def get_live_url(plugin, item_id, video_id, item_dict, **kwargs):

    resp = urlquick.get(URL_LIVE_SITE,
                        headers={'User-Agent': web_utils.get_random_ua()},
                        max_age=-1)
    video_id = re.compile(
        r'www.dailymotion.com/embed/video/(.*?)[\?\"]').findall(resp.text)[0]
    return resolver_proxy.get_stream_dailymotion(plugin, video_id, False)
