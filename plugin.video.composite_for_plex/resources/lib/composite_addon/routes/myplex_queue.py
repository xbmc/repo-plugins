# -*- coding: utf-8 -*-
"""

    Copyright (C) 2011-2018 PleXBMC (plugin.video.plexbmc) by hippojay (Dave Hawes-Johnson)
    Copyright (C) 2018-2019 Composite (plugin.video.composite_for_plex)

    This file is part of Composite (plugin.video.composite_for_plex)

    SPDX-License-Identifier: GPL-2.0-or-later
    See LICENSES/GPL-2.0-or-later.txt for more information.
"""

from kodi_six import xbmcgui  # pylint: disable=import-error

from ..addon.constants import CONFIG
from ..addon.processing.plex_plugins import process_plex_plugins
from ..addon.strings import i18n
from ..plex import plex


def run(context):
    context.plex_network = plex.Plex(context.settings, load=True)
    if not context.plex_network.is_myplex_signedin():
        xbmcgui.Dialog().notification(heading=CONFIG['name'],
                                      message=i18n('myPlex not configured'),
                                      icon=CONFIG['icon'])
    else:
        tree = context.plex_network.get_myplex_queue()
        process_plex_plugins(context, 'https://plex.tv/playlists/queue/all', tree)
