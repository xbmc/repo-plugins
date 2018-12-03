# -*- coding: utf-8 -*-
"""

    Copyright (C) 2012-2018 Twitch-on-Kodi

    This file is part of Twitch-on-Kodi (plugin.video.twitch)

    SPDX-License-Identifier: GPL-3.0-only
    See LICENSES/GPL-3.0-only for more information.
"""
from ..addon import utils
from ..addon.common import kodi
from ..addon.constants import Keys, LINE_LENGTH
from ..addon.converter import JsonListItemConverter
from ..addon.twitch_exceptions import NotFound


def route(api):
    blacklist_filter = utils.BlacklistFilter()
    converter = JsonListItemConverter(LINE_LENGTH)
    utils.refresh_previews()
    kodi.set_view('videos', set_sort=True)
    streams = api.get_featured_streams(offset=0, limit=100)
    if Keys.FEATURED in streams:
        filtered = \
            blacklist_filter.by_type(streams, Keys.FEATURED, parent_keys=[Keys.STREAM, Keys.CHANNEL], id_key=Keys._ID, list_type='user')
        filtered = \
            blacklist_filter.by_type(filtered, Keys.FEATURED, parent_keys=[Keys.STREAM], game_key=Keys.GAME, list_type='game')
        if filtered[Keys.FEATURED]:
            for result in filtered[Keys.FEATURED]:
                kodi.create_item(converter.stream_to_listitem(result[Keys.STREAM]))
            kodi.end_of_directory()
            return
    raise NotFound('streams')
