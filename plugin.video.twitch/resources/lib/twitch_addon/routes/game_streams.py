# -*- coding: utf-8 -*-
"""

    Copyright (C) 2012-2018 Twitch-on-Kodi

    This file is part of Twitch-on-Kodi (plugin.video.twitch)

    SPDX-License-Identifier: GPL-3.0-only
    See LICENSES/GPL-3.0-only for more information.
"""
from ..addon import utils
from ..addon.common import kodi
from ..addon.constants import Keys, LINE_LENGTH, MODES
from ..addon.converter import JsonListItemConverter
from ..addon.twitch_exceptions import NotFound
from ..addon.utils import i18n


def route(api, game, after='MA=='):
    converter = JsonListItemConverter(LINE_LENGTH)
    utils.refresh_previews()
    kodi.set_view('videos', set_sort=True)
    per_page = utils.get_items_per_page()
    language = utils.get_language()

    all_items = list()

    streams = api.get_game_streams(game_id=game, after=after, first=per_page, language=language)

    if Keys.DATA in streams:
        for stream in streams[Keys.DATA]:
            all_items.append(stream)

    if len(all_items) > 0:
        for stream in all_items:
            kodi.create_item(converter.stream_to_listitem(stream))

        cursor = streams.get('pagination', {}).get('cursor')
        if cursor:
            kodi.create_item(utils.link_to_next_page({'mode': MODES.GAMESTREAMS, 'game': game, 'after': cursor}))

        kodi.end_of_directory()
        return
    raise NotFound(i18n('streams'))
