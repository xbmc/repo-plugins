# -*- coding: utf-8 -*-
# Copyright: (c) 2017, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
from builtins import str
import json

from codequick import Listitem, Resolver, Route
import urlquick

from resources.lib import download
from resources.lib.menu_utils import item_post_treatment


URL_ROOT = 'https://www3.nhk.or.jp/'

URL_WEATHER_NHK_NEWS = URL_ROOT + '/news/weather/weather_movie.json'

URL_NEWS_NHK_NEWS = URL_ROOT + '/news/json16/newmovie_%s.json'
# Page

URL_STREAM_NHK_NEWS = URL_ROOT + '/news/html/%s/movie/%s.json'
# Date, IdVideo

CORRECT_MONTH = {
    'Jan': '01',
    'Feb': '02',
    'Mar': '03',
    'Apr': '04',
    'May': '05',
    'Jun': '06',
    'Jul': '07',
    'Aug': '08',
    'Sep': '09',
    'Oct': '10',
    'Nov': '11',
    'Dec': '12'
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
    category_title = 'NHK ニュース'
    item = Listitem()
    item.label = category_title
    item.set_callback(list_videos_news, item_id=item_id, page='1')
    item_post_treatment(item)
    yield item

    category_title = 'NHK ニュース - 気象'
    item = Listitem()
    item.label = category_title
    item.set_callback(list_videos_weather, item_id=item_id)
    item_post_treatment(item)
    yield item


@Route.register
def list_videos_weather(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_WEATHER_NHK_NEWS)
    json_parser = json.loads(resp.text)

    video_title = json_parser["va"]["adobe"]["vodContentsID"]["VInfo1"]
    video_image = URL_ROOT + json_parser["mediaResource"]["posterframe"]
    video_url = json_parser["mediaResource"]["url"]

    item = Listitem()
    item.label = video_title
    item.art['thumb'] = item.art['landscape'] = video_image
    item.set_callback(get_video_weather_url,
                      item_id=item_id,
                      video_url=video_url)
    item_post_treatment(item, is_playable=True, is_downloadable=True)
    yield item


@Resolver.register
def get_video_weather_url(plugin,
                          item_id,
                          video_url,
                          download_mode=False,
                          **kwargs):
    return video_url


@Route.register
def list_videos_news(plugin, item_id, page, **kwargs):

    list_videos_datas_url = ''
    if int(page) < 10:
        list_videos_datas_url = URL_NEWS_NHK_NEWS % ('00' + page)
    elif int(page) >= 10 and int(page) < 100:
        list_videos_datas_url = URL_NEWS_NHK_NEWS % ('0' + page)
    else:
        list_videos_datas_url = URL_NEWS_NHK_NEWS % page

    resp = urlquick.get(list_videos_datas_url)
    json_parser = json.loads(resp.text)

    for video_datas in json_parser["channel"]["item"]:
        video_title = video_datas["title"]
        video_image = URL_ROOT + 'news/' + video_datas["imgPath"]
        video_duration = int(video_datas["videoDuration"])
        video_id = video_datas["videoPath"].replace('.mp4', '')
        date_value = video_datas["pubDate"].split(' ')
        if len(date_value[1]) == 1:
            day = '0' + date_value[0]
        else:
            day = date_value[1]
        try:
            month = CORRECT_MONTH[date_value[2]]
        except Exception:
            month = '00'
        year = date_value[3]
        video_date = ''.join((year, month, day))
        date_value = '-'.join((year, month, day))

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = item.art['landscape'] = video_image
        item.info['duration'] = video_duration
        item.info.date(date_value, '%Y-%m-%d')

        item.set_callback(get_video_news_url,
                          item_id=item_id,
                          video_id=video_id,
                          video_date=video_date)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item

    yield Listitem.next_page(item_id=item_id, page=str(int(page) + 1))


@Resolver.register
def get_video_news_url(plugin,
                       item_id,
                       video_id,
                       video_date,
                       download_mode=False,
                       **kwargs):

    resp = urlquick.get(URL_STREAM_NHK_NEWS % (video_date, video_id))
    json_parser = json.loads(resp.text)
    final_video_url = json_parser["mediaResource"]["url"]
    if download_mode:
        return download.download_video(final_video_url)
    return final_video_url
