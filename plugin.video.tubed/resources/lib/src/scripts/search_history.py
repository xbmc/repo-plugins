# -*- coding: utf-8 -*-
"""
    Copyright (C) 2020 Tubed (plugin.video.tubed)

    This file is part of plugin.video.tubed

    SPDX-License-Identifier: GPL-2.0-only
    See LICENSES/GPL-2.0-only.txt for more information.
"""

import xbmc  # pylint: disable=import-error

from ..lib.url_utils import unquote
from ..storage.search_history import SearchHistory
from ..storage.users import UserStorage


def invoke(context, action, item=''):
    history = SearchHistory(UserStorage().uuid, context.settings.search_history_maximum)

    if action == 'clear':
        history.clear()

    elif action == 'remove':
        if not item:
            return

        if '%' in item:
            item = unquote(item)

        history.remove(item)

    xbmc.executebuiltin('Container.Refresh')
