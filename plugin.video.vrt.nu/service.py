# -*- coding: utf-8 -*-

# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

''' This is the actual VRT NU service entry point '''

from __future__ import absolute_import, division, unicode_literals

import xbmc
from resources.lib import kodiwrapper, tokenresolver


class VrtMonitor(xbmc.Monitor):
    ''' This is the class that monitors Kodi for the VRT NU video plugin '''

    def __init__(self):
        ''' VRT Monitor initialisiation '''
        xbmc.Monitor.__init__(self)

    def onSettingsChanged(self):
        ''' Handler for changes to settings '''
        _kodi = kodiwrapper.KodiWrapper(None)
        _kodi.log_notice('VRT NU Addon: settings changed')
        _kodi.container_refresh()

        _kodi.invalidate_caches('offline-*.json')
        _kodi.invalidate_caches('recent-*.json')

        _tokenresolver = tokenresolver.TokenResolver(_kodi)
        _tokenresolver.delete_tokens()


if __name__ == '__main__':
    monitor = VrtMonitor()

    while not monitor.abortRequested():
        if monitor.waitForAbort(10):
            break
