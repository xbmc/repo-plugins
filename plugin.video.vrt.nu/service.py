# -*- coding: utf-8 -*-

# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

''' This is the actual VRT Nu service entry point '''

from __future__ import absolute_import, division, unicode_literals

import xbmc
import xbmcaddon
from resources.lib.kodiwrappers import kodiwrapper
from resources.lib.vrtplayer import tokenresolver


class VrtMonitor(xbmc.Monitor):
    ''' This is the class that monitors Kodi for the VRT Nu video plugin '''

    def __init__(self):
        ''' VRT Monitor initialisiation '''
        xbmc.Monitor.__init__(self)

    def onSettingsChanged(self):
        ''' Handler for changes to settings '''
        addon = xbmcaddon.Addon(id='plugin.video.vrt.nu')
        kodi_wrapper = kodiwrapper.KodiWrapper(None, None, addon)
        kodi_wrapper.log_notice('VRT NU Addon: settings changed')
        token_resolver = tokenresolver.TokenResolver(kodi_wrapper)
        token_resolver.reset_cookies()


if __name__ == '__main__':
    monitor = VrtMonitor()

    while not monitor.abortRequested():
        if monitor.waitForAbort(10):
            break
