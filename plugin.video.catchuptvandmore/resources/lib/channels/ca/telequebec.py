# -*- coding: utf-8 -*-
# Copyright: (c) 2017, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import json
import time
import urlquick

from codequick import Listitem, Resolver, Route

from resources.lib import resolver_proxy, web_utils
from resources.lib.menu_utils import item_post_treatment

# TO DO
# Add info LIVE TV, Replay

URL_API = 'https://beacon.playback.api.brightcove.com/telequebec/api'

URL_LIVE_DATAS = URL_API + '/epg?device_type=web&device_layout=web&datetimestamp=%s'
# datetimestamp

URL_BRIGHTCOVE_DATAS = URL_API + '/assets/%s/streams/%s'
# ContentId, StreamId

URL_CATEGORIES = URL_API + '/menus/0/option/29060-sur-demande?device_type=web&device_layout=web'

URL_ALL_PROGRAMS_PER_CATEGORY = URL_API + '/playlists/%s/assets?limit=30&device_type=web&device_layout=web&layout_id=347&page=%s'

URL_PROGRAM_ASSETS = URL_API + '/assets/%s?device_type=web&device_layout=web&asset_id=%s'
# ProgramId, ProgramId

URL_SEASON_VIDEOS = URL_API + '/tvshow/%s/season/%s/episodes?device_type=web&device_layout=web&layout_id=317&limit=1000'
# ProgramId, SeasonSlug


@Route.register
def list_categories(plugin, item_id, **kwargs):
    """
    Build categories listing
    - Tous les programmes
    - Séries
    - Informations
    - ...
    """
    resp = urlquick.get(URL_CATEGORIES)
    json_parser = json.loads(resp.text)

    for category_datas in json_parser['data']['screen']['blocks']:
        category_title = category_datas['widgets'][0]['playlist']['name']
        category_id = category_datas['widgets'][0]['playlist']['id']

        item = Listitem()
        item.label = category_title
        item.set_callback(
            list_programs, item_id=item_id, category_id=category_id)
        item_post_treatment(item)
        yield item


@Route.register
def list_programs(plugin, item_id, category_id, **kwargs):

    item = Listitem()
    item.label = plugin.localize(30717)
    item.set_callback(list_all_programs, item_id=item_id, category_id=category_id, page='1')
    item_post_treatment(item)
    yield item

    resp = urlquick.get(URL_CATEGORIES)
    json_parser = json.loads(resp.text)

    for category_datas in json_parser['data']['screen']['blocks']:
        if category_datas['widgets'][0]['playlist']['id'] == int(category_id):
            for program_datas in category_datas['widgets'][0]['playlist']['contents']:
                program_title = program_datas['name']
                program_image = program_datas['image']['url']
                program_plot = ''
                if 'short_description' in program_datas:
                    program_plot = program_datas['short_description']
                program_id = program_datas['id']

                item = Listitem()
                item.label = program_title
                item.art['thumb'] = item.art['landscape'] = program_image
                item.info['plot'] = program_plot
                if program_datas['type'] == 'series':
                    item.set_callback(
                        list_seasons, item_id=item_id, program_id=program_id)
                else:
                    item.set_callback(
                        list_movie_videos, item_id=item_id, program_id=program_id)
                item_post_treatment(item)
                yield item


@Route.register
def list_all_programs(plugin, item_id, category_id, page, **kwargs):

    resp = urlquick.get(URL_ALL_PROGRAMS_PER_CATEGORY % (category_id, page))
    json_parser = json.loads(resp.text)

    for program_datas in json_parser['data']:
        program_title = program_datas['name']
        program_image = program_datas['image']['url']
        program_plot = ''
        if 'short_description' in program_datas:
            program_plot = program_datas['short_description']
        program_id = program_datas['id']

        item = Listitem()
        item.label = program_title
        item.art['thumb'] = item.art['landscape'] = program_image
        item.info['plot'] = program_plot
        if program_datas['type'] == 'series':
            item.set_callback(
                list_seasons, item_id=item_id, program_id=program_id)
        else:
            item.set_callback(
                list_movie_videos, item_id=item_id, program_id=program_id)
        item_post_treatment(item)
        yield item

    if json_parser['pagination']['url']['next'] is not None:
        yield Listitem.next_page(item_id=item_id, category_id=category_id, page=str(int(page) + 1))


@Route.register
def list_seasons(plugin, item_id, program_id, **kwargs):

    resp = urlquick.get(URL_PROGRAM_ASSETS % (program_id, program_id))
    json_parser = json.loads(resp.text)

    for season_datas in json_parser['data']['screen']['blocks'][0]['widgets'][0]['playlist']['contents']:
        season_title = season_datas['name']
        season_slug = season_datas['slug']
        item = Listitem()
        item.label = season_title
        item.set_callback(
            list_season_videos, item_id=item_id, program_id=program_id, season_slug=season_slug)
        item_post_treatment(item)
        yield item


@Route.register
def list_season_videos(plugin, item_id, program_id, season_slug, **kwargs):

    resp = urlquick.get(URL_SEASON_VIDEOS % (program_id, season_slug))
    json_parser = json.loads(resp.text)

    for video_datas in json_parser['data']:
        video_name = video_datas['name']
        video_image = video_datas['image']['url']
        video_plot = video_datas['short_description']
        content_id = video_datas['id']
        video_id = video_datas['video']['streams']['id']

        item = Listitem()
        item.label = video_name
        item.art['thumb'] = item.art['landscape'] = video_image
        item.info['plot'] = video_plot
        item.set_callback(
            get_video_url, item_id=item_id, content_id=content_id, video_id=video_id)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item


@Route.register
def list_movie_videos(plugin, item_id, program_id, **kwargs):

    resp = urlquick.get(URL_PROGRAM_ASSETS % (program_id, program_id))
    json_parser = json.loads(resp.text)
    video_datas = json_parser['data']['asset']
    video_name = video_datas['name']
    video_image = video_datas['images']['poster']['url']
    video_plot = video_datas['short_description']
    video_id = video_datas['video']['streams']['id']

    item = Listitem()
    item.label = video_name
    item.art['thumb'] = item.art['landscape'] = video_image
    item.info['plot'] = video_plot
    item.set_callback(
        get_video_url, item_id=item_id, content_id=program_id, video_id=video_id)
    item_post_treatment(item, is_playable=True, is_downloadable=True)
    yield item


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  content_id,
                  video_id,
                  download_mode=False,
                  **kwargs):

    payload = {
        "device_layout": "web",
        "device_type": "web"
    }
    resp = urlquick.post(URL_BRIGHTCOVE_DATAS % (content_id, video_id),
                         data=payload,
                         max_age=-1)
    json_parser2 = json.loads(resp.text)

    data_account = json_parser2["data"]["stream"]["video_provider_details"]["account_id"]
    data_player = 'default'
    data_video_id = json_parser2["data"]["stream"]["url"]
    return resolver_proxy.get_brightcove_video_json(plugin, data_account,
                                                    data_player, data_video_id)


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    unix_time = time.time()
    resp = urlquick.get(URL_LIVE_DATAS % unix_time)
    json_parser = json.loads(resp.text)

    content_id = json_parser["data"]["blocks"][0]["widgets"][0]["playlist"]["contents"][0]["id"]
    stream_id = json_parser["data"]["blocks"][0]["widgets"][0]["playlist"]["contents"][0]["streams"][0]["id"]

    # Build PAYLOAD
    payload = {
        "device_layout": "web",
        "device_type": "web"
    }
    resp2 = urlquick.post(URL_BRIGHTCOVE_DATAS % (content_id, stream_id),
                          data=payload)
    json_parser2 = json.loads(resp2.text)

    data_account = json_parser2["data"]["stream"]["video_provider_details"]["account_id"]
    data_player = 'default'
    data_live_id = json_parser2["data"]["stream"]["url"]
    return resolver_proxy.get_brightcove_video_json(plugin, data_account,
                                                    data_player, data_live_id)
