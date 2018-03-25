#   Copyright (C) 2018 Lunatixz
#
#
# This file is part of HDHomerun Simple
#
# HDHomerun Simple is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# HDHomerun Simple is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with HDHomerun Simple. If not, see <http://www.gnu.org/licenses/>.

# -*- coding: utf-8 -*-
import traceback
import xbmc, xbmcgui, xbmcaddon

from pyhdhr import PyHDHR

# Plugin Info
ADDON_ID      = 'plugin.video.hdhomerun.simple'
REAL_SETTINGS = xbmcaddon.Addon(id=ADDON_ID)
ADDON_NAME    = REAL_SETTINGS.getAddonInfo('name')
SETTINGS_LOC  = REAL_SETTINGS.getAddonInfo('profile')
ADDON_PATH    = REAL_SETTINGS.getAddonInfo('path').decode('utf-8')
ADDON_VERSION = REAL_SETTINGS.getAddonInfo('version')
ICON          = REAL_SETTINGS.getAddonInfo('icon')
FANART        = REAL_SETTINGS.getAddonInfo('fanart')
LANGUAGE      = REAL_SETTINGS.getLocalizedString

## GLOBALS ##
DEBUG         = REAL_SETTINGS.getSetting('Enable_Debugging') == 'true'
  
def log(msg, level=xbmc.LOGDEBUG):
    if DEBUG == False and level != xbmc.LOGERROR: return
    if level == xbmc.LOGERROR: msg += ' ,' + traceback.format_exc()
    xbmc.log(ADDON_ID + '-' + ADDON_VERSION + '-' + msg, level)
 
def setSetting(string1, value):
    log("setSetting, string = " + str(string1) + ", value = " + str(value))
    REAL_SETTINGS.setSetting(string1,value)

class Service(object):
    def __init__(self):
        self.pyHDHR = PyHDHR.PyHDHR()
        self.tuners = self.pyHDHR.getTuners()
        xbmc.sleep(1000)
        self.fillTuners()

        
    def fillTuners(self):
        setSetting('HDHR.TotalDevices',str(len(self.tuners)))
        for idx, tunerkey in enumerate(self.tuners):
            idx+=1
            setSetting('HDHR.FriendlyName.%d'    %idx,'%s - %s'%(self.tuners[tunerkey].FriendlyName,tunerkey))
            setSetting('HDHR.FirmwareName.%d'    %idx,'%s - %s'%(self.tuners[tunerkey].FirmwareName.upper(),self.tuners[tunerkey].FirmwareVersion))
            setSetting('HDHR.TunerCount.%d'      %idx,str(self.tuners[tunerkey].TunerCount))
            setSetting('HDHR.LocalIP.%d'         %idx,str(self.tuners[tunerkey].getLocalIP()))
            setSetting('HDHR.TranscodeOption.%d' %idx,str(self.tuners[tunerkey].TranscodeOption))  
        
if __name__ == '__main__': Service()