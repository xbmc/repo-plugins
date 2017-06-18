#   Copyright (C) 2017 Lunatixz
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
import pycountry
import xbmcgui, xbmcaddon

# Plugin Info
ADDON_ID      = 'plugin.video.plutotv'
REAL_SETTINGS = xbmcaddon.Addon(id=ADDON_ID)
ADDON_NAME    = REAL_SETTINGS.getAddonInfo('name')
LANGUAGE      = REAL_SETTINGS.getLocalizedString
COUNTRY_LIST  = list(pycountry.countries)

def getCountryList():
    for country in COUNTRY_LIST:
        yield (country.name)
        
def getAlpha2(idx):
    if idx < 0 or not idx:
        return 'US'
    return str((COUNTRY_LIST[idx]).alpha_2)
        
def selectDialog(list, header=ADDON_NAME):
    select = xbmcgui.Dialog().select(LANGUAGE(30005), list)
    if select > -1:
        return select
        
if __name__ == '__main__':
    REAL_SETTINGS.setSetting("Select_Country",getAlpha2(selectDialog(list(getCountryList()),LANGUAGE(30005))))