# -*- coding: utf-8 -*-
# Copyright: (c) 2019, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
from datetime import date
import json
import re

from codequick import Listitem, Resolver, Route, Script
import urlquick

from resources.lib import download, web_utils
from resources.lib.menu_utils import item_post_treatment


URL_ROOT = 'https://www.equidia.fr'

URL_API = "https://equidia-vodce-players.hexaglobe.net"

URL_LIVE_DATAS = URL_API + '/mf_data/%s.json'

URL_API_SEARCH = "https://api.equidia.fr/api/public"

URL_IMAGE = URL_API_SEARCH + '/media/article_header/%s'
# ImageId

URL_REPLAY_DATAS = 'https://api.equidia.fr/api/public/videos-store/player/%s'
# VideoId
URL_MOBILE_API = 'https://api.equidia.fr/api/public/racing/equidia-mobileapp-ios-1/%s'

CATEGORIES_VIDEOS_EQUIDIA = {
    '/search/emissions': Script.localize(20343),  # TV shows
    '/search/courses': Script.localize(30726)  # Races
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
    for category_context, category_title in list(CATEGORIES_VIDEOS_EQUIDIA.items(
    )):
        category_url = URL_API_SEARCH + category_context
        item = Listitem()
        if 'courses' in category_context:
            next_value = 'list_videos_courses'
        else:
            next_value = 'list_videos_emissions'
        item.label = category_title
        item.set_callback(eval(next_value),
                          item_id=item_id,
                          category_url=category_url,
                          page='0')
        item_post_treatment(item)
        yield item


@Route.register
def list_videos_emissions(plugin, item_id, category_url, page, **kwargs):

    params = {
        'range': '[%s,%s]' % (page, str(int(page) + 11))
    }
    resp = urlquick.post(category_url, params=params)
    json_parser = json.loads(resp.text)

    for video_datas in json_parser["results"]:
        video_title = video_datas["name"]
        video_image = URL_IMAGE % video_datas["episode"]["media"]["slug"]
        video_url = URL_ROOT + '/programmes/' + \
            video_datas["program"]["slug"] + '/' + video_datas["episode"]["slug"]

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = item.art['landscape'] = video_image

        item.set_callback(get_video_emission_url,
                          item_id=item_id,
                          video_url=video_url)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item

    # More videos...
    yield Listitem.next_page(item_id=item_id,
                             category_url=category_url,
                             page=str(int(page) + 12))


@Route.register
def list_videos_courses(plugin, item_id, category_url, page, **kwargs):

    params = {
        'range': '[%s,%s]' % (page, str(int(page) + 11))
    }
    resp = urlquick.post(category_url, params=params)
    json_parser = json.loads(resp.text)

    for video_datas in json_parser["results"]:
        video_title = 'R%s - C%s - %s' % (
            video_datas["reunion"]["num_reunion"], video_datas["num_course_pmu"], video_datas["libcourt_prix_course"])
        video_image = ''
        if 'photo' in video_datas:
            video_image = URL_IMAGE % video_datas["photo"]["slug"]
        video_url = URL_ROOT + '/courses/%s/R%s/C%s' % (
            video_datas["reunion"]["date_reunion"], video_datas["reunion"]["num_reunion"], video_datas["num_course_pmu"])

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = item.art['landscape'] = video_image

        item.set_callback(get_video_course_url,
                          item_id=item_id,
                          video_url=video_url)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item

    # More videos...
    yield Listitem.next_page(item_id=item_id,
                             category_url=category_url,
                             page=str(int(page) + 12))


@Resolver.register
def get_video_emission_url(plugin,
                           item_id,
                           video_url,
                           download_mode=False,
                           **kwargs):

    resp = urlquick.get(video_url,
                        headers={'User-Agent': web_utils.get_random_ua()},
                        max_age=-1)
    video_id = re.compile(r'name_no_extention\"\:\"(.*?)[\?\"]').findall(
        resp.text)[0]
    resp2 = urlquick.get(URL_REPLAY_DATAS % video_id, max_age=-1)
    json_parser2 = json.loads(resp2.text)
    resp3 = urlquick.get(json_parser2["video_url"], max_age=-1)
    json_parser3 = json.loads(resp3.text)
    if download_mode:
        return download.download_video(json_parser3["master"])
    return json_parser3["master"]


@Resolver.register
def get_video_course_url(plugin,
                         item_id,
                         video_url,
                         download_mode=False,
                         **kwargs):

    resp = urlquick.get(video_url,
                        headers={'User-Agent': web_utils.get_random_ua()},
                        max_age=-1)
    video_id = re.compile(r'video_course_nom\"\:\"(.*?)[\?\"]').findall(
        resp.text)[0]
    resp2 = urlquick.get(URL_REPLAY_DATAS % video_id, max_age=-1)
    json_parser2 = json.loads(resp2.text)
    resp3 = urlquick.get(json_parser2["video_url"], max_age=-1)
    json_parser3 = json.loads(resp3.text)
    if download_mode:
        return download.download_video(json_parser3["master"])
    return json_parser3["master"]


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    if item_id == 'equidia-racing':
        temp_id = item_id + kwargs.get('language', Script.setting["equidia-racing.language"])
    else:
        temp_id = item_id

    resp = urlquick.get(
        URL_MOBILE_API % temp_id,
        headers={
            "User-Agent": "Equidia/6036 CFNetwork/1220.1 Darwin/20.3.0",
            "Referer": "https://fr.equidia.app/"
        },
        max_age=-1)
    json_parser2 = json.loads(resp.text)
    if "primary" in json_parser2:
        return json_parser2["primary"]
    else:
        return json_parser2["stream_url_pri"]
