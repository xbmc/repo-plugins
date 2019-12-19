# -*- coding: utf-8 -*-
"""
    Catch-up TV & More
    Copyright (C) 2019  SylvainCecchetto

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

from codequick import Route, Resolver, Listitem, utils, Script

from resources.lib.labels import LABELS
from resources.lib import web_utils
from resources.lib.listitem_utils import item_post_treatment, item2dict

import inputstreamhelper
import json
import re
import urlquick

# TODO
# Add Replay

URL_ROOT = "https://www.lachainenormande.tv"


def live_entry(plugin, item_id, item_dict, **kwargs):
    return get_live_url(plugin, item_id, item_id.upper(), item_dict)


@Resolver.register
def get_live_url(plugin, item_id, video_id, item_dict, **kwargs):

    is_helper = inputstreamhelper.Helper('mpd')
    if not is_helper.check_inputstream():
        return False

    resp = urlquick.get(
        URL_ROOT, headers={"User-Agent": web_utils.get_random_ua()}, max_age=-1)
    root = resp.parse()
    url_live_datas = URL_ROOT + root.find(".//div[@class='HDR_VISIO']").get(
        "data-url") + "&mode=html"

    resp2 = urlquick.get(
        url_live_datas,
        headers={"User-Agent": web_utils.get_random_ua()},
        max_age=-1)
    json_parser = json.loads(resp2.text)

    item = Listitem()
    item.path = json_parser["files"]["auto"]
    item.property["inputstreamaddon"] = "inputstream.adaptive"
    item.property["inputstream.adaptive.manifest_type"] = "mpd"
    if item_dict:
        if "label" in item_dict:
            item.label = item_dict["label"]
        if "info" in item_dict:
            item.info.update(item_dict["info"])
        if "art" in item_dict:
            item.art.update(item_dict["art"])
    else:
        item.label = LABELS[item_id]
        item.art["thumb"] = ""
        item.art["icon"] = ""
        item.art["fanart"] = ""
        item.info["plot"] = LABELS[item_id]
    return item
