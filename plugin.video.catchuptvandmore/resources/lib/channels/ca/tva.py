# -*- coding: utf-8 -*-
# Copyright: (c) 2018, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
from builtins import str
import json
import re

import inputstreamhelper
from codequick import Listitem, Resolver, Route
import urlquick

from resources.lib import resolver_proxy, web_utils
from resources.lib.addon_utils import get_item_media_path
from resources.lib.kodi_utils import get_selected_item_art, get_selected_item_label, get_selected_item_info, INPUTSTREAM_PROP
from resources.lib.menu_utils import item_post_treatment


# TO DO
# Fix download mode when video is not DRM protected

URL_ROOT = 'https://www.qub.ca'

URL_API = URL_ROOT + '/proxy/pfu/content-delivery-service/v1'

URL_CATEGORIES = URL_API + '/entities?slug=/%s'

URL_LIVE = URL_ROOT + '/tvaplus/%s/en-direct'

URL_INFO_STREAM = URL_ROOT + '/tvaplus%s'

URL_BRIGHTCOVE_POLICY_KEY = 'http://players.brightcove.net/%s/%s_default/index.min.js'
# AccountId, PlayerId

URL_BRIGHTCOVE_VIDEO_JSON = 'https://edge.api.brightcove.com/'\
                            'playback/v1/accounts/%s/videos/%s'
# AccountId, VideoId


@Route.register
def tva_root(plugin, **kwargs):

    # (item_id, label, thumb, fanart)
    channels = [
        ('tva', 'TVA', 'tva.png', 'tva_fanart.jpg'),
        ('addiktv', 'addikTV', 'addiktv.png', 'addiktv_fanart.jpg'),
        ('casa', 'Casa', 'casa.png', 'casa_fanart.jpg'),
        ('evasion', 'Evasion', 'evasion.png', 'evasion_fanart.jpg'),
        ('moi-et-cie', 'MOI ET CIE', 'moietcie.png', 'moietcie_fanart.jpg'),
        ('prise2', 'PRISE2', 'prise2.png', 'prise2_fanart.jpg'),
        ('yoopa', 'Yoopa', 'yoopa.png', 'yoopa_fanart.jpg'),
        ('zeste', 'Zeste', 'zeste.png', 'zeste_fanart.jpg'),
        ('tva-sports', 'TVA Sports', 'tvasports.png', 'tvasports_fanart.jpg'),
        ('lcn', 'LCN', 'lcn.png', 'lcn_fanart.jpg')
    ]

    for channel_infos in channels:
        item = Listitem()
        item.label = channel_infos[1]
        item.art["thumb"] = get_item_media_path('channels/ca/' + channel_infos[2])
        item.art["fanart"] = get_item_media_path('channels/ca/' + channel_infos[3])
        item.set_callback(list_categories, channel_infos[0])
        item_post_treatment(item)
        yield item


@Route.register
def list_categories(plugin, item_id, **kwargs):
    """
    Build categories listing
    - Tous les programmes
    - Séries
    - Informations
    - ...
    """
    resp = urlquick.get(URL_CATEGORIES % item_id)
    json_parser = json.loads(resp.text)

    for category_datas in json_parser['associatedEntities']:
        if 'name' in category_datas:
            category_name = category_datas['name']

            item = Listitem()
            item.label = category_name
            item.set_callback(
                list_programs, item_id=item_id, category_name=category_name, next_url=None)
            item_post_treatment(item)
            yield item


@Route.register
def list_programs(plugin, item_id, category_name, next_url, **kwargs):

    if next_url is None:
        resp = urlquick.get(URL_CATEGORIES % item_id)
        json_parser = json.loads(resp.text)

        for category_datas in json_parser['associatedEntities']:
            if 'name' in category_datas:
                if category_name == category_datas['name']:
                    for program_datas in category_datas['associatedEntities']:
                        program_name = program_datas['label']
                        program_image = program_datas['mainImage']['url']
                        program_slug = program_datas['slug']

                        item = Listitem()
                        item.label = program_name
                        item.art['thumb'] = item.art['landscape'] = program_image
                        item.set_callback(
                            list_seasons, item_id=item_id, program_slug=program_slug)
                        item_post_treatment(item)
                        yield item

                    if 'next' in category_datas:
                        yield Listitem.next_page(
                            item_id=item_id, category_name=category_name, next_url=URL_API + category_datas['next'])
    else:
        resp = urlquick.get(next_url)
        json_parser = json.loads(resp.text)

        for program_datas in json_parser['associatedEntities']:
            program_name = program_datas['label']
            program_image = program_datas['mainImage']['url']
            program_slug = program_datas['slug']

            item = Listitem()
            item.label = program_name
            item.art['thumb'] = item.art['landscape'] = program_image
            item.set_callback(
                list_seasons, item_id=item_id, program_slug=program_slug)
            item_post_treatment(item)
            yield item

        if 'next' in json_parser:
            yield Listitem.next_page(
                item_id=item_id, category_name=category_name, next_url=URL_API + category_datas['next'])


@Route.register
def list_seasons(plugin, item_id, program_slug, **kwargs):

    resp = urlquick.get(URL_API + '/entities?slug=%s' % program_slug)
    json_parser = json.loads(resp.text)

    if 'seasons' in json_parser['knownEntities']:
        for season_datas in json_parser['knownEntities']['seasons']['associatedEntities']:

            season_name = json_parser['knownEntities']['seasons']['name'] + ' ' + str(season_datas['seasonNumber'])
            season_number = str(season_datas['seasonNumber'])

            item = Listitem()
            item.label = season_name
            item.set_callback(
                list_videos_categories, item_id=item_id, program_slug=program_slug, season_number=season_number)
            item_post_treatment(item)
            yield item

        season_name = json_parser['name']
        season_number = '-1'
        item = Listitem()
        item.label = season_name
        item.set_callback(
            list_videos_categories, item_id=item_id, program_slug=program_slug, season_number=season_number)
        item_post_treatment(item)
        yield item


@Route.register
def list_videos_categories(plugin, item_id, program_slug, season_number, **kwargs):

    resp = urlquick.get(URL_API + '/entities?slug=%s' % program_slug)
    json_parser = json.loads(resp.text)

    if season_number == '-1':
        for video_category_datas in json_parser['associatedEntities']:
            if 'associatedEntities' in video_category_datas:
                if len(video_category_datas['associatedEntities']) > 0:
                    video_category_name = video_category_datas['name']
                    video_category_slug = video_category_datas['slug']

                    item = Listitem()
                    item.label = video_category_name
                    item.set_callback(
                        list_videos, item_id=item_id, video_category_slug=video_category_slug)
                    item_post_treatment(item)
                    yield item
    else:
        for season_datas in json_parser['knownEntities']['seasons']['associatedEntities']:
            if season_number == str(season_datas['seasonNumber']):
                for video_category_datas in season_datas['associatedEntities']:
                    if len(video_category_datas['associatedEntities']) > 0:
                        video_category_name = video_category_datas['name']
                        video_category_slug = video_category_datas['slug']

                        item = Listitem()
                        item.label = video_category_name
                        item.set_callback(
                            list_videos, item_id=item_id, video_category_slug=video_category_slug)
                        item_post_treatment(item)
                        yield item


@Route.register
def list_videos(plugin, item_id, video_category_slug, **kwargs):

    resp = urlquick.get(URL_API + '/entities?slug=%s' % video_category_slug)
    json_parser = json.loads(resp.text)

    for video_datas in json_parser['associatedEntities']:
        video_name = video_datas['secondaryLabel'] + ' - ' + video_datas['label']
        video_image = video_datas['mainImage']['url']
        video_plot = ''
        if 'description' in video_datas:
            video_plot = video_datas['description']
        video_duration = video_datas['durationMillis'] / 1000
        video_slug = video_datas['slug']

        item = Listitem()
        item.label = video_name
        item.art['thumb'] = item.art['landscape'] = video_image
        item.info['plot'] = video_plot
        item.info['duration'] = video_duration
        item.set_callback(
            get_video_url, item_id=item_id, video_slug=video_slug)
        item_post_treatment(item, is_playable=True, is_downloadable=False)
        yield item

    if 'next' in json_parser:
        yield Listitem.next_page(
            item_id=item_id, video_category_slug=json_parser['next'])


# BRIGHTCOVE Part
def get_brightcove_policy_key(data_account, data_player):
    """Get policy key"""
    file_js = urlquick.get(URL_BRIGHTCOVE_POLICY_KEY %
                           (data_account, data_player))
    return re.compile('policyKey:"(.+?)"').findall(file_js.text)[0]


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_slug,
                  download_mode=False,
                  **kwargs):

    is_helper = inputstreamhelper.Helper('mpd', drm='widevine')
    if not is_helper.check_inputstream():
        return False

    resp = urlquick.get(URL_INFO_STREAM % video_slug)
    data_account = re.compile(
        r'data-accound\=\"(.*?)\"').findall(resp.text)[0]
    data_player = re.compile(
        r'data-player\=\"(.*?)\"').findall(resp.text)[0]
    data_video_id = re.compile(
        r'\"referenceId\":\"(.*?)\"').findall(resp.text)[0]

    # Method to get JSON from 'edge.api.brightcove.com'
    resp = urlquick.get(
        URL_BRIGHTCOVE_VIDEO_JSON % (data_account, "ref:%s" % data_video_id),
        headers={
            'User-Agent': web_utils.get_random_ua(),
            'Accept': 'application/json;pk=%s' % (get_brightcove_policy_key(data_account, data_player)),
        })
    json_parser = json.loads(resp.text)

    video_url = ''
    licence_url = ''
    is_protected_drm = False
    if 'sources' in json_parser:
        for url in json_parser["sources"]:
            if 'src' in url:
                if 'manifest.mpd' in url["src"]:
                    video_url = url["src"]
                    if 'key_systems' in url:
                        licence_url = url['key_systems']['com.widevine.alpha']['license_url']
                        is_protected_drm = True
    else:
        if json_parser[0]['error_code'] == "ACCESS_DENIED":
            plugin.notify('ERROR', plugin.localize(30713))
            return False

    if video_url == '':
        return False

    item = Listitem()
    item.path = video_url
    item.label = get_selected_item_label()
    item.art.update(get_selected_item_art())
    item.info.update(get_selected_item_info())
    item.property[INPUTSTREAM_PROP] = 'inputstream.adaptive'
    item.property['inputstream.adaptive.manifest_type'] = 'mpd'
    if is_protected_drm:
        item.property['inputstream.adaptive.license_type'] = 'com.widevine.alpha'
        item.property[
            'inputstream.adaptive.license_key'] = licence_url + '|Content-Type=&User-Agent=Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3041.0 Safari/537.36|R{SSM}|'
    return item


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_LIVE % item_id)
    video_url = re.compile(r'videoSourceUrl\"\:\"(.*?)\"').findall(resp.text)[0]

    return resolver_proxy.get_stream_with_quality(plugin, video_url, manifest_type="hls")
