# -*- coding: utf-8 -*-
# Copyright: (c) JUL1EN094, SPM, SylvainCecchetto
# Copyright: (c) 2016, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import json

from codequick import Listitem, Resolver, Route, utils, Script
import urlquick

from resources.lib import resolver_proxy, web_utils
from resources.lib.menu_utils import item_post_treatment

LANG = Script.setting['france24.language']
TOKEN_APP = '66b85dad-3ad5-40f3-ab32-2305fc2357ea'
URL_API = utils.urljoin_partial('https://apis.france24.com')


@Route.register
def root_catchup_tv(plugin, item_id, **kwargs):
    # http://apis.france24.com/products/get_product/78dcf358-9333-4fb2-a035-7b91e9705b13?token_application=66b85dad-3ad5-40f3-ab32-2305fc2357ea
    root_json_url = 'products/get_product/78dcf358-9333-4fb2-a035-7b91e9705b13'
    root_json_r = urlquick.get(URL_API(root_json_url),
                               headers={'User-Agent': web_utils.get_random_ua()},
                               params={'token_application': TOKEN_APP})
    json_root = json.loads(root_json_r.text)

    try:
        json_languages = json_root['result']['list']['languages']
    except Exception:
        yield False

    # code in JSON: FR, EN, ES and AR
    for json_language in json_languages:
        if json_language['code'] == LANG:
            json_tv = json_language['tv']

            if 'direct_tv' in json_tv:
                item = Listitem()
                item.label = json_tv['direct_tv']['label']
                guid = json_tv['direct_tv']['guid']
                item.info['plot'] = json_tv['direct_tv']['description']
                item.set_callback(list_direct_tv_jts,
                                  item_id=item_id,
                                  guid=guid)
                item_post_treatment(item)
                yield item

            if 'videos' in json_tv:
                item = Listitem()
                item.label = json_tv['videos']['label']
                guid = json_tv['videos']['guid']
                item.info['plot'] = json_tv['videos']['description']
                item.set_callback(list_videos, item_id=item_id, guid=guid)
                item_post_treatment(item)
                yield item

            if 'shows' in json_tv:
                json_shows = json_tv['shows']
                if 'shows_last_edition' in json_shows:
                    item = Listitem()
                    item.label = json_shows['shows_last_edition']['label']
                    guid = json_shows['shows_last_edition']['guid']
                    item.info['plot'] = json_shows['shows_last_edition'][
                        'description']
                    item.set_callback(list_last_edition,
                                      item_id=item_id,
                                      guid=guid)
                    item_post_treatment(item)
                    yield item

                if 'shows_all' in json_shows:
                    if 'show_editions' in json_shows:

                        item = Listitem()
                        item.label = json_shows['shows_all']['label']
                        guid = json_shows['shows_all']['guid']
                        item.info['plot'] = json_shows['shows_all'][
                            'description']
                        item.set_callback(
                            list_all_programs,
                            item_id=item_id,
                            guid=guid,
                            guid_program=json_shows['show_editions']['guid'])
                        item_post_treatment(item)
                        yield item

#                if 'show_editions' in json_shows:
#                    menus_to_add.append(json_shows['show_editions'])


@Route.register
def list_direct_tv_jts(plugin, item_id, guid, **kwargs):
    json_url = 'products/get_product/%s' % guid
    json_r = urlquick.get(URL_API(json_url),
                          params={'token_application': TOKEN_APP},
                          headers={'User-agent': web_utils.get_ua()})
    json_v = json.loads(json_r.text)
    try:
        json_channels = json_v['result']['channels']
    except Exception:
        yield False

    for json_channel in json_channels:
        code = json_channel['code']
        if code == 'direct_f24':
            continue
        if code == 'live_audio':
            continue
        label = json_channel['title']

#        for json_image in json_channel['images']['formats']:
#            if json_image['code'] == '1920x1080':
#                item.art['fanart'] = json_image['url']
#            if json_image['code'] == '720x405':
#                item.art['thumb'] = item.art['landscape'] = json_image['url'

        youtube_playlist_id = ''
        for json_video in json_channel['videos']:
            for json_format in json_video['formats']:
                if 'youtube_playlist_id' in json_format:
                    youtube_playlist_id = json_format['youtube_playlist_id']

        # print youtube_playlist_id
        yield Listitem.youtube(youtube_playlist_id, label=label)


@Route.register
def list_videos(plugin, item_id, guid, page=1, **kwargs):
    json_url = 'products/get_product/%s' % guid
    json_r = urlquick.get(URL_API(json_url),
                          params={
                              'token_application': TOKEN_APP,
                              'page': page},
                          headers={'User-agent': web_utils.get_ua()})
    json_v = json.loads(json_r.text)
    try:
        json_list = json_v['result']['list']
    except Exception:
        yield False

    for json_video in json_list:
        item = Listitem()
        item.label = json_video['title']
        youtube_id = json_video['youtube_id']

        try:
            for json_image in json_video['images']['formats']:
                item.art['fanart'] = json_image['url']
                item.art['thumb'] = item.art['landscape'] = json_image['url']
        except Exception:
            pass

        item.set_callback(get_video_url,
                          item_id=item_id,
                          youtube_id=youtube_id)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item

    last_page = json_v['result']['last_page']
    if page != last_page:
        yield Listitem.next_page(item_id=item_id, guid=guid, page=page + 1)


@Route.register
def list_last_edition(plugin, item_id, guid, **kwargs):
    json_url = 'products/get_product/%s' % guid
    json_r = urlquick.get(URL_API(json_url),
                          params={'token_application': TOKEN_APP},
                          headers={'User-agent': web_utils.get_ua()})
    json_v = json.loads(json_r.text)
    try:
        json_list = json_v['result']['list']
    except Exception:
        yield False

    for json_video in json_list:
        item = Listitem()
        item.label = json_video['title']
        if 'subtitle' in json_video:
            item.label = item.label + ' — ' + json_video['subtitle']

        if 'intro':
            item.info['plot'] = json_video['intro'].replace('<p>', '').replace(
                '</p>', '')
        youtube_id = json_video['main_video'][0]['youtube_id']

        try:
            for json_image in json_video['images']['formats']:
                item.art['fanart'] = json_image['url']
                item.art['thumb'] = item.art['landscape'] = json_image['url']
        except Exception:
            pass

        item.set_callback(get_video_url,
                          item_id=item_id,
                          youtube_id=youtube_id)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item


@Route.register
def list_all_programs(plugin, item_id, guid, guid_program, page=1, **kwargs):
    json_url = 'products/get_product/%s' % guid
    json_r = urlquick.get(URL_API(json_url),
                          params={'token_application': TOKEN_APP},
                          headers={'User-agent': web_utils.get_ua()})
    json_v = json.loads(json_r.text)
    try:
        json_list = json_v['result']['list']
    except Exception:
        yield False

    for json_video in json_list:
        item = Listitem()
        item.label = json_video['title']
        if 'subtitle' in json_video:
            item.label = item.label + ' — ' + json_video['subtitle']

        if 'intro':
            item.info['plot'] = json_video['intro'].replace('<p>', '').replace(
                '</p>', '')

        try:
            for json_image in json_video['images']['formats']:
                item.art['fanart'] = json_image['url']
                item.art['thumb'] = item.art['landscape'] = json_image['url']
        except Exception:
            pass

        nid = json_video['nid']

        item.set_callback(list_program_video,
                          item_id=item_id,
                          nid=nid,
                          guid_program=guid_program)
        item_post_treatment(item)
        yield item

    last_page = json_v['result']['last_page']
    if page != last_page:
        yield Listitem.next_page(item_id=item_id, guid=guid, page=page + 1)


@Route.register
def list_program_video(plugin, item_id, nid, guid_program, page=1, **kwargs):
    json_url = 'products/get_product/%s' % guid_program
    json_r = urlquick.get(URL_API(json_url),
                          params={
                              'token_application': TOKEN_APP,
                              'nid': nid,
                              'page': page},
                          headers={'User-agent': web_utils.get_ua()})
    json_v = json.loads(json_r.text)

    try:
        json_list = json_v['result']['list']
    except Exception:
        yield False

    for json_video in json_list:
        if len(json_video['main_video']) > 0:
            item = Listitem()
            item.label = json_video['title']
            if 'subtitle' in json_video:
                item.label = item.label + ' — ' + json_video['subtitle']

            if 'intro':
                item.info['plot'] = json_video['intro'].replace('<p>',
                                                                '').replace(
                                                                    '</p>', '')
            youtube_id = json_video['main_video'][0]['youtube_id']

            try:
                for json_image in json_video['images']['formats']:
                    item.art['fanart'] = json_image['url']
                    item.art['thumb'] = item.art['landscape'] = json_image['url']
            except Exception:
                pass

            item.set_callback(
                get_video_url,
                item_id=item_id,
                youtube_id=youtube_id)
            item_post_treatment(item, is_playable=True, is_downloadable=True)
            yield item

    last_page = json_v['result']['last_page']
    if page != last_page:
        yield Listitem.next_page(item_id=item_id,
                                 nid=nid,
                                 guid_program=guid_program,
                                 page=page + 1)


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  youtube_id,
                  download_mode=False,
                  **kwargs):
    return resolver_proxy.get_stream_youtube(plugin, youtube_id, download_mode)


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    channels = {"FR": "gxG3pdKvlIs", "AR": "8BZpOolYLUA", "EN": "h3MuIUNCCzI", "ES": "XDJPzMznAjU"}
    final_language = kwargs.get('language', LANG)
    return resolver_proxy.get_stream_youtube(plugin, channels[final_language])
