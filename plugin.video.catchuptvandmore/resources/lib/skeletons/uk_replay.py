# -*- coding: utf-8 -*-
# Copyright: (c) 2016, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals

# The following dictionaries describe
# the addon's tree architecture.
# * Key: item id
# * Value: item infos
#     - route (folder)/resolver (playable URL): Callback function to run once this item is selected
#     - thumb: Item thumb path relative to "media" folder
#     - fanart: Item fanart path relative to "media" folder

root = "replay"

menu = {
    "blaze": {
        "route": "/resources/lib/channels/uk/blaze:list_categories",
        "label": "Blaze",
        "thumb": "channels/uk/blaze.png",
        "fanart": "channels/uk/blaze_fanart.jpg",
        "enabled": True,
        "order": 1,
    },
    "skynews": {
        "route": "/resources/lib/channels/uk/sky:list_categories",
        "label": "Sky News",
        "thumb": "channels/uk/skynews.png",
        "fanart": "channels/uk/skynews_fanart.jpg",
        "enabled": True,
        "order": 2,
    },
    "skysports": {
        "route": "/resources/lib/channels/uk/sky:list_categories",
        "label": "Sky Sports",
        "thumb": "channels/uk/skysports.png",
        "fanart": "channels/uk/skysports_fanart.jpg",
        "enabled": True,
        "order": 3,
    },
    "channel4": {
        "route": "/resources/lib/channels/uk/channel4:list_categories",
        "label": "Channel 4",
        "thumb": "channels/uk/channel4.png",
        "fanart": "channels/uk/channel4_fanart.jpg",
        "enabled": True,
        "order": 4,
    },
    "stv": {
        "route": "/resources/lib/channels/uk/stv:list_categories",
        "label": "STV",
        "thumb": "channels/uk/stv.png",
        "fanart": "channels/uk/stv_fanart.jpg",
        "enabled": True,
        "order": 5,
    },
    "uktvplay": {
        "route": "/resources/lib/channels/uk/uktvplay:list_categories",
        "label": "UKTV Play",
        "thumb": "channels/uk/uktvplay.png",
        "fanart": "channels/uk/uktvplay_fanart.jpg",
        "enabled": True,
        "order": 6,
    },
    "my5": {
        "route": "/resources/lib/channels/uk/my5:list_categories",
        "label": "My 5",
        "thumb": "channels/uk/my5.png",
        "fanart": "channels/uk/my5_fanart.jpg",
        "enabled": True,
        "order": 7,
    },
    "uklocaltv": {
        "route": "/resources/lib/channels/uk/uklocaltv:channels",
        "label": "UK Local TV",
        "thumb": "channels/uk/uklocaltv.png",
        "fanart": "channels/uk/uklocaltv_fanart.jpg",
        "enabled": True,
        "order": 8,
    },
    "discoveryplus": {
        "route": "/resources/lib/channels/uk/discoveryplus:discoveryplus_root",
        "label": "discovery+",
        "thumb": "channels/uk/discoveryplus.png",
        "fanart": "channels/uk/discoveryplus_fanart.jpg",
        "enabled": False,
        "order": 9,
    },
}
