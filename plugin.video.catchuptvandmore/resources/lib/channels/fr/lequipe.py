# -*- coding: utf-8 -*-
# Copyright: (c) 2017, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
from builtins import str
import json
import re

from codequick import Listitem, Resolver, Route, Script
import urlquick

from resources.lib import resolver_proxy, web_utils
from resources.lib.menu_utils import item_post_treatment
import xbmcgui

# TO DO
# Rework Date/AIred
URL_ROOT = 'https://www.lequipe.fr'

URL_LIVE = URL_ROOT + '/lachainelequipe/'

URL_API_LEQUIPE = URL_ROOT + '/equipehd/applis/filtres/videosfiltres.json'


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
        item.art['thumb'] = item.art['landscape'] = img
        item.info['duration'] = duration

        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_id=video_id)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item

    if int(page) < int(json_parser['nb_total_pages']):
        yield Listitem.next_page(item_id=item_id,
                                 program_url=program_url,
                                 page=str(int(page) + 1))


@Resolver.register
def get_video_url(plugin, item_id, video_id, download_mode=False, **kwargs):

    return resolver_proxy.get_stream_dailymotion(plugin, video_id, download_mode)


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    if item_id == 'lequipelive':
        resp = urlquick.get("https://www.lequipe.fr/directs", headers={'user-agent': web_utils.get_random_ua()}, max_age=-1)
        live_id = re.compile(r'<article.+?<a href="(.+?)".+?alt="(.+?)"').findall(resp.text)
        list_url = []
        list_q = []

        for a in live_id:
            list_url.append(a[0])
            list_q.append(a[1])

        if len(list_url) == 0:
            return ''
        if len(list_url) == 1:
            return list_url[0]

        ret = xbmcgui.Dialog().select(Script.localize(30174), list_q)
        if ret > -1:
            live_id = list_url[ret]
        resp = urlquick.get(live_id, headers={'user-agent': web_utils.get_random_ua()}, max_age=-1)
        live_id = re.compile(r'"EmbedUrl": "(.+?)",').findall(resp.text)[0].rsplit('/', 1)[-1]

    else:
        resp = urlquick.get(URL_LIVE, headers={'User-Agent': web_utils.get_random_ua()}, max_age=-1)
        live_id = re.compile(r'video-id\=\"(.*?)\"', re.DOTALL).findall(resp.text)[0]

    return resolver_proxy.get_stream_dailymotion(plugin, live_id, False)
