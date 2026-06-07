# ----------------------------------------------------------------------------------------------------------------------
#  Copyright (c) 2025 Dimitri Kroon.
#  This file is part of plugin.video.viwx.
#  SPDX-License-Identifier: GPL-2.0-or-later
#  See LICENSE.txt
# ----------------------------------------------------------------------------------------------------------------------

region_map = {
    "london": "london",
    "meridian_east": "meridian_east",
    "meridian_south_coast": "meridian_east",
    "meridian_thames_valley": "meridian_east",
    "channel_islands": "meridian_east",
    "anglia_east": "meridian_east",
    "anglia_west": "meridian_east",
    "central_west": "central_west",
    "central_east":  "central_west",
    "west":  "central_west",
    "west_country":  "central_west",
    "wales": "wales",
    "granada": "granada",
    "border_england": "granada",
    "border_scotland": "granada",
    "tyne_tees": "granada",
    "emley_moor": "granada",
    "belmont": "granada",
    "ulster": "ulster",
}


def tv_region(user_region):
    """Convert a user's region to a TV region.

    Used in live TV to get the correct regional news and weather.
    """
    return region_map.get(user_region, '')
