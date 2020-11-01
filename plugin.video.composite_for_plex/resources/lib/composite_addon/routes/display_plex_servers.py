# -*- coding: utf-8 -*-
"""

    Copyright (C) 2011-2018 PleXBMC (plugin.video.plexbmc) by hippojay (Dave Hawes-Johnson)
    Copyright (C) 2018-2020 Composite (plugin.video.composite_for_plex)

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
from ..addon.processing.music import process_music
from ..addon.processing.photos import process_photos
from ..addon.processing.plex_online import process_plex_online
from ..addon.processing.plex_plugins import process_plex_plugins
from ..plex import plex

LOG = Logger()


def run(context, url):
    context.plex_network = plex.Plex(context.settings, load=True)
    content_type = url.split('/')[2]
    LOG.debug('Displaying entries for %s' % content_type)
    servers = context.plex_network.get_server_list()
    servers_list = len(servers)

    items = []
    append_item = items.append
    # For each of the servers we have identified
    for media_server in servers:

        if media_server.is_secondary():
            continue

        details = {
            'title': media_server.get_name()
        }
        extra_data = {}
        url = None

        if content_type == 'video':
            extra_data['mode'] = MODES.PLEXPLUGINS
            url = media_server.join_url(media_server.get_url_location(), 'video')
            if servers_list == 1:
                process_plex_plugins(context, url)
                return

        elif content_type == 'online':
            extra_data['mode'] = MODES.PLEXONLINE
            url = media_server.join_url(media_server.get_url_location(), 'system/plexonline')
            if servers_list == 1:
                process_plex_online(context, url)
                return

        elif content_type == 'music':
            extra_data['mode'] = MODES.MUSIC
            url = media_server.join_url(media_server.get_url_location(), 'music')
            if servers_list == 1:
                process_music(context, url)
                return

        elif content_type == 'photo':
            extra_data['mode'] = MODES.PHOTOS
            url = media_server.join_url(media_server.get_url_location(), 'photos')
            if servers_list == 1:
                process_photos(context, url)
                return

        if url:
            gui_item = GUIItem(url, details, extra_data)
            append_item(create_gui_item(context, gui_item))

    if items:
        xbmcplugin.addDirectoryItems(get_handle(), items, len(items))

    xbmcplugin.endOfDirectory(get_handle(), cacheToDisc=context.settings.cache_directory())
