# -*- coding: utf-8 -*-
"""

    Copyright (C) 2011-2018 PleXBMC (plugin.video.plexbmc) by hippojay (Dave Hawes-Johnson)
    Copyright (C) 2018-2019 Composite (plugin.video.composite_for_plex)

    This file is part of Composite (plugin.video.composite_for_plex)

    SPDX-License-Identifier: GPL-2.0-or-later
    See LICENSES/GPL-2.0-or-later.txt for more information.
"""

from kodi_six import xbmcgui  # pylint: disable=import-error
from kodi_six import xbmcplugin  # pylint: disable=import-error

from ..addon.common import get_handle
from ..addon.constants import CONFIG
from ..addon.data_cache import DATA_CACHE
from ..addon.logger import Logger
from ..plex import plex

LOG = Logger()


def run(context, url):
    context.plex_network = plex.Plex(context.settings, load=True)
    if url.startswith('file'):
        LOG.debug('We are playing a local file')
        # Split out the path from the URL
        playback_url = url.split(':', 1)[1]
    elif url.startswith('http'):
        LOG.debug('We are playing a stream')
        if '?' in url:
            server = context.plex_network.get_server_from_url(url)
            playback_url = server.get_formatted_url(url)
        else:
            playback_url = ''
    else:
        playback_url = url

    if CONFIG['kodi_version'] >= 18:
        list_item = xbmcgui.ListItem(path=playback_url, offscreen=True)
    else:
        list_item = xbmcgui.ListItem(path=playback_url)

    xbmcplugin.setResolvedUrl(get_handle(), playback_url != '', list_item)
    DATA_CACHE.delete_cache(True)
