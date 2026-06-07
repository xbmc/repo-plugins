#   Copyright (C) 2024 Lunatixz
#
#
# This file is part of iSpot.tv.
#
# iSpot.tv is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# iSpot.tv is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with iSpot.tv.  If not, see <http://www.gnu.org/licenses/>.

# -*- coding: utf-8 -*-

import sys, time

from resources.lib import ispot
from kodi_six      import xbmc, xbmcaddon, xbmcplugin, xbmcgui, xbmcvfs, py2_encode, py2_decode

# Plugin Info
ADDON_ID      = 'plugin.video.ispot.tv'
REAL_SETTINGS = xbmcaddon.Addon(id=ADDON_ID)

class Service(object):
    def __init__(self):
        self.myMonitor = xbmc.Monitor()
        self.running   = False
        self._start()
        
        
    def _check(self, key, runEvery=900):
        epoch = int(time.time())
        next  = int(xbmcgui.Window(10000).getProperty(key) or '0')
        if (epoch >= next):
            xbmcgui.Window(10000).setProperty(key,str(epoch+runEvery))
            return True
        return False

    
    def _start(self):
        while not self.myMonitor.abortRequested():
            if self.myMonitor.waitForAbort(5): break
            elif not self.running:
                self.running = True
                iservice = ispot.iSpotTV(sys.argv)
                if   self._check('queue',86400):  iservice.queDownloads()
                elif self._check('download',900): iservice.getDownloads()
                del iservice
                self.running = False
            
if __name__ == '__main__': Service()