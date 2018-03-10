#   Copyright (C) 2018 Lunatixz
#
#
# This file is part of PlutoTV.
#
# PlutoTV is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PlutoTV is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with PlutoTV.  If not, see <http://www.gnu.org/licenses/>.

# -*- coding: utf-8 -*-
import os, json
import xbmcgui, xbmcaddon, xbmcvfs

# Plugin Info
ADDON_ID      = 'plugin.video.plutotv'
REAL_SETTINGS = xbmcaddon.Addon(id=ADDON_ID)
ADDON_NAME    = REAL_SETTINGS.getAddonInfo('name')
SETTINGS_LOC  = REAL_SETTINGS.getAddonInfo('profile')
ADDON_PATH    = REAL_SETTINGS.getAddonInfo('path').decode('utf-8')
ADDON_VERSION = REAL_SETTINGS.getAddonInfo('version')
ICON          = REAL_SETTINGS.getAddonInfo('icon')
FANART        = REAL_SETTINGS.getAddonInfo('fanart')
LANGUAGE      = REAL_SETTINGS.getLocalizedString

## GLOBALS ##
USER_REGION   = REAL_SETTINGS.getSetting("Select_Country")
ISO3166       = os.path.join(ADDON_PATH,'resources','iso3166-1.json')
COUNTRY_LIST  = sorted((json.load(xbmcvfs.File(ISO3166)))['3166-1'], key=lambda x: x['name'])

def getCurrentRegion():
    for idx, country in enumerate(COUNTRY_LIST):
        if country['alpha_2'] == USER_REGION: return idx
    return 0
    
def getCountryList():
    for country in COUNTRY_LIST: yield (country['name'])
        
def getAlpha2(idx):
    if idx is None or idx < 0: return 'US'
    return str((COUNTRY_LIST[idx])['alpha_2'])
        
def selectDialog(list, header=ADDON_NAME):
    select = xbmcgui.Dialog().select(LANGUAGE(30005), list, preselect=getCurrentRegion())
    if select > -1: return select
        
if __name__ == '__main__':
    REAL_SETTINGS.setSetting("Select_Country",getAlpha2(selectDialog(list(getCountryList()),LANGUAGE(30005))))