# -*- coding: utf-8 -*-

# Advanced MAME Launcher asset (artwork) related stuff.

# Copyright (c) 2016-2020 Wintermute0110 <wintermute0110@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.

# --- Python standard library ---
from __future__ import unicode_literals

# -------------------------------------------------------------------------------------------------
# Asset functions
# -------------------------------------------------------------------------------------------------
#
# Make sure this match the contents of settings.xml!
# values="Title|Snap|Flyer|Cabinet|PCB"
#
def assets_get_asset_key_MAME_icon(asset_index):
    asset_key = 'title' # Default value

    if   asset_index == 0: asset_key = 'title'
    elif asset_index == 1: asset_key = 'snap'
    elif asset_index == 2: asset_key = 'flyer'
    elif asset_index == 3: asset_key = 'cabinet'
    elif asset_index == 4: asset_key = 'PCB'

    return asset_key

#
# values="Fanart|Snap|Title|Flyer|CPanel"
#
def assets_get_asset_key_MAME_fanart(asset_index):
    asset_key = 'fanart' # Default value

    if   asset_index == 0: asset_key = 'fanart'
    elif asset_index == 1: asset_key = 'snap'
    elif asset_index == 2: asset_key = 'title'
    elif asset_index == 3: asset_key = 'flyer'
    elif asset_index == 4: asset_key = 'cpanel'

    return asset_key

#
# values="Boxfront|Title|Snap"
#
def assets_get_asset_key_SL_icon(asset_index):
    asset_key = 'boxfront' # Default value

    if   asset_index == 0: asset_key = 'boxfront'
    elif asset_index == 1: asset_key = 'title'
    elif asset_index == 2: asset_key = 'snap'

    return asset_key

#
# values="Fanart|Snap|Title"
#
def assets_get_asset_key_SL_fanart(asset_index):
    asset_key = 'fanart' # Default value

    if   asset_index == 0: asset_key = 'fanart'
    elif asset_index == 1: asset_key = 'snap'
    elif asset_index == 2: asset_key = 'title'

    return asset_key
