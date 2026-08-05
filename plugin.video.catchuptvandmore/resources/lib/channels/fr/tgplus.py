# -*- coding: utf-8 -*-
# Copyright: (c) 2019, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import re

from codequick import Listitem, Resolver, Route
import urlquick
import urllib.request
import http.cookiejar
import json

from resources.lib import resolver_proxy, web_utils
from resources.lib.menu_utils import item_post_treatment


# TODO
# Add Replay

URL_ROOT = ":https://tgplus.fr"

URL_LIVE = URL_ROOT + '/direct.html'

URL_ROOT_LIVE = 'https://tgplus.fr'

URL_LIVE_PLAYER = URL_ROOT_LIVE + '/direct'

URL_REPLAY = URL_ROOT + '/replay.html'

URL_VIDEOS = URL_ROOT + '/views/htmlFragments/replayDetail_pages.php?page=%s&elementsPerPage=10&idEmission=%s'
# Page, Category_Id

URL_KICK_INFO = 'https://kick.com/api/v2/channels/telegrenoble/info'

GENERIC_HEADERS = {"User-Agent": web_utils.get_random_ua()}


@Route.register
def list_categories(plugin, item_id, **kwargs):
    """
    Build categories listing
    - Tous les programmes
    - Séries
    - Informations
    - ...
    """
    resp = urlquick.get(URL_REPLAY, headers=GENERIC_HEADERS)
    root = resp.parse()

    for category_datas in root.iterfind(".//div[@class='emission black']"):
        category_name = category_datas.find('.//a').text
        category_image = URL_ROOT + '/' + category_datas.find('.//img').get('src')
        category_plot = category_datas.find(".//div[@class='description']").text
        category_id = re.compile(r'fichiers\/emissions\/(.*?)\/').findall(category_image)[0]

        item = Listitem()
        item.label = category_name
        item.art['thumb'] = item.art['landscape'] = category_image
        item.info['plot'] = category_plot
        item.set_callback(list_videos, category_id=category_id, page='1')
        item_post_treatment(item)
        yield item


@Route.register
def list_videos(plugin, category_id, page, **kwargs):

    resp = urlquick.get(URL_VIDEOS % (page, category_id), headers=GENERIC_HEADERS)
    root = resp.parse()

    for video_datas in root.iterfind(".//div[@class='replay']"):
        video_title = video_datas.find('.//a').get('title')
        video_image = video_datas.find('.//img').get('src')
        video_plot = video_datas.find(".//div[@class='description']").text
        video_url = URL_ROOT + '/' + video_datas.find('.//a').get('href')

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = item.art['landscape'] = video_image
        item.info['plot'] = video_plot

        item.set_callback(get_video_url, video_url=video_url)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item


@Resolver.register
def get_video_url(plugin, video_url, download_mode=False, **kwargs):

    resp = urlquick.get(video_url, headers=GENERIC_HEADERS)
    video_id = re.compile(r'dailymotion.com/embed/video/(.*?)[\?\"]').findall(resp.text)[0]
    return resolver_proxy.get_stream_dailymotion(plugin, video_id, download_mode)


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    headers = [
        ('User-Agent', web_utils.get_random_ua()),
        ('Accept', 'application/json'),
        ('Referer', 'https://player.kick.com/'),
    ]

    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    opener.addheaders = headers

    with opener.open(URL_KICK_INFO) as resp:
        json_parser = json.loads(resp.read().decode('utf-8'))

    video_url = json_parser['playback_url']

    return resolver_proxy.get_stream_with_quality(plugin, video_url=video_url)
