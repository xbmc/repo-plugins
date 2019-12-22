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

from builtins import str
from codequick import Route, Resolver, Listitem, utils, Script

from resources.lib.labels import LABELS

from resources.lib import web_utils
from resources.lib import resolver_proxy
from resources.lib.listitem_utils import item_post_treatment, item2dict

import json
import re
import urlquick

# TO DO
# Rework Date/AIred

URL_ROOT = 'https://www.lequipe.fr'

URL_LIVE = URL_ROOT + '/lachainelequipe/'

URL_INFO_STREAM_LIVE = URL_ROOT + '/js/app.%s.js'

URL_API_LEQUIPE = URL_ROOT + '/equipehd/applis/filtres/videosfiltres.json'


def replay_entry(plugin, item_id, **kwargs):
    """
    First executed function after replay_bridge
    """
    return list_programs(plugin, item_id)


@Route.register
def list_programs(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_API_LEQUIPE)
    json_parser = json.loads(resp.text)

    for programs in json_parser['filtres_vod']:
        if 'missions' in programs['titre']:
            for program in programs['filters']:
                program_name = program['titre']
                program_url = program['filters'].replace('1.json', '%s.json')

                item = Listitem()
                item.label = program_name
                item.set_callback(list_videos,
                                  item_id=item_id,
                                  program_url=program_url,
                                  page='1')
                item_post_treatment(item)
                yield item


@Route.register
def list_videos(plugin, item_id, program_url, page, **kwargs):

    resp = urlquick.get(program_url % page)
    json_parser = json.loads(resp.text)

    for video_datas in json_parser['videos']:

        title = video_datas['titre']
        img = video_datas['src_tablette_retina']
        duration = video_datas['duree']
        video_id = video_datas['lien_dm'].split('//')[1]

        item = Listitem()
        item.label = title
        item.art['thumb'] = img
        item.info['duration'] = duration

        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_label=LABELS[item_id] + ' - ' + item.label,
                          video_id=video_id)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item

    if int(page) < int(json_parser['nb_total_pages']):
        yield Listitem.next_page(item_id=item_id,
                                 program_url=program_url,
                                 page=str(int(page) + 1))


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_id,
                  download_mode=False,
                  video_label=None,
                  **kwargs):

    return resolver_proxy.get_stream_dailymotion(plugin, video_id,
                                                 download_mode, video_label)


def live_entry(plugin, item_id, item_dict, **kwargs):
    return get_live_url(plugin, item_id, item_id.upper(), item_dict)


@Resolver.register
def get_live_url(plugin, item_id, video_id, item_dict, **kwargs):

    resp = urlquick.get(URL_LIVE,
                        headers={'User-Agent': web_utils.get_random_ua()},
                        max_age=-1)
    js_live_id = re.compile(r'\/js\/app\.(.*?)\.',
                            re.DOTALL).findall(resp.text)[0]
    resp2 = urlquick.get(URL_INFO_STREAM_LIVE % js_live_id,
                         headers={'User-Agent': web_utils.get_random_ua()},
                         max_age=-1)
    live_id = re.compile(r'channelLiveDmId\:\"(.*?)\"',
                         re.DOTALL).findall(resp2.text)[0]
    return resolver_proxy.get_stream_dailymotion(plugin, live_id, False)
