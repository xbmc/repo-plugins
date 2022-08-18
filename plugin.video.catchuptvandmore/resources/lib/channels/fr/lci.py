# -*- coding: utf-8 -*-
# Copyright: (c) JUL1EN094, SPM, SylvainCecchetto
# Copyright: (c) 2016, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals

import json
import re
from builtins import str

import inputstreamhelper
import urlquick
from codequick import Listitem, Resolver, Route, utils
from kodi_six import xbmcgui
from resources.lib import web_utils
from resources.lib.kodi_utils import (INPUTSTREAM_PROP, get_selected_item_art,
                                      get_selected_item_info,
                                      get_selected_item_label)
from resources.lib.menu_utils import item_post_treatment

# TO DO
# Add aired, date, duration etc...
# Rework get_video_url (remove code not needed)

URL_ROOT = utils.urljoin_partial("http://www.tf1.fr")

URL_LCI_CATEGORIES = "http://www.lci.fr/%s"
URL_LCI_ROOT = "http://www.lci.fr"

URL_VIDEO_STREAM = "https://mediainfo.tf1.fr/mediainfocombo/%s?context=MYTF1&pver=4008002&platform=web&os=linux&osVersion=unknown&topDomain=www.tf1.fr"

URL_LICENCE_KEY = "https://drm-wide.tf1.fr/proxy?id=%s|Content-Type=&User-Agent=Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3041.0 Safari/537.36&Host=drm-wide.tf1.fr|R{SSM}|"
# videoId


@Route.register
def lci_root(plugin, item_id, **kwargs):
    """LCI cacth up tv entry point."""
    categories = [
        ("emissions", plugin.localize(30729)),
        ("replay-lci", plugin.localize(30031)),
    ]

    for category in categories:
        item = Listitem()
        item.label = category[1]
        item.set_callback(list_programs, item_id, category[0])
        item_post_treatment(item)
        yield item


@Route.register
def list_programs(plugin, item_id, path, **kwargs):
    """Build programs listing."""
    resp = urlquick.get(URL_LCI_CATEGORIES % path)
    root = resp.parse("ul", attrs={"class": "topic-chronology-milestone-component"})

    for program in root.iterfind(".//li"):
        item = Listitem()
        program_url = URL_LCI_ROOT + program.find(".//a").get("href")
        program_name = program.find(".//h2[@class='text-block']").text
        img = program.findall(".//source")[0]
        try:
            img = img.get("data-srcset")
        except Exception:
            img = img.get("srcset")
        img = img.split(",")[0].split(" ")[0]
        item.label = program_name
        item.art["thumb"] = item.art["landscape"] = img
        item.set_callback(
            list_videos, item_id=item_id, program_url=program_url, page="1"
        )
        item_post_treatment(item)
        yield item


@Route.register
def list_videos(plugin, item_id, program_url, page, **kwargs):

    if page == "1":
        resp = urlquick.get(program_url)
    else:
        resp = urlquick.get(program_url + "%s/" % page)
    root = resp.parse()

    for replay in root.iterfind(".//article[@class='grid-blk__item']"):

        title = replay.find(".//h2").text
        img = ""
        for img in replay.findall(".//source"):
            try:
                img = img.get("data-srcset")
            except Exception:
                img = img.get("srcset")

        img = img.split(",")[0].split(" ")[0]
        program_id = URL_LCI_ROOT + replay.find(".//a").get("href")

        item = Listitem()
        item.label = title
        item.art["thumb"] = item.art["landscape"] = img

        item.set_callback(get_video_url, item_id=item_id, program_id=program_id)
        item_post_treatment(item, is_playable=True, is_downloadable=False)
        yield item

    # More videos...
    yield Listitem.next_page(
        item_id=item_id, program_url=program_url, page=str(int(page) + 1)
    )


@Resolver.register
def get_video_url(plugin, item_id, program_id, download_mode=False, **kwargs):

    if "www.wat.tv/embedframe" in program_id:
        url = "http:" + program_id
    elif "http" not in program_id:
        if program_id[0] == "/":
            program_id = program_id[1:]
        url = URL_ROOT(program_id)
    else:
        url = program_id

    video_html = urlquick.get(url).text

    if "www.wat.tv/embedframe" in program_id:
        video_id = re.compile("UVID=(.*?)&").findall(video_html)[0]
    elif item_id == "lci":
        video_id = re.compile(r'data-videoid="(.*?)"').findall(video_html)[0]
    else:
        root = video_html.parse()
        iframe_player = root.find(".//div[@class='iframe_player']")
        if iframe_player is not None:
            video_id = iframe_player.get("data-watid")
        else:
            video_id = re.compile(r"www\.tf1\.fr\/embedplayer\/(.*?)\"").findall(
                video_html
            )[0]

    url_json = URL_VIDEO_STREAM % video_id
    htlm_json = urlquick.get(
        url_json, headers={"User-Agent": web_utils.get_random_ua()}, max_age=-1
    )
    json_parser = json.loads(htlm_json.text)

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

    return item


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    video_id = "L_%s" % item_id.upper()
    url_json = URL_VIDEO_STREAM % (video_id)
    htlm_json = urlquick.get(
        url_json, headers={"User-Agent": web_utils.get_random_ua()}, max_age=-1
    )
    json_parser = json.loads(htlm_json.text)

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

    return item
