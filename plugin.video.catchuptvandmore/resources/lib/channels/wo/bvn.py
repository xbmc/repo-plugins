# -*- coding: utf-8 -*-
# Copyright: (c) 2017, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals

import json
import re

import urlquick
# noinspection PyUnresolvedReferences
from codequick import Listitem, Resolver, Route

from resources.lib import resolver_proxy, web_utils
from resources.lib.menu_utils import item_post_treatment

URL_ROOT = 'https://www.bvn.tv'

# LIVE :
URL_LIVE = URL_ROOT + '/bvnlive'

# STREAM_LINK :
URL_STRAM_LINK = 'https://prod.npoplayer.nl/stream-link'

# REPLAY :
URL_DAYS = URL_ROOT + '/uitzendinggemist/'

# STREAM :
URL_STREAM = 'https://start-player.npo.nl/video/%s/streams'
# Id video, tokenId
URL_SUBTITLE = 'https://rs.poms.omroep.nl/v1/api/subtitles/%s'

# License URL
LICENSE_URL = "https://npo-drm-gateway.samgcloud.nepworldwide.nl/authentication?custom_data=%s"

GENERIC_HEADERS = {'User-Agent': web_utils.get_random_ua()}


@Route.register
def list_days(plugin, item_id, **kwargs):
    """
    Build categories listing
    - day 1
    - day 2
    - ...
    """

    resp = urlquick.get(URL_DAYS, headers=GENERIC_HEADERS, max_age=-1)
    root = resp.parse("div", attrs={"id": "missed"})

    day_id = 0
    for title in root.iterfind(".//h3[@class='m-section__title']"):
        day_title = title.text
        day_id = day_id + 1

        item = Listitem()
        item.label = day_title
        item.set_callback(list_videos, item_id=item_id, day_id=day_id)
        item_post_treatment(item)
        yield item


@Route.register
def list_videos(plugin, item_id, day_id, **kwargs):
    resp = urlquick.get(URL_DAYS, headers=GENERIC_HEADERS, max_age=-1)
    root = resp.parse("ul", attrs={"id": "slick-missed-day-%s" % day_id})

    for broadcast in root.iterfind(".//li"):
        video_time = broadcast.find(
            ".//time[@class='m-section__scroll__item__bottom__time']"
        ).text.replace('.', ':')
        video_title = video_time + " - " + broadcast.find(
            ".//span[@class='m-section__scroll__item__bottom__title']").text

        subtitle = broadcast.find(
            "span[@class='m-section__scroll__item__bottom__title--sub']")
        if subtitle is not None and subtitle.text is not None:
            video_title += ": " + subtitle.text

        video_image = URL_ROOT + broadcast.find('.//img').get('data-src')
        video_url = URL_ROOT + broadcast.find('.//a').get('href')

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = item.art['landscape'] = video_image

        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_url=video_url)
        item_post_treatment(item, is_playable=True, is_downloadable=False)
        yield item


@Resolver.register
def get_video_url(plugin, item_id, video_url, download_mode=False, **kwargs):

    resp = urlquick.get(video_url, headers=GENERIC_HEADERS, max_age=-1)

    token_id = re.compile(r'start-player\.npo\.nl/embed/(.*?)\"').findall(
        resp.text)[0]
    video_id = re.compile(r'\"iframe-(.*?)\"').findall(resp.text)[0]

    params = {
        'profile': 'dash-widevine',
        'quality': 'npo',
        'tokenId': token_id,
        'streamType': 'broadcast',
        'isYospace': '0',
        'videoAgeRating': 'null',
        'isChromecast': '0',
        'mobile': '0',
        'ios': '0'
    }

    resp2 = urlquick.post(URL_STREAM % video_id, params=params, headers=GENERIC_HEADERS, max_age=-1)
    json_parser = json.loads(resp2.text)

    if "html" in json_parser and "Deze video mag niet bekeken worden vanaf jouw locatie" in json_parser[
            "html"]:
        plugin.notify('ERROR', plugin.localize(30713))
        return False

    if "html" in json_parser and "Deze video is niet beschikbaar" in json_parser[
            "html"]:
        plugin.notify('ERROR', plugin.localize(30716))
        return False

    license_url = json_parser["stream"]["keySystemOptions"][0]["options"]["licenseUrl"]
    xcdata_value = json_parser["stream"]["keySystemOptions"][0]["options"]["httpRequestHeaders"]["x-custom-data"]

    video_url = json_parser["stream"]["src"]

    if plugin.setting.get_boolean('active_subtitle'):
        subtitles = URL_SUBTITLE % video_id
    else:
        subtitles = None

    headers = {
        'Content-Type': '',
        'User-Agent': web_utils.get_random_ua(),
        'x-custom-data': xcdata_value
    }

    return resolver_proxy.get_stream_with_quality(plugin, video_url=video_url, manifest_type="mpd", license_url=license_url, headers=headers, subtitles=subtitles)


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    resp = urlquick.get(URL_LIVE, headers=GENERIC_HEADERS, max_age=-1)
    jwt = re.compile('let jwt[^=]*= \"(.*?)\"').findall(resp.text)[0]

    headers = {
        'Authorization': jwt,
        'User-Agent': web_utils.get_random_ua()
    }

    json_data = {
        'profileName': 'dash',
        'drmType': 'widevine',
    }

    resp = urlquick.post(URL_STRAM_LINK, headers=headers, json=json_data, max_age=-1)

    json_parser = resp.json()

    drm_token = json_parser["stream"]['drmToken']
    license_url = LICENSE_URL % drm_token

    video_url = json_parser["stream"]["streamURL"]

    return resolver_proxy.get_stream_with_quality(plugin, video_url=video_url, manifest_type="mpd", license_url=license_url)
