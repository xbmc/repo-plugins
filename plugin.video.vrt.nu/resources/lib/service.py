# -*- coding: utf-8 -*-
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
''' This is the actual VRT NU service entry point '''

# pylint: disable=non-parent-init-called,no-member,too-many-function-args

from __future__ import absolute_import, division, unicode_literals
from xbmc import Monitor
from kodiwrapper import KodiWrapper
from tokenresolver import TokenResolver


class VrtMonitor(Monitor):
    ''' This is the class that monitors Kodi for the VRT NU video plugin '''

    def __init__(self):
        ''' VRT Monitor initialisiation '''
        Monitor.__init__(self)
        while not self.abortRequested():
            if self.waitForAbort(10):
                break

    def onNotification(self, sender, method, data):
        ''' Handler for notifications '''
        _kodi = KodiWrapper(None)
        _kodi.log_notice('Got a notification: %s, %s, %s' % (sender, method, data), 'Verbose')

    def onSettingsChanged(self):
        ''' Handler for changes to settings '''
        _kodi = KodiWrapper(None)
        _kodi.log_notice('Settings changed')

        _kodi.invalidate_caches('offline-*.json')
        _kodi.invalidate_caches('recent-*.json')

        TokenResolver(_kodi).refresh_login()
        _kodi.container_refresh()
