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
    for section in sections:
        if section.is_movie():
            items += movie_widgets(context, server, section)

        if section.is_show():
            items += tvshow_widgets(context, server, section)

    if items:
        items += all_server_widgets(context)

    if items:
        xbmcplugin.addDirectoryItems(get_handle(), items, len(items))

    xbmcplugin.endOfDirectory(get_handle(), cacheToDisc=context.settings.cache_directory())


def movie_widgets(context, server, section):
    items = []
    append_item = items.append
    details = {
        'title': '%s: %s' % (section.get_title(), i18n('On Deck'))
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
        'title': '%s: %s' % (section.get_title(), i18n('Recently Added'))
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
        'title': '%s: %s' % (section.get_title(), i18n('Recently Released'))
    }
    extra_data = {
        'mode': MODES.TXT_MOVIES_RECENT_RELEASE,
        'parameters': {
            'server_uuid': server.get_uuid()
        }
    }
    gui_item = GUIItem(section.get_path(), details, extra_data)
    append_item(create_gui_item(context, gui_item))

    return items


def tvshow_widgets(context, server, section):
    items = []
    append_item = items.append

    details = {
        'title': '%s: %s' % (section.get_title(), i18n('On Deck'))
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
        'title': '%s: %s' % (section.get_title(), i18n('Recently Added'))
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
        'title': '%s: %s' % (section.get_title(), i18n('Recently Aired'))
    }
    extra_data = {
        'mode': MODES.TXT_TVSHOWS_RECENT_AIRED,
        'parameters': {
            'server_uuid': server.get_uuid()
        }
    }
    gui_item = GUIItem(section.get_path(), details, extra_data)
    append_item(create_gui_item(context, gui_item))

    return items


def all_server_widgets(context):
    items = []
    append_item = items.append

    details = {
        'title': i18n('All Servers: TV Shows On Deck')
    }
    extra_data = {
        'type': 'Folder',
        'mode': MODES.TVSHOWS_ON_DECK
    }

    gui_item = GUIItem('/library/onDeck', details, extra_data)
    append_item(create_gui_item(context, gui_item))

    details = {
        'title': i18n('All Servers: Movies On Deck')
    }
    extra_data = {
        'type': 'Folder',
        'mode': MODES.MOVIES_ON_DECK
    }

    gui_item = GUIItem('/library/onDeck', details, extra_data)
    append_item(create_gui_item(context, gui_item))

    details = {
        'title': i18n('All Servers: Recently Added Episodes')
    }
    extra_data = {
        'type': 'Folder',
        'mode': MODES.EPISODES_RECENTLY_ADDED
    }

    gui_item = GUIItem('/library/recentlyAdded', details, extra_data)
    append_item(create_gui_item(context, gui_item))

    details = {
        'title': i18n('All Servers: Recently Added Movies')
    }
    extra_data = {
        'type': 'Folder',
        'mode': MODES.MOVIES_RECENTLY_ADDED
    }

    gui_item = GUIItem('/library/recentlyAdded', details, extra_data)
    append_item(create_gui_item(context, gui_item))

    return items
