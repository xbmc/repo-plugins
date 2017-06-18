# -*- coding: utf-8 -*-
# 
# Massengeschmack Kodi add-on
# Copyright (C) 2013-2016 by Janek Bevendorff
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import xbmcgui
import json

from globalvars import *
import resources.lib as lib

# show warning and open settings if login data have not been configured
if '' == ADDON.getSetting('account.username') or '' == ADDON.getSetting('account.password'):
    dialog = xbmcgui.Dialog()
    dialog.ok(ADDON.getLocalizedString(30100), ADDON.getLocalizedString(30101))
    ADDON.openSettings()
    exit(1)

lib.installHTTPLoginData(ADDON.getSetting('account.username'), ADDON.getSetting('account.password'))

# if we're on the start page, verify login data first
if 'cmd' not in ADDON_ARGS:
    lib.handleHttpStatus(lib.probeLogin(showDialog=True))

# analyze URL
if 'cmd' not in ADDON_ARGS:
    ADDON_ARGS['cmd'] = 'list'

if 'list' == ADDON_ARGS['cmd']:
    listing    = lib.listing.Listing()
    datasource = lib.datasource.createDataSource(ADDON_ARGS.get('module', None))
    if listing.generate(datasource):
        listing.show()
    
elif 'play' == ADDON_ARGS['cmd']:
    name       = ADDON_ARGS.get('name', '')
    streamInfo = json.loads(ADDON_ARGS.get('streaminfo', '{}'))
    art        = json.loads(ADDON_ARGS.get('art', '{}'))

    lib.playVideoStream(ADDON_ARGS['url'], name, art, streamInfo)
    
else:
    raise RuntimeError(ADDON_ARGS['cmd'] + ': ' + ADDON.getLocalizedString(30901))
