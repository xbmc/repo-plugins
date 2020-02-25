# -*- coding: utf-8 -*-
"""

    Copyright (C) 2019 Composite (plugin.video.composite_for_plex)

    This file is part of Composite (plugin.video.composite_for_plex)

    SPDX-License-Identifier: GPL-2.0-or-later
    See LICENSES/GPL-2.0-or-later.txt for more information.
"""

from kodi_six import xbmc  # pylint: disable=import-error
from kodi_six import xbmcgui  # pylint: disable=import-error

from ..addon.common import get_argv
from ..addon.data_cache import DATA_CACHE
from ..addon.logger import Logger
from ..addon.strings import i18n
from ..plex import plex

LOG = Logger()


def run(context):
    context.plex_network = plex.Plex(context.settings, load=True)

    server_uuid = get_argv()[2]
    metadata_id = get_argv()[3]

    server = context.plex_network.get_server_from_uuid(server_uuid)

    result = xbmcgui.Dialog().yesno(i18n('Confirm playlist delete?'),
                                    i18n('Are you sure you want to delete this playlist?'))
    if result:
        _ = server.delete_playlist(metadata_id)
        DATA_CACHE.delete_cache(True)
        xbmc.executebuiltin('Container.Refresh')
