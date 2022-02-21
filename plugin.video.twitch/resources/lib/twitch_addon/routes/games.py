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


def route(api, after='MA=='):
    converter = JsonListItemConverter(LINE_LENGTH)
    kodi.set_view('files', set_sort=False)
    per_page = utils.get_items_per_page()
    all_items = list()

    games = api.get_top_games(after=after, first=per_page)

    if Keys.DATA in games:
        for game in games[Keys.DATA]:
            all_items.append(game)

    if len(all_items) > 0:
        for game in all_items:
            kodi.create_item(converter.game_to_listitem(game))

        cursor = games.get('pagination', {}).get('cursor')
        if cursor:
            kodi.create_item(utils.link_to_next_page({'mode': MODES.GAMES, 'after': cursor}))

        kodi.end_of_directory()
        return

    raise NotFound('games')
