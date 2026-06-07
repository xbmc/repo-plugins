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
    "venezolana": {
        "resolver": "/resources/lib/channels/ve/venezolana:get_live_url",
        "label": "Venezolana",
        "thumb": "channels/ve/venezolana.png",
        "fanart": "channels/ve/venezolana_fanart.jpg",
        "enabled": True,
        "order": 1,
    },
}
