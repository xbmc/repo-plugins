# -*- coding: utf-8 -*-
# Copyright: (c) 2019, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
from builtins import str
import re

from codequick import Listitem, Resolver, Route
import urlquick

from resources.lib import resolver_proxy, web_utils
from resources.lib.menu_utils import item_post_treatment


# TO DO
# Add Pseudo Live TV (like RTBF and France TV Sport)
# Add info video (duration)
# Fix video date

URL_ROOT = 'https://noovo.ca'
# Channel Name

URL_EMISSIONS = URL_ROOT + '/emissions'

URL_VIDEOS = 'https://noovo.ca/index.php/actions/noovo/show/getPaginatedEpisodes/p%s?seasonId=%s'
# Page, SeasonId

URL_LIVE = URL_ROOT + '/en-direct'

URL_LIVE_INFOS = URL_ROOT + '/dist/js/noovo.%s.js'
# Id


@Route.register
def list_programs(plugin, item_id, **kwargs):
    """
    Build programs listing
    - ...
    """
    resp = urlquick.get(URL_EMISSIONS,
                        headers={'User-Agent': web_utils.get_random_ua()})
    root = resp.parse()

    for program_datas in root.iterfind(".//div[@class='card']"):
        program_title = program_datas.find(".//img").get("alt")
        program_image = program_datas.find(".//img").get("src")
        program_url = program_datas.find(".//a").get("href")

        item = Listitem()
        item.label = program_title
        item.art['thumb'] = item.art['landscape'] = program_image
        item.set_callback(
            list_seasons, item_id=item_id, program_url=program_url)
        item_post_treatment(item)
        yield item


@Route.register
def list_seasons(plugin, item_id, program_url, **kwargs):

    resp = urlquick.get(program_url,
                        headers={'User-Agent': web_utils.get_random_ua()})
    root = resp.parse()
    if root.find(".//ul[@class='dropdown__menu']") is not None:
        root = resp.parse("ul", attrs={"class": "dropdown__menu"})

        for season_datas in root.iterfind(".//li"):
            season_title = season_datas.find(".//a").text
            season_url = URL_ROOT + season_datas.find(".//a").get('href')

            item = Listitem()
            item.label = season_title

            item.set_callback(
                list_videos, item_id=item_id, season_url=season_url, page='1')
            item_post_treatment(item)
            yield item


@Route.register
def list_videos(plugin, item_id, season_url, page, **kwargs):

    resp = urlquick.get(season_url,
                        headers={'User-Agent': web_utils.get_random_ua()})
    list_season_id = re.compile(r'\?seasonId\=(.*?)\"').findall(resp.text)

    if len(list_season_id) > 0:
        resp2 = urlquick.get(URL_VIDEOS % (page, list_season_id[0]))
        root = resp2.parse()
    else:
        root = resp.parse()

    for video_datas in root.iterfind(
            ".//div[@class='card card--video']"):
        video_title = video_datas.find(".//img").get('alt')
        video_image = video_datas.find(".//img").get('src')
        video_plot = ''
        if video_datas.find(".//p[@class='card__description']").find(
                ".//p") is not None:
            video_plot = video_datas.find(
                ".//p[@class='card__description']").find(".//p").text
        video_url = video_datas.find(".//a").get('href')
        # video_date = video_datas.find(".//time").text
        video_duration = 0

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = item.art['landscape'] = video_image
        item.info['plot'] = video_plot
        item.info['duration'] = video_duration
        # item.info.date(video_date, "%Y-%m-%d")

        item.set_callback(
            get_video_url,
            item_id=item_id,
            video_url=video_url)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item

    if len(list_season_id) > 0:
        yield Listitem.next_page(
            item_id=item_id, season_url=season_url, page=str(int(page) + 1))


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_url,
                  download_mode=False,
                  **kwargs):

    resp = urlquick.get(
        video_url, headers={'User-Agent': web_utils.get_random_ua()}, max_age=-1)
    data_account = re.compile(r'data-account\=\"(.*?)\"').findall(resp.text)[0]
    data_player = re.compile(r'data-player\=\"(.*?)\"').findall(resp.text)[0]
    data_video_id = re.compile(r'data-video-id\=\"(.*?)\"').findall(
        resp.text)[0]
    return resolver_proxy.get_brightcove_video_json(plugin, data_account, data_player, data_video_id, None, download_mode)


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    resp = urlquick.get(
        URL_LIVE, headers={'User-Agent': web_utils.get_random_ua()}, max_age=-1)
    live_info_id = re.compile(
        r'dist\/js\/noovo\.(.*?)\.').findall(resp.text)[0]

    resp2 = urlquick.get(
        URL_LIVE_INFOS % live_info_id, headers={'User-Agent': web_utils.get_random_ua()}, max_age=-1)

    data_account = re.compile(r'data-account\=\"(.*?)\"').findall(resp2.text)[0]
    data_player = re.compile(r'data-embed\=\"(.*?)\"').findall(resp2.text)[0]
    data_video_id = re.compile(r'data-video-id\=\"(.*?)\"').findall(
        resp2.text)[0]
    return resolver_proxy.get_brightcove_video_json(plugin, data_account,
                                                    data_player, data_video_id,
                                                    False)
