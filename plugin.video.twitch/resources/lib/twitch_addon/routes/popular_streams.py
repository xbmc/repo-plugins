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
    converter = JsonListItemConverter(LINE_LENGTH)
    utils.refresh_previews()
    kodi.set_view('videos', set_sort=True)
    streams = api.get_all_streams(first=100)
    if Keys.DATA in streams:
        if streams[Keys.DATA]:
            for result in streams[Keys.DATA]:
                kodi.create_item(converter.stream_to_listitem(result))
            kodi.end_of_directory()
            return
    raise NotFound('streams')
