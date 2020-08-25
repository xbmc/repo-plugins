# -*- coding: utf-8 -*-
"""

    Copyright (C) 2020-2020 Composite (plugin.video.composite_for_plex)

    This file is part of Composite (plugin.video.composite_for_plex)

    SPDX-License-Identifier: GPL-2.0-or-later
    See LICENSES/GPL-2.0-or-later.txt for more information.
"""

from kodi_six import xbmc  # pylint: disable=import-error

from ..addon.constants import CONFIG
from ..addon.dialogs.skip_intro import SkipIntroDialog


def run():
    monitor = xbmc.Monitor()
    dialog = SkipIntroDialog('skip_intro.xml',
                             CONFIG['addon'].getAddonInfo('path'),
                             'default', '720p', intro_end=1000000)
    xbmc.executebuiltin('Dialog.Close(all,true)')
    dialog.show()
    monitor.waitForAbort(0.5)
    while not monitor.abortRequested() and dialog.showing:
        if monitor.waitForAbort(0.5):
            break
    dialog.close()
