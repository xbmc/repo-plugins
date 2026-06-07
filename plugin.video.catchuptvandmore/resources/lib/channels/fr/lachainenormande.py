# -*- coding: utf-8 -*-
# Copyright: (c) 2019, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import json

import inputstreamhelper
from codequick import Listitem, Resolver
import urlquick

from resources.lib import web_utils
from resources.lib.kodi_utils import get_selected_item_art, get_selected_item_label, get_selected_item_info, INPUTSTREAM_PROP


# TODO
# Add Replay

URL_ROOT = "https://www.lachainenormande.tv"


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

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
    item.property[INPUTSTREAM_PROP] = "inputstream.adaptive"
    item.property["inputstream.adaptive.manifest_type"] = "mpd"
    item.label = get_selected_item_label()
    item.art.update(get_selected_item_art())
    item.info.update(get_selected_item_info())
    return item
