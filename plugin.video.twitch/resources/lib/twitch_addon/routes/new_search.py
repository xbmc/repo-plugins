# -*- coding: utf-8 -*-
"""

    Copyright (C) 2012-2018 Twitch-on-Kodi

    This file is part of Twitch-on-Kodi (plugin.video.twitch)

    SPDX-License-Identifier: GPL-3.0-only
    See LICENSES/GPL-3.0-only for more information.
"""
from ..addon.common import kodi
from ..addon.utils import i18n


def _query_key(content):
    return kodi.get_id() + '-new_search_query-' + content


def clear_query(content):
    # Called by the search menus (search.py / search_history.py) right before the user can
    # click "New Search", so a deliberate New Search always prompts the keyboard again.
    kodi.Window(10000).clearProperty(_query_key(content))


def route(api, content):
    # Render results inline. A Container.Update redirect to a dedicated search_results
    # container would be cleaner, but it is reliably *swallowed* under
    # reuselanguageinvoker=true (empty result list) -- verified on both SZ (2026-06-17)
    # and WZ (2026-06-21, issue #1), with succeeded=True and succeeded=False alike.
    #
    # Inline render leaves the folder path at new_search, so Kodi reloads this route when
    # returning from playback. Plain inline then re-popped the keyboard, and (issue #1)
    # cancelling it hung at "Working..." (route returned without end_of_directory) until
    # CScriptRunner killed the script after 12 min.
    #
    # Fix: remember the entered query in a window property. On the post-playback reload the
    # property is set -> re-render the previous results instead of re-prompting. The search
    # menus clear the property before "New Search" is reachable, so a deliberate new search
    # still prompts. An empty/cancelled keyboard ends the directory cleanly (no hang).
    from . import search_results

    win = kodi.Window(10000)
    key = _query_key(content)
    previous = win.getProperty(key)

    if previous:
        search_results.route(api, content, previous)
        return

    user_input = kodi.get_keyboard(i18n('search'))
    if not user_input:
        kodi.end_of_directory(succeeded=False)
        return

    win.setProperty(key, user_input)
    search_results.route(api, content, user_input)
