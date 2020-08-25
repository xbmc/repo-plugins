# -*- coding: utf-8 -*-
"""

    Copyright (C) 2020 Composite (plugin.video.composite_for_plex)

    This file is part of Composite (plugin.video.composite_for_plex)

    SPDX-License-Identifier: GPL-2.0-or-later
    See LICENSES/GPL-2.0-or-later.txt for more information.
"""

from kodi_six import xbmc  # pylint: disable=import-error

from ..addon.dialogs.composite_playlist import composite_playlist
from ..addon.logger import Logger
from ..addon.utils import wait_for_busy_dialog
from ..plex import plex

LOG = Logger()


def run(context):
    context.plex_network = plex.Plex(context.settings, load=True)
    play = composite_playlist(context) and wait_for_busy_dialog()
    if play:
        xbmc.Player().play(item=xbmc.PlayList(xbmc.PLAYLIST_VIDEO), startpos=0)
