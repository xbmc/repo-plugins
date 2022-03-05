# -*- coding: utf-8 -*-
# Copyright: (c) 2022, Joaopa
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from codequick import Listitem, Resolver
import urlquick
import json

import inputstreamhelper
from resources.lib import resolver_proxy, web_utils
from resources.lib.kodi_utils import (INPUTSTREAM_PROP, get_selected_item_art,
                                      get_selected_item_info,
                                      get_selected_item_label)
from resources.lib.menu_utils import item_post_treatment

# TODO
# Add Replay

URL_ROOT = "https://www.lrt.lt"

URL_API = URL_ROOT + "/servisai/stream_url/live/get_live_url.php?channel=%s"


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_API % item_id, headers={'User-Agent': web_utils.get_random_ua()}, max_age=-1).json()

    is_helper = inputstreamhelper.Helper("hls")
    if not is_helper.check_inputstream():
        return False

    item = Listitem()
    item.path = resp['response']['data']['content']
    item.property[INPUTSTREAM_PROP] = "inputstream.adaptive"
    item.property["inputstream.adaptive.manifest_type"] = "hls"

    return item
