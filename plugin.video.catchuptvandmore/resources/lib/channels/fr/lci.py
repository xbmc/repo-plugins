# -*- coding: utf-8 -*-
# Copyright: (c) JUL1EN094, SPM, SylvainCecchetto, darodi
# Copyright: (c) 2016, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals

import json
import re

import inputstreamhelper
import urlquick
# noinspection PyUnresolvedReferences
from codequick import Listitem, Resolver, Route, utils
# noinspection PyUnresolvedReferences
from codequick.utils import urljoin_partial
# noinspection PyUnresolvedReferences
from kodi_six import xbmcgui

from resources.lib import web_utils
from resources.lib.kodi_utils import (INPUTSTREAM_PROP, get_selected_item_art,
                                      get_selected_item_info,
                                      get_selected_item_label)
from resources.lib.menu_utils import item_post_treatment

# TO DO
# Add aired, date, duration etc...
# Rework get_video_url (remove code not needed)

URL_ROOT = "https://www.tf1info.fr"
url_constructor = urljoin_partial(URL_ROOT)

URL_LCI_EMISSIONS = url_constructor('/emissions/?channel=lci')

# "https://mediainfo.tf1.fr/mediainfocombo/%s?context=MYTF1&pver=4015000&topDomain=unknown&platform=web&device=desktop&os=windows&osVersion=10.0&playerVersion=4.15.0&productName=mytf1&productVersion=0.0.0&browser=firefox&browserVersion=100"

URL_VIDEO_STREAM = "https://mediainfo.tf1.fr/mediainfocombo/%s?context=MYTF1&pver=4008002&platform=web&os=linux&osVersion=unknown&topDomain=www.tf1.fr"

# videoId
URL_LICENCE_KEY = "https://drm-wide.tf1.fr/proxy?id=%s|Content-Type=&User-Agent=Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3041.0 Safari/537.36&Host=drm-wide.tf1.fr|R{SSM}|"


@Route.register
def lci_root(plugin, item_id, **kwargs):
    """Build programs listing."""
    resp = urlquick.get(URL_LCI_EMISSIONS)
    root = resp.parse("div", attrs={"id": "ProgramList__Container-1"})

    for program in root.iterfind("./a"):
        item = Listitem()
        program_url = url_constructor(program.get("href"))
        program_name = re.sub(r'.*/emission/([^/]*)/', r'\1', program_url)
        program_name = re.sub(r'-[^-]+$', '', program_name)
        program_name = re.sub(r'-', ' ', program_name)
        img = get_image(program)
        item.label = program_name
        if img is not None:
            item.art["thumb"] = item.art["landscape"] = img
        item.set_callback(list_videos, item_id=item_id, program_url=program_url, page="1")
        item_post_treatment(item)
        yield item


def get_image(program):
    img_sources = program.findall(".//picture//source")
    img = None
    for img_source in img_sources:
        img = img_source.get("data-srcset")
        if img is None:
            img = img_source.get("srcset")
    return img


@Route.register
def list_videos(plugin, item_id, program_url, page, **kwargs):
    if page == "1":
        resp = urlquick.get(program_url)
    else:
        resp = urlquick.get(program_url + "%s/" % page)

    body_header = resp.parse("span", attrs={"data-module": "program-header"})
    plot = body_header.findtext(".//span")

    root = resp.parse("div", attrs={"data-module": "program-video-list"})

    for replay in root.iterfind(".//ul/li"):
        img = get_image(replay)
        program_url = url_constructor(replay.find(".//a").get("href"))

        item = Listitem()
        item.label = replay.find(".//h2").text
        if img is not None:
            item.art["thumb"] = item.art["landscape"] = img

        if plot is not None:
            item.info['plot'] = plot

        item.set_callback(get_video_url, item_id=item_id, program_url=program_url)
        item_post_treatment(item, is_playable=True, is_downloadable=False)
        yield item

    # More videos...
    yield Listitem.next_page(item_id=item_id, program_url=program_url, page=str(int(page) + 1))


@Resolver.register
def get_video_url(plugin, item_id, program_url, download_mode=False, **kwargs):
    json_data = urlquick.get(program_url).parse().find(".//script[@id='__NEXT_DATA__']").text
    json_parser_program = json.loads(json_data)
    video_id = json_parser_program["props"]["pageProps"]["page"]["video"]["id"]

    json_parser = urlquick.get(URL_VIDEO_STREAM % video_id,
                               headers={"User-Agent": web_utils.get_random_ua()},
                               max_age=-1).json()

    if json_parser["delivery"]["code"] > 400:
        plugin.notify("ERROR", plugin.localize(30713))
        return False

    if download_mode:
        xbmcgui.Dialog().ok("Info", plugin.localize(30603))
        return False

    is_helper = inputstreamhelper.Helper("mpd", drm="widevine")
    if not is_helper.check_inputstream():
        return False

    item = Listitem()
    item.path = json_parser["delivery"]["url"]
    item.label = get_selected_item_label()
    item.art.update(get_selected_item_art())
    item.info.update(get_selected_item_info())
    item.property[INPUTSTREAM_PROP] = "inputstream.adaptive"
    item.property["inputstream.adaptive.manifest_type"] = "mpd"
    item.property["inputstream.adaptive.license_type"] = "com.widevine.alpha"
    item.property["inputstream.adaptive.license_key"] = URL_LICENCE_KEY % video_id
    stream_bitrate_limit = plugin.setting.get_int('stream_bitrate_limit')
    if stream_bitrate_limit > 0:
        item.property["inputstream.adaptive.max_bandwidth"] = str(stream_bitrate_limit * 1000)

    return item


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    video_id = "L_%s" % item_id.upper()
    json_parser = urlquick.get(URL_VIDEO_STREAM % video_id,
                               headers={"User-Agent": web_utils.get_random_ua()},
                               max_age=-1).json()

    if json_parser["delivery"]["code"] > 400:
        plugin.notify("ERROR", plugin.localize(30713))
        return False

    is_helper = inputstreamhelper.Helper("mpd", drm="widevine")
    if not is_helper.check_inputstream():
        return False

    item = Listitem()
    item.path = json_parser["delivery"]["url"]
    item.label = get_selected_item_label()
    item.art.update(get_selected_item_art())
    item.info.update(get_selected_item_info())
    item.property[INPUTSTREAM_PROP] = "inputstream.adaptive"
    item.property["inputstream.adaptive.manifest_type"] = "mpd"
    item.property["inputstream.adaptive.license_type"] = "com.widevine.alpha"
    item.property["inputstream.adaptive.license_key"] = URL_LICENCE_KEY % video_id
    stream_bitrate_limit = plugin.setting.get_int('stream_bitrate_limit')
    if stream_bitrate_limit > 0:
        item.property["inputstream.adaptive.max_bandwidth"] = str(stream_bitrate_limit * 1000)

    return item
