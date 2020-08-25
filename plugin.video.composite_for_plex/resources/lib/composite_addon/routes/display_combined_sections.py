# -*- coding: utf-8 -*-
"""

    Copyright (C) 2020 Composite (plugin.video.composite_for_plex)

    This file is part of Composite (plugin.video.composite_for_plex)

    SPDX-License-Identifier: GPL-2.0-or-later
    See LICENSES/GPL-2.0-or-later.txt for more information.
"""

from kodi_six import xbmcplugin  # pylint: disable=import-error

from ..addon.common import get_handle
from ..addon.constants import MODES
from ..addon.containers import GUIItem
from ..addon.items.gui import create_gui_item
from ..addon.logger import Logger
from ..addon.strings import i18n
from ..plex import plex

LOG = Logger()


def run(context):
    context.plex_network = plex.Plex(context.settings, load=True)
    xbmcplugin.setContent(get_handle(), 'files')

    server_list = context.plex_network.get_server_list()
    LOG.debug('Using list of %s servers: %s' % (len(server_list), server_list))

    items = get_menu_items(context)

    if items:
        xbmcplugin.addDirectoryItems(get_handle(), items, len(items))

    xbmcplugin.endOfDirectory(get_handle(), cacheToDisc=context.settings.cache_directory())


def get_menu_items(context):
    items = []

    details = {
        'title': i18n('TV Shows on Deck')
    }
    extra_data = {
        'type': 'Folder',
        'mode': MODES.TVSHOWS_ON_DECK
    }

    gui_item = GUIItem('/library/onDeck', details, extra_data)
    items.append(create_gui_item(context, gui_item))

    details = {
        'title': i18n('Movies on Deck')
    }
    extra_data = {
        'type': 'Folder',
        'mode': MODES.MOVIES_ON_DECK
    }

    gui_item = GUIItem('/library/onDeck', details, extra_data)
    items.append(create_gui_item(context, gui_item))

    details = {
        'title': i18n('Recently Added Episodes')
    }
    extra_data = {
        'type': 'Folder',
        'mode': MODES.EPISODES_RECENTLY_ADDED
    }

    gui_item = GUIItem('/library/recentlyAdded', details, extra_data)
    items.append(create_gui_item(context, gui_item))

    details = {
        'title': i18n('Recently Added Movies')
    }
    extra_data = {
        'type': 'Folder',
        'mode': MODES.MOVIES_RECENTLY_ADDED
    }

    gui_item = GUIItem('/library/recentlyAdded', details, extra_data)
    items.append(create_gui_item(context, gui_item))

    details = {
        'title': i18n('All Movies')
    }
    extra_data = {
        'type': 'Folder',
        'mode': MODES.MOVIES_ALL
    }

    gui_item = GUIItem('/library/all_movies', details, extra_data)
    items.append(create_gui_item(context, gui_item))

    details = {
        'title': i18n('All Shows')
    }
    extra_data = {
        'type': 'Folder',
        'mode': MODES.TVSHOWS_ALL
    }

    gui_item = GUIItem('/library/all_shows', details, extra_data)
    items.append(create_gui_item(context, gui_item))

    details = {
        'title': i18n('All Artists')
    }
    extra_data = {
        'type': 'Folder',
        'mode': MODES.ARTISTS_ALL
    }

    gui_item = GUIItem('/library/all_artists', details, extra_data)
    items.append(create_gui_item(context, gui_item))

    details = {
        'title': i18n('All Photos')
    }
    extra_data = {
        'type': 'Folder',
        'mode': MODES.PHOTOS_ALL
    }

    gui_item = GUIItem('/library/all_photos', details, extra_data)
    items.append(create_gui_item(context, gui_item))

    details = {
        'title': i18n('Search Movies...')
    }
    extra_data = {
        'type': 'Folder',
        'mode': MODES.MOVIES_SEARCH_ALL
    }

    gui_item = GUIItem('/library/search_all_movies', details, extra_data)
    items.append(create_gui_item(context, gui_item))

    details = {
        'title': i18n('Search Shows...')
    }
    extra_data = {
        'type': 'Folder',
        'mode': MODES.TVSHOWS_SEARCH_ALL
    }

    gui_item = GUIItem('/library/search_all_shows', details, extra_data)
    items.append(create_gui_item(context, gui_item))

    details = {
        'title': i18n('Search Episodes...')
    }
    extra_data = {
        'type': 'Folder',
        'mode': MODES.EPISODES_SEARCH_ALL
    }

    gui_item = GUIItem('/library/search_all_episodes', details, extra_data)
    items.append(create_gui_item(context, gui_item))

    details = {
        'title': i18n('Search Artists...')
    }
    extra_data = {
        'type': 'Folder',
        'mode': MODES.ARTISTS_SEARCH_ALL
    }

    gui_item = GUIItem('/library/search_all_artists', details, extra_data)
    items.append(create_gui_item(context, gui_item))

    details = {
        'title': i18n('Search Albums...')
    }
    extra_data = {
        'type': 'Folder',
        'mode': MODES.ALBUMS_SEARCH_ALL
    }

    gui_item = GUIItem('/library/search_all_albums', details, extra_data)
    items.append(create_gui_item(context, gui_item))

    details = {
        'title': i18n('Search Tracks...')
    }
    extra_data = {
        'type': 'Folder',
        'mode': MODES.TRACKS_SEARCH_ALL
    }

    gui_item = GUIItem('/library/search_all_tracks', details, extra_data)
    items.append(create_gui_item(context, gui_item))

    return items
