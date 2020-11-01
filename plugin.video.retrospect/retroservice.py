# SPDX-License-Identifier: CC-BY-NC-SA-4.0

import xbmc
import xbmcaddon


def autorun_retrospect():
    if xbmcaddon.Addon().getSetting("auto_run") == "true":
        xbmc.executebuiltin('RunAddon(plugin.video.retrospect)')
    return


autorun_retrospect()
