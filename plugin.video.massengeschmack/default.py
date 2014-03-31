# -*- coding: utf-8 -*-
# 
# Massengeschmack XBMC add-on
# Copyright (C) 2013 by Janek Bevendorff
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

import xbmc
import xbmcgui
import xbmcaddon
import xbmcplugin
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
if not 'cmd' in ADDON_ARGS:
    response = lib.fetchSubscriptions(True)
    if 200 != response['code']:
        dialog = xbmcgui.Dialog()
        if -1 == response['code']:
            dialog.ok(ADDON.getLocalizedString(30902), ADDON.getLocalizedString(30903) + '[CR]Error: {0}'.format(response['reason']))
        elif 401 == response['code']:
            dialog.ok(ADDON.getLocalizedString(30102), ADDON.getLocalizedString(30103))
            ADDON.openSettings()
        else:
            dialog.ok(ADDON.getLocalizedString(30902), ADDON.getLocalizedString(30904) + '[CR]Error: {0} {1}'.format(response['code'], response['reason']))
        exit(1)
    
    # if all went well, cache subscriptions
    lib.cacheSubscriptions(response['subscriptions'])


# analyze URL
if not 'cmd' in ADDON_ARGS:
    ADDON_ARGS['cmd'] = 'list'

if 'list' == ADDON_ARGS['cmd']:
    listing    = lib.Listing()
    datasource = None
    if 'module' in ADDON_ARGS:
        datasource = lib.datasource.createDataSource(ADDON_ARGS['module'])
    else:
        datasource = lib.datasource.createDataSource()
    listing.generate(datasource)
    listing.show()
    
elif 'play' == ADDON_ARGS['cmd']:
    name       = ''
    iconImage  = ''
    metaData   = {}
    streamInfo = {}
    if 'name' in ADDON_ARGS:
        name = ADDON_ARGS['name']
    if 'iconimage' in ADDON_ARGS:
        iconImage = ADDON_ARGS['iconimage']
    if 'metadata' in ADDON_ARGS:
        metaData = json.loads(ADDON_ARGS['metadata'])
    if 'streaminfo' in ADDON_ARGS:
        streamInfo = json.loads(ADDON_ARGS['streaminfo'])
    
    listitem = xbmcgui.ListItem(name, iconImage=iconImage, thumbnailImage=iconImage)
    listitem.setInfo('video', metaData)
    if not IS_XBOX:
        listitem.addStreamInfo('video', streamInfo)
    playlist = xbmc.PlayList(1)
    playlist.clear()
    playlist.add(ADDON_ARGS['url'], listitem)
    xbmc.Player().play(playlist)
    playlist.clear()
    
else:
    raise RuntimeError(ADDON_ARGS['cmd'] + ': ' + ADDON.getLocalizedString(30901)) 