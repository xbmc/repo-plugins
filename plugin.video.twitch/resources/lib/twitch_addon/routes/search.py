# -*- coding: utf-8 -*-
"""

    Copyright (C) 2012-2018 Twitch-on-Kodi

    This file is part of Twitch-on-Kodi (plugin.video.twitch)

    SPDX-License-Identifier: GPL-3.0-only
    See LICENSES/GPL-3.0-only for more information.
"""
from ..addon.common import kodi
from ..addon import utils, menu_items
from ..addon.constants import MODES
from ..addon.utils import i18n


def route():
    kodi.set_view('files', set_sort=False)
    history_size = utils.get_search_history_size()
    use_history = history_size > 0
    if use_history:
        context_menu = list()
        context_menu.extend(menu_items.clear_search_history('streams', do_refresh=False))
        kodi.create_item({'label': i18n('streams'), 'path': {'mode': MODES.LISTSEARCH, 'content': 'streams'}, 'context_menu': context_menu,
                          'info': {'plot': '%s - %s' % (i18n('search'), i18n('streams'))}, 'thumbfile': 'Streams.png'})
        context_menu = list()
        context_menu.extend(menu_items.clear_search_history('channels', do_refresh=False))
        kodi.create_item({'label': i18n('channels'), 'path': {'mode': MODES.LISTSEARCH, 'content': 'channels'}, 'context_menu': context_menu,
                          'info': {'plot': '%s - %s' % (i18n('search'), i18n('channels'))}, 'thumbfile': 'Channels.png'})
        context_menu = list()
        context_menu.extend(menu_items.clear_search_history('games', do_refresh=False))
        kodi.create_item({'label': i18n('games'), 'path': {'mode': MODES.LISTSEARCH, 'content': 'games'}, 'context_menu': context_menu,
                          'info': {'plot': '%s - %s' % (i18n('search'), i18n('games'))}, 'thumbfile': 'Games.png'})
        context_menu = list()
        context_menu.extend(menu_items.clear_search_history('id_url', do_refresh=False))
        kodi.create_item({'label': i18n('video_id_url'), 'path': {'mode': MODES.LISTSEARCH, 'content': 'id_url'}, 'context_menu': context_menu,
                          'info': {'plot': '%s - %s[CR]%s' % (i18n('search'), i18n('video_id_url'), i18n('search_id_url_description'))}, 'thumbfile': 'Video_Url.png'})
    else:
        context_menu = list()
        kodi.create_item({'label': i18n('streams'), 'path': {'mode': MODES.NEWSEARCH, 'content': 'streams'}, 'context_menu': context_menu,
                          'info': {'plot': '%s - %s' % (i18n('search'), i18n('streams'))}, 'thumbfile': 'Streams.png'})
        kodi.create_item({'label': i18n('channels'), 'path': {'mode': MODES.NEWSEARCH, 'content': 'channels'},
                          'info': {'plot': '%s - %s' % (i18n('search'), i18n('channels'))}, 'thumbfile': 'Channels.png'})
        kodi.create_item({'label': i18n('games'), 'path': {'mode': MODES.NEWSEARCH, 'content': 'games'},
                          'info': {'plot': '%s - %s' % (i18n('search'), i18n('games'))}, 'thumbfile': 'Games.png'})
        kodi.create_item({'label': i18n('video_id_url'), 'path': {'mode': MODES.NEWSEARCH, 'content': 'id_url'},
                          'info': {'plot': '%s - %s[CR]%s' % (i18n('search'), i18n('video_id_url'), i18n('search_id_url_description'))}, 'thumbfile': 'Video_Url.png'})

    kodi.end_of_directory(cache_to_disc=False)
