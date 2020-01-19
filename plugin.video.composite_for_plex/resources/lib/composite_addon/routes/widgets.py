# -*- coding: utf-8 -*-
"""

    Copyright (C) 2019-2020 Composite (plugin.video.composite_for_plex)

    This file is part of Composite (plugin.video.composite_for_plex)

    SPDX-License-Identifier: GPL-2.0-or-later
    See LICENSES/GPL-2.0-or-later.txt for more information.
"""

from kodi_six import xbmcplugin  # pylint: disable=import-error

from ..addon.common import get_handle
from ..addon.constants import MODES
from ..addon.containers import GUIItem
from ..addon.items.gui import create_gui_item
from ..addon.strings import i18n
from ..plex import plex


def run(context, url):
    context.plex_network = plex.Plex(context.settings, load=True)
    server = context.plex_network.get_server_from_url(url)

    sections = server.get_sections()

    items = []
    append_item = items.append
    for section in sections:
        if section.is_movie():
            details = {
                'title': '%s: %s' % (server.get_name(), i18n('Movies on Deck'))
            }
            extra_data = {
                'mode': MODES.TXT_MOVIES_ON_DECK,
                'parameters': {
                    'server_uuid': server.get_uuid()
                }
            }
            gui_item = GUIItem(section.get_path(), details, extra_data)
            append_item(create_gui_item(context, gui_item))

            details = {
                'title': '%s: %s' % (server.get_name(), i18n('Recently Added Movies'))
            }
            extra_data = {
                'mode': MODES.TXT_MOVIES_RECENT_ADDED,
                'parameters': {
                    'server_uuid': server.get_uuid()
                }
            }
            gui_item = GUIItem(section.get_path(), details, extra_data)
            append_item(create_gui_item(context, gui_item))

            details = {
                'title': '%s: %s' % (server.get_name(), i18n('Recently Released Movies'))
            }
            extra_data = {
                'mode': MODES.TXT_MOVIES_RECENT_RELEASE,
                'parameters': {
                    'server_uuid': server.get_uuid()
                }
            }
            gui_item = GUIItem(section.get_path(), details, extra_data)
            append_item(create_gui_item(context, gui_item))

        if section.is_show():
            details = {
                'title': '%s: %s' % (server.get_name(), i18n('TV Shows on Deck'))
            }
            extra_data = {
                'mode': MODES.TXT_TVSHOWS_ON_DECK,
                'parameters': {
                    'server_uuid': server.get_uuid()
                }
            }
            gui_item = GUIItem(section.get_path(), details, extra_data)
            append_item(create_gui_item(context, gui_item))

            details = {
                'title': '%s: %s' % (server.get_name(), i18n('Recently Added TV Shows'))
            }
            extra_data = {
                'mode': MODES.TXT_TVSHOWS_RECENT_ADDED,
                'parameters': {
                    'server_uuid': server.get_uuid()
                }
            }
            gui_item = GUIItem(section.get_path(), details, extra_data)
            append_item(create_gui_item(context, gui_item))

            details = {
                'title': '%s: %s' % (server.get_name(), i18n('Recently Aired TV Shows'))
            }
            extra_data = {
                'mode': MODES.TXT_TVSHOWS_RECENT_AIRED,
                'parameters': {
                    'server_uuid': server.get_uuid()
                }
            }
            gui_item = GUIItem(section.get_path(), details, extra_data)
            append_item(create_gui_item(context, gui_item))

    if items:
        xbmcplugin.addDirectoryItems(get_handle(), items, len(items))

    xbmcplugin.endOfDirectory(get_handle(), cacheToDisc=context.settings.cache_directory())
