# -*- coding: utf-8 -*-
"""

    Copyright (C) 2011-2018 PleXBMC (plugin.video.plexbmc) by hippojay (Dave Hawes-Johnson)
    Copyright (C) 2018-2020 Composite (plugin.video.composite_for_plex)

    This file is part of Composite (plugin.video.composite_for_plex)

    SPDX-License-Identifier: GPL-2.0-or-later
    See LICENSES/GPL-2.0-or-later.txt for more information.
"""

from kodi_six import xbmcplugin  # pylint: disable=import-error
from six import PY3

from ..common import get_handle
from ..containers import Item
from ..items.season import create_season_item
from ..logger import Logger
from ..utils import get_xml
from .episodes import process_episodes

LOG = Logger()


def process_seasons(context, url, rating_key=None, library=False):
    xbmcplugin.setContent(get_handle(), 'seasons')

    if not url.startswith(('http', 'file')) and rating_key:
        # Get URL, XML and parse
        server = context.plex_network.get_server_from_uuid(url)
        url = server.join_url(server.get_url_location(),
                              'library/metadata/%s/children' % str(rating_key))
    else:
        server = context.plex_network.get_server_from_url(url)

    tree = get_xml(context, url)
    if tree is None:
        return

    will_flatten = False
    if context.settings.flatten_seasons() == '1':
        # check for a single season
        if int(tree.get('size', 0)) == 1:
            LOG.debug('Flattening single season show')
            will_flatten = True

    all_season_disabled = context.settings.all_season_disabled()

    items = []
    append_item = items.append
    # For all the directory tags
    if PY3:
        seasons = tree.iter('Directory')
    else:
        seasons = tree.getiterator('Directory')

    for season in seasons:

        if will_flatten:
            url = server.join_url(server.get_url_location(), season.get('key'))
            process_episodes(context, url)
            return

        if all_season_disabled and season.get('index') is None:
            continue

        item = Item(server, url, tree, season)
        append_item(create_season_item(context, item, library=library))

    if items:
        xbmcplugin.addDirectoryItems(get_handle(), items, len(items))

    xbmcplugin.endOfDirectory(get_handle(), cacheToDisc=context.settings.cache_directory())
