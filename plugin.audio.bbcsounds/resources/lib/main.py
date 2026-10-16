# ------------------------------------------------------------------------------
#  Copyright (c) 2026 Dimitri Kroon.
#  This file is part of plugin.audio.bbcsounds.
#  SPDX-License-Identifier: GPL-3.0-or-later
#  See LICENSE.txt or https://www.gnu.org/licenses/gpl-3.0.txt
# ------------------------------------------------------------------------------

import sys
from time import monotonic

import xbmc
import xbmcaddon
import xbmcplugin
import xbmcgui

from resources.lib import plugin
from resources.lib import exceptions
from resources.lib.log import log

addon_version = xbmcaddon.Addon().getAddonInfo('version')
log(f"------ Python version: {sys.version} ------")


def run():
    # noinspection PyBroadException
    try:
        start = monotonic()
        plugin.Plugin(sys.argv).run()
        log(f'Addon execution time: {monotonic() - start:0.3f} sec.')
        installed_version = xbmcaddon.Addon().getAddonInfo('version')
        if installed_version != addon_version:
            log(f"New version {installed_version} is installed while "
                f"version {addon_version} is currently running. Exiting now.")
            sys.exit(1)
    except exceptions.AddonError as err:
        xbmcgui.Dialog().notification('BBC Sounds',
                                      str(err),
                                      xbmcgui.NOTIFICATION_INFO,
                                      7000)
        xbmc.PlayList(xbmc.PLAYLIST_MUSIC).clear()
        xbmcplugin.endOfDirectory(int(sys.argv[1]), succeeded=False)
    except Exception as err:
        # A final catch-all to ensure that any unhandled exceptions are logged and we exit gracefully.
        log("ERROR: Unhandled exception:", exc_info=True)
        xbmcgui.Dialog().notification('BBC Sounds Error',
                                      str(err),
                                      xbmcgui.NOTIFICATION_ERROR,
                                      7000)
        xbmc.PlayList(xbmc.PLAYLIST_MUSIC).clear()
        sys.exit(1)
