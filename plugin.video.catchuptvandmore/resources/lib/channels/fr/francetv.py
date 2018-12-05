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

from codequick import Route, Resolver, Listitem, utils, Script

from resources.lib.labels import LABELS
from resources.lib import web_utils
from resources.lib import resolver_proxy
import resources.lib.cq_utils as cqu

import json
import time
import urlquick


'''
Channels:
    * France 2
    * France 3 Nationale
    * France 4
    * France Ô
    * France 5
'''

URL_API = utils.urljoin_partial('http://api-front.yatta.francetv.fr')

URL_LIVE_JSON = URL_API('standard/edito/directs')

HEADERS_YATTA = {
    'X-Algolia-API-Key': '80d9c91958fc448dd20042d399ebdf16',
    'X-Algolia-Application-Id': 'VWDLASHUFE'
}


'''
URL_SEARCH_VIDEOS = 'https://vwdlashufe-dsn.algolia.net/1/indexes/' \
                    'yatta_prod_contents/query'

URL_YATTA_VIDEO = URL_API + '/standard/publish/contents/%s'
# Param : id_yatta

URL_VIDEOS = URL_API + '/standard/publish/taxonomies/%s/contents'
# program
'''


def replay_entry(plugin, item_id):
    """
    First executed function after replay_bridge
    """
    return list_categories(plugin, item_id)


@Route.register
def list_categories(plugin, item_id):
    """
    Build categories listing
    - actualités & société
    - vie quotidienne
    - jeux & divertissement
    - ...
    """
    # URL example: http://api-front.yatta.francetv.fr/standard/publish/channels/france-2/categories/
    # category_part_url example: actualites-et-societe

    url_categories = 'standard/publish/channels/%s/categories/' % item_id
    resp = urlquick.get(URL_API(url_categories))
    json_parser = json.loads(resp.text)

    for category in json_parser["result"]:
        item = Listitem()

        item.label = category["label"]
        category_part_url = category["url"]

        item.set_callback(
            list_programs,
            item_id=item_id,
            category_part_url=category_part_url)
        yield item

    '''
    Seems to be broken in current CodeQuick version
    yield Listitem.recent(
        list_videos_last,
        item_id=item_id)
    '''
    item = Listitem()
    item.label = 'Recent'
    item.set_callback(
        list_videos_last,
        item_id=item_id)
    yield item

    item = Listitem.search(
        list_videos_search,
        item_id=item_id)
    yield item


@Route.register
def list_programs(plugin, item_id, category_part_url, page=0):
    """
    Build programs listing
    - Journal de 20H
    - Cash investigation
    """
    # URL example: http://api-front.yatta.francetv.fr/standard/publish/categories/actualites-et-societe/programs/france-2/?size=20&page=0&filter=with-no-vod,only-visible&sort=begin_date:desc
    # program_part_url example: france-2_cash-investigation
    url_programs = 'standard/publish/categories/%s/programs/%s/' % (
        category_part_url, item_id)
    resp = urlquick.get(
        URL_API(url_programs),
        params={
            'size': 20,
            'page': page,
            'filter': 'with-no-vod,only-visible',
            'sort': 'begin_date:desc'})
    json_parser = json.loads(resp.text)

    for program in json_parser["result"]:
        item = Listitem()

        item.label = program["label"]
        if 'media_image' in program:
            if program["media_image"] is not None:
                for image_datas in program["media_image"]["patterns"]:
                    if "vignette_16x9" in image_datas["type"]:
                        item.art['thumb'] = URL_API(
                            image_datas["urls"]["w:1024"])

        if 'description' in program:
            item.info['plot'] = program['description']

        program_part_url = program["url_complete"].replace('/', '_')

        item.set_callback(
            list_videos,
            item_id=item_id,
            program_part_url=program_part_url)
        yield item

    # Next page
    if json_parser["cursor"]["next"] is not None:
        yield Listitem.next_page(
            item_id=item_id,
            category_part_url=category_part_url,
            page=json_parser["cursor"]["next"])


@Route.register
def list_videos_last(plugin, item_id, page=1):
    url_last = 'standard/publish/channels/%s/contents/' % item_id
    resp = urlquick.get(
        URL_API(url_last),
        params={
            'size': 20,
            'page': page,
            'filter': 'with-no-vod,only-visible',
            'sort': 'begin_date:desc'})
    json_parser = json.loads(resp.text)

    for video_datas in json_parser["result"]:
        item = Listitem()
        program_name = ''
        for program_datas in video_datas["content_has_taxonomys"]:
            if 'program' in program_datas["type"]:
                program_name = program_datas['taxonomy']['label']

        if program_name:
            if video_datas["type"] == 'extrait':
                item.label = 'Extrait - ' + program_name + ' ' + video_datas["title"]
            else:
                item.label = program_name + ' ' + video_datas["title"]
        else:
            if video_datas["type"] == 'extrait':
                item.label = 'Extrait - ' + ' ' + video_datas["title"]
            else:
                item.label = video_datas["title"]

        image = ''
        for video_media in video_datas["content_has_medias"]:
            if "main" in video_media["type"]:
                id_diffusion = video_media["media"]["si_id"]
                if video_datas["type"] != 'extrait':
                    item.info['duration'] = int(video_media["media"]["duration"])
            elif "image" in video_media["type"]:
                for image_datas in video_media["media"]["patterns"]:
                    if "vignette_16x9" in image_datas["type"]:
                        image = URL_API(image_datas["urls"]["w:1024"])

        date_value = video_datas['first_publication_date'].split('T')[0]
        # 2018-09-20T05:03:01+02:00
        item.info.date(date_value, '%Y-%m-%d')

        if "text" in video_datas:
            item.info['plot'] = video_datas["text"]

        item.art['fanart'] = image
        item.art['thumb'] = image

        item.context.script(
            get_video_url,
            plugin.localize(LABELS['Download']),
            item_id=item_id,
            id_diffusion=id_diffusion,
            video_label=LABELS[item_id] + ' - ' + item.label,
            download_mode=True)

        item.set_callback(
            get_video_url,
            item_id=item_id,
            id_diffusion=id_diffusion,
            item_dict=cqu.item2dict(item))
        yield item

    # More videos...
    if json_parser["cursor"]["next"] is not None:
        yield Listitem.next_page(
            item_id=item_id,
            page=json_parser["cursor"]["next"])


@Route.register
def list_videos(plugin, item_id, program_part_url, page=0):

    # URL example: http://api-front.yatta.francetv.fr/standard/publish/taxonomies/france-2_cash-investigation/contents/?size=20&page=0&sort=begin_date:desc&filter=with-no-vod,only-visible
    url_program = 'standard/publish/taxonomies/%s/contents/' % program_part_url
    resp = urlquick.get(
        URL_API(url_program),
        params={
            'size': 20,
            'page': page,
            'filter': 'with-no-vod,only-visible',
            'sort': 'sort=begin_date:desc'})
    json_parser = json.loads(resp.text)

    for video_datas in json_parser["result"]:
        item = Listitem()
        if video_datas["type"] == 'extrait':
            item.label = 'Extrait - ' + video_datas["title"]
        else:
            item.label = video_datas["title"]

        image = ''
        for video_media in video_datas["content_has_medias"]:
            if "main" in video_media["type"]:
                id_diffusion = video_media["media"]["si_id"]
                if video_datas["type"] != 'extrait':
                    item.info['duration'] = int(video_media["media"]["duration"])
            elif "image" in video_media["type"]:
                for image_datas in video_media["media"]["patterns"]:
                    if "vignette_16x9" in image_datas["type"]:
                        image = URL_API(image_datas["urls"]["w:1024"])

        date_value = video_datas['first_publication_date'].split('T')[0]
        item.info.date(date_value, '%Y-%m-%d')

        if "text" in video_datas:
            item.info['plot'] = video_datas["text"]

        item.art['fanart'] = image
        item.art['thumb'] = image

        item.context.script(
            get_video_url,
            plugin.localize(LABELS['Download']),
            item_id=item_id,
            id_diffusion=id_diffusion,
            video_label=LABELS[item_id] + ' - ' + item.label,
            download_mode=True)

        item.set_callback(
            get_video_url,
            item_id=item_id,
            id_diffusion=id_diffusion,
            item_dict=cqu.item2dict(item))
        yield item

    # More videos...
    if json_parser["cursor"]["next"] is not None:
        yield Listitem.next_page(
            item_id=item_id,
            program_part_url=program_part_url,
            page=json_parser["cursor"]["next"])


@Route.register
def list_videos_search(plugin, item_id, search_query, page=0):
    at_least_one_item = False

    while not at_least_one_item:
        url_search = 'https://vwdlashufe-dsn.algolia.net/1/indexes/yatta_prod_contents/'
        resp = urlquick.get(
            url_search,
            params={
                'page': page,
                'filters': 'class:video',
                'query': search_query},
            headers=HEADERS_YATTA)

        json_parser = json.loads(resp.text)

        nb_pages = json_parser['nbPages']

        for hit in json_parser['hits']:

            item_id_found = False
            for channel in hit['channels']:
                if channel['url'] == item_id:
                    item_id_found = True
                    break

            if not item_id_found:
                continue

            at_least_one_item = True

            title = hit['title']
            if 'program' in hit:
                label = hit['program']['label']
                title = label + ' - ' + title
            headline = hit['headline_title']
            desc = hit['text']
            duration = hit['duration']
            season = hit['season_number']
            episode = hit['episode_number']
            id_yatta = hit['id']
            director = hit['director']
            # producer = hit['producer']
            presenter = hit['presenter']
            casting = hit['casting']
            # characters = hit['characters']
            last_publication_date = hit['dates']['last_publication_date']
            date_value = time.strftime(
                '%Y-%m-%d', time.localtime(last_publication_date))

            image_400 = ''
            image_1024 = ''
            if 'image' in hit:
                image_400 = hit['image']['formats']['vignette_16x9']['urls']['w:400']
                image_1024 = hit['image']['formats']['vignette_16x9']['urls']['w:1024']

            image_400 = URL_API(image_400)
            image_1024 = URL_API(image_1024)

            if headline and headline != '':
                desc = headline + '\n' + desc

            if not director:
                director = presenter

            item = Listitem()
            item.label = title
            item.art['fanart'] = image_1024
            item.art['thumb'] = image_400
            item.info['plot'] = desc
            item.info['duration'] = duration
            item.info['season'] = season
            item.info['episode'] = episode
            item.info['cast'] = casting.split(', ')
            item.info['director'] = director
            item.info.date(date_value, '%Y-%m-%d')

            item.context.script(
                get_video_url,
                plugin.localize(LABELS['Download']),
                item_id=item_id,
                id_yatta=id_yatta,
                video_label=LABELS[item_id] + ' - ' + item.label,
                download_mode=True)

            item.set_callback(
                get_video_url,
                item_id=item_id,
                id_yatta=id_yatta,
                item_dict=cqu.item2dict(item))
            yield item
        page = page + 1


    # More videos...
    if page != nb_pages - 1:
        yield Listitem.next_page(
            search_query=search_query,
            item_id=item_id,
            page=page + 1)


@Resolver.register
def get_video_url(
        plugin, item_id, id_diffusion=None,
        id_yatta=None, item_dict=None, download_mode=False, video_label=None):

    if id_yatta is not None:
        url_yatta_video = 'standard/publish/contents/%s' % id_yatta
        resp = urlquick.get(URL_API(url_yatta_video), max_age=-1)
        json_parser = json.loads(resp.text)
        for media in json_parser['content_has_medias']:
            if 'si_id' in media['media']:
                id_diffusion = media['media']['si_id']
                break

    return resolver_proxy.get_francetv_video_stream(
        plugin, id_diffusion, item_dict, download_mode, video_label)


def live_entry(plugin, item_id, item_dict):
    return get_live_url(plugin, item_id, item_id.upper(), item_dict)


@Resolver.register
def get_live_url(plugin, item_id, video_id, item_dict):

    resp = urlquick.get(
        URL_LIVE_JSON,
        headers={'User-Agent': web_utils.get_random_ua},
        max_age=-1)
    json_parser = json.loads(resp.text)

    for live in json_parser["result"]:
        if live["channel"] == item_id:
            live_datas = live["collection"][0]["content_has_medias"]
            liveId = ''
            for live_data in live_datas:
                if "si_direct_id" in live_data["media"]:
                    liveId = live_data["media"]["si_direct_id"]
            return resolver_proxy.get_francetv_live_stream(plugin, liveId)
