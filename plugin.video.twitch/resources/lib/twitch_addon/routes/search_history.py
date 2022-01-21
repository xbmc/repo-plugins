# -*- coding: utf-8 -*-
"""

    Copyright (C) 2012-2018 Twitch-on-Kodi

    This file is part of Twitch-on-Kodi (plugin.video.twitch)

    SPDX-License-Identifier: GPL-3.0-only
    See LICENSES/GPL-3.0-only for more information.
"""
from ..addon import utils, menu_items
from ..addon.common import kodi
from ..addon.constants import MODES
from ..addon.utils import i18n


def route(content):
    kodi.set_view('files', set_sort=False)
    context_menu = list()
    context_menu.extend(menu_items.clear_search_history(content, do_refresh=True))
    kodi.create_item({'label': '[B]%s[/B]' % i18n('new_search'), 'path': {'mode': MODES.NEWSEARCH, 'content': content},
                      'info': {'plot': i18n('new_search')}, 'context_menu': context_menu, 'thumbfile': 'Search.png'})
    history = utils.get_search_history(content)
    history_items = list()
    if history:
        history_items = history.list()
    if len(history_items) > 0:
        for item in history_items:
            context_menu = list()
            context_menu.extend(menu_items.clear_search_history(content, do_refresh=True))
            context_menu.extend(menu_items.remove_search_history(content, item, do_refresh=True))
            kodi.create_item({'label': item, 'path': {'mode': MODES.SEARCHRESULTS, 'content': content, 'query': item},
                              'info': {'plot': item}, 'context_menu': context_menu})
    kodi.end_of_directory(cache_to_disc=False)
