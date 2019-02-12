# -*- coding: utf-8 -*-
"""

    Copyright (C) 2012-2018 Twitch-on-Kodi

    This file is part of Twitch-on-Kodi (plugin.video.twitch)

    SPDX-License-Identifier: GPL-3.0-only
    See LICENSES/GPL-3.0-only for more information.
"""
from ..addon import utils
from ..addon.common import kodi
from ..addon.constants import Keys, LINE_LENGTH, MODES, MAX_REQUESTS, REQUEST_LIMIT
from ..addon.converter import JsonListItemConverter
from ..addon.twitch_exceptions import NotFound


def route(api, offset):
    blacklist_filter = utils.BlacklistFilter()
    converter = JsonListItemConverter(LINE_LENGTH)
    kodi.set_view('files', set_sort=False)
    per_page = utils.get_items_per_page()
    games = None
    all_items = list()
    requests = 0
    while (per_page >= (len(all_items) + 1)) and (requests < MAX_REQUESTS):
        requests += 1
        games = api.get_top_games(offset, limit=REQUEST_LIMIT)
        if (games[Keys.TOTAL] > 0) and (Keys.TOP in games):
            filtered = \
                blacklist_filter.by_type(games, Keys.TOP, parent_keys=[Keys.GAME], game_key=Keys.NAME, list_type='game')
            last = None
            for game in filtered[Keys.TOP]:
                last = game
                if per_page >= (len(all_items) + 1):
                    add_item = last if last not in all_items else None
                    if add_item:
                        all_items.append(add_item)
                else:
                    break
            offset = utils.get_offset(offset, last[Keys.GAME], games[Keys.TOP], key=Keys.GAME)
            if (offset is None) or (games[Keys.TOTAL] <= offset) or (games[Keys.TOTAL] <= REQUEST_LIMIT):
                break
        else:
            break
    has_items = False
    if len(all_items) > 0:
        has_items = True
        for game in all_items:
            kodi.create_item(converter.game_to_listitem(game))
    if games[Keys.TOTAL] > (offset + 1):
        has_items = True
        kodi.create_item(utils.link_to_next_page({'mode': MODES.GAMES, 'offset': offset}))
    if has_items:
        kodi.end_of_directory()
        return
    raise NotFound('games')
