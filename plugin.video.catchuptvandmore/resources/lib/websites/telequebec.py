# -*- coding: utf-8 -*-
# Copyright: (c) 2018, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import json
import re
import html

from codequick import Listitem, Resolver, Route
import urlquick

from resources.lib import download
from resources.lib import web_utils, resolver_proxy

from resources.lib.menu_utils import item_post_treatment

# TODO fix module, 404 error on url root


URL_SITE = 'https://squat.api.telequebec.tv/v1'

URL_ROOT = URL_SITE + '/init'

URL_IMAGES = 'https://images.tele.quebec/squat'

URL_VIDEOS = URL_SITE + '/chaines/%s/onglets/%s/videos'

URL_IMAGES = 'https://images.tele.quebec/squat'

URL_STREAM = 'https://mnmedias.api.telequebec.tv/api/v4/player/%s'

VODPLAYER = 'https://player.telequebec.tv/players/latest/js/vodplayer.min.js'

GENERIC_HEADERS = {'User-Agent': web_utils.get_random_ua()}


@Route.register
def website_root(plugin, item_id, **kwargs):
    """Add modes in the listing"""
    resp = urlquick.get(URL_ROOT, headers=GENERIC_HEADERS, max_age=-1)
    channels_list = json.loads(resp.text)

    for channel in channels_list['chaines']:
        title = channel['titre']
        root_image = channel['images']
        for picture in root_image:
            if 'emplacement' in picture:
                if picture['emplacement'] == 'profil_carre':
                    image = picture['path'] + picture['declinaisons'][0]['file']
        description = html.unescape(channel['description'].replace('<p>', '').replace('</p>', ''))
        count = channel['id']
        for onglets in channel['onglets']:
            if 'typeOnglet' in onglets:
                if onglets['typeOnglet'] == 'videos':
                    if 'episodes' in onglets['permalink'] or 'videos' in onglets['permalink']:
                        onglet = onglets['id']

        item = Listitem()
        item.label = title
        item.info['plot'] = description
        item.art['fanart'] = item.art['thumb'] = URL_IMAGES + image
        item.set_callback(list_videos, count=count, onglet=onglet)
        item_post_treatment(item)
        yield item


@Route.register
def list_videos(plugin, count, onglet, **kwargs):
    params = {
        'publiableOnly': 'true',
        'count': '500',
        'after': 'null'
    }
    url = URL_VIDEOS % (count, onglet)
    resp = urlquick.get(url, params=params, headers=GENERIC_HEADERS, max_age=-1)
    episodes_list = json.loads(resp.text)

    if 'carrousels' in episodes_list:
        episodes = episodes_list['carrousels']
        for episode in episodes:
            item = Listitem()
            item.label = episode['type'] + ' ' + str(episode['id'])
            item.set_callback(list_parts_episodes, episode=episode)
            item_post_treatment(item)
            yield item
    else:
        for episode in episodes_list:
            title = episode['titre']
            image = episode['imageUrlTemplate'].replace('{w}', '640').replace('{h}', '360')
            description = episode['description']
            source_id = episode['sourceId']

            item = Listitem()
            item.label = title
            item.info['plot'] = description
            item.art['fanart'] = item.art['thumb'] = image
            item.set_callback(get_video_url, source=source_id)
            item_post_treatment(item)
            yield item


@Route.register
def list_parts_episodes(plugin, episode, **kwargs):
    for part in episode['items']:
        title = part['titre']
        image = part['imageUrlTemplate'].replace('{w}', '640').replace('{h}', '360')
        description = part['description']
        source_id = part['sourceId']

        item = Listitem()
        item.label = title
        item.info['plot'] = description
        item.art['fanart'] = item.art['thumb'] = image
        item.set_callback(get_video_url, source=source_id)
        item_post_treatment(item)
        yield item


@Resolver.register
def get_video_url(plugin, source, download_mode=False, **kwargs):
    """Get video URL and start video player"""

    resp = urlquick.get(URL_STREAM % source, headers=GENERIC_HEADERS, max_age=-1)
    json_parser = json.loads(resp.text)

    for stream in json_parser['streamInfos']:
        if 'source' in stream:
            if stream['canPlay']:
                data_video_id = stream['sourceId']

    resp = urlquick.get(VODPLAYER, headers=GENERIC_HEADERS, max_age=-1)
    vodplayer = resp.text

    data_account = re.compile('https://players.brightcove.net\/(.*?)\/').findall(vodplayer)[0]
    data_player = re.compile('this\;\_t\(r\,\"(.*?)\"').findall(vodplayer)[0]

    return resolver_proxy.get_brightcove_video_json(plugin, data_account, data_player, data_video_id, download_mode=download_mode)
