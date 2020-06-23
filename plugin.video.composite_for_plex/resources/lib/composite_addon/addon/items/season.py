# -*- coding: utf-8 -*-
"""

    Copyright (C) 2011-2018 PleXBMC (plugin.video.plexbmc) by hippojay (Dave Hawes-Johnson)
    Copyright (C) 2018-2020 Composite (plugin.video.composite_for_plex)

    This file is part of Composite (plugin.video.composite_for_plex)

    SPDX-License-Identifier: GPL-2.0-or-later
    See LICENSES/GPL-2.0-or-later.txt for more information.
"""

from ..constants import MODES
from ..containers import GUIItem
from ..strings import encode_utf8
from ..strings import i18n
from .common import get_banner_image
from .common import get_fanart_image
from .common import get_thumb_image
from .context_menu import ContextMenu
from .gui import create_gui_item


def create_season_item(context, item, library=False):
    # Create the basic data structures to pass up
    info_labels = {
        'title': encode_utf8(item.data.get('title', i18n('Unknown'))),
        'TVShowTitle': encode_utf8(item.data.get('parentTitle', i18n('Unknown'))),
        'sorttitle': encode_utf8(item.data.get('titleSort',
                                               item.data.get('title', i18n('Unknown')))),
        'studio': encode_utf8(item.data.get('studio', '')),
        'plot': encode_utf8(item.tree.get('summary', '')),
        'season': item.data.get('index', 0),
        'episode': int(item.data.get('leafCount', 0)),
        'mpaa': item.data.get('contentRating', ''),
        'aired': item.data.get('originallyAvailableAt', ''),
        'mediatype': 'season'
    }

    if item.data.get('sorttitle'):
        info_labels['sorttitle'] = item.data.get('sorttitle')

    _watched = int(item.data.get('viewedLeafCount', 0))

    extra_data = {
        'type': 'video',
        'source': 'tvseasons',
        'TotalEpisodes': info_labels['episode'],
        'WatchedEpisodes': _watched,
        'UnWatchedEpisodes': info_labels['episode'] - _watched,
        'thumb': get_thumb_image(context, item.server, item.data),
        'fanart_image': get_fanart_image(context, item.server, item.data),
        'banner': get_banner_image(context, item.server, item.tree),
        'key': item.data.get('key', ''),
        'ratingKey': str(item.data.get('ratingKey', 0)),
        'mode': MODES.TVEPISODES
    }

    if extra_data['fanart_image'] == '':
        extra_data['fanart_image'] = get_fanart_image(context, item.server, item.tree)

    # Set up overlays for watched and unwatched episodes
    if extra_data['WatchedEpisodes'] == 0:
        info_labels['playcount'] = 0
    elif extra_data['UnWatchedEpisodes'] == 0:
        info_labels['playcount'] = 1
    else:
        extra_data['partialTV'] = 1

    item_url = item.server.join_url(item.server.get_url_location(), extra_data['key'])

    context_menu = None
    if not context.settings.skip_context_menus():
        context_menu = ContextMenu(context, item.server, item_url, item.data).menu

    if library:
        extra_data['path_mode'] = MODES.TXT_TVSHOWS_LIBRARY

    # Build the screen directory listing
    gui_item = GUIItem(item_url, info_labels, extra_data, context_menu)
    return create_gui_item(context, gui_item)
