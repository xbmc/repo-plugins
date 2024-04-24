# -*- coding: utf-8 -*-
# Copyright: (c) 2022, Joaopa
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals

from codequick import Script, utils

# The following dictionaries describe
# the addon's tree architecture.
# * Key: item id
# * Value: item infos
#     - route (folder)/resolver (playable URL): Callback function to run once this item is selected
#     - thumb: Item thumb path relative to "media" folder
#     - fanart: Item fanart path relative to "media" folder

root = "live_tv"

menu = {
    "atv": {
        "resolver": "/resources/lib/channels/pe/atv:get_live_url",
        "label": "ATV",
        "thumb": "channels/pe/atv.png",
        "fanart": "channels/pe/atv_fanart.jpg",
        "enabled": True,
        "order": 1,
    },
    "atvmas": {
        "resolver": "/resources/lib/channels/pe/atv:get_live_url",
        "label": "ATV+",
        "thumb": "channels/pe/atvplus.png",
        "fanart": "channels/pe/atvplus_fanart.jpg",
        "enabled": True,
        "order": 2,
    },
    "enlace": {
        "resolver": "/resources/lib/channels/pe/enlace:get_live_url",
        "label": "Enlace",
        "thumb": "channels/pe/enlace.png",
        "fanart": "channels/pe/enlace_fanart.jpg",
        "enabled": True,
        "order": 3,
    },
    "panamericana": {
        "resolver": "/resources/lib/channels/pe/panamericana:get_live_url",
        "label": "Panamericana TV",
        "thumb": "channels/pe/panamericana.png",
        "fanart": "channels/pe/panamericana_fanart.jpg",
        "enabled": True,
        "order": 4,
    },
}
