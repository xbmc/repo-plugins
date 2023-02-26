# -*- coding: utf-8 -*-
"""
    Copyright (C) 2020 Tubed (plugin.video.tubed)

    This file is part of plugin.video.tubed

    SPDX-License-Identifier: GPL-2.0-only
    See LICENSES/GPL-2.0-only.txt for more information.
"""

from urllib.parse import quote

import xbmcgui  # pylint: disable=import-error
import xbmcplugin  # pylint: disable=import-error

from ..constants import ADDON_ID
from ..constants import MODES
from ..constants import SCRIPT_MODES
from ..items.directory import Directory
from ..items.search_query import SearchQuery
from ..lib.txt_fmt import bold
from ..lib.url_utils import create_addon_path
from ..storage.search_history import SearchHistory
from ..storage.users import UserStorage


def invoke(context):
    items = []

    directory = SearchQuery(
        label=bold(context.i18n('New Search')),
        path=create_addon_path(parameters={
            'mode': str(MODES.SEARCH_QUERY)
        })
    )
    items.append(tuple(directory))

    if context.settings.search_history_maximum > 0:
        history = SearchHistory(UserStorage().uuid, context.settings.search_history_maximum)

        for query in history.list():
            directory = Directory(
                label=query,
                path=create_addon_path(parameters={
                    'mode': str(MODES.SEARCH_QUERY),
                    'query': quote(query)
                })
            )

            context_menus = [
                (context.i18n('Remove...'),
                 'RunScript(%s,mode=%s&action=remove&item=%s)' %
                 (ADDON_ID, str(SCRIPT_MODES.SEARCH_HISTORY), quote(query))),

                (context.i18n('Clear history'),
                 'RunScript(%s,mode=%s&action=clear)' %
                 (ADDON_ID, str(SCRIPT_MODES.SEARCH_HISTORY))),
            ]

            directory.ListItem.addContextMenuItems(context_menus)
            items.append(tuple(directory))

    if items:
        xbmcplugin.addDirectoryItems(context.handle, items, len(items))

        xbmcplugin.endOfDirectory(context.handle, True)

    else:
        xbmcgui.Dialog().notification(context.addon.getAddonInfo('name'),
                                      context.i18n('No entries found'),
                                      context.addon.getAddonInfo('icon'),
                                      sound=False)
        xbmcplugin.endOfDirectory(context.handle, False)
