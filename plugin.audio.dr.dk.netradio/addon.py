#
#      Copyright (C) 2011 Tommy Winther
#      http://tommy.winther.nu
#
#  This Program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2, or (at your option)
#  any later version.
#
#  This Program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with XBMC; see the file COPYING.  If not, write to
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#  http://www.gnu.org/copyleft/gpl.html
#
import os
import sys
import simplejson
import urllib2
import buggalo

import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmcvfs

CHANNELS_URL = 'http://www.dr.dk/LiveNetRadio/datafeed/channels.js.drxml'

def showChannels():
    u = urllib2.urlopen(CHANNELS_URL)
    data = u.read()
    u.close()

    channels = simplejson.loads(data[39:-3])
    for channel in channels:
        logoImage = os.path.join(LOGO_PATH, channel['source_url'] + '.png')
        if xbmcvfs.exists(logoImage):
            item = xbmcgui.ListItem(channel['title'], iconImage = logoImage)
        else:
            item = xbmcgui.ListItem(channel['title'], iconImage = ICON)

        item.setProperty('IsPlayable', 'true')
        item.setProperty('Fanart_Image', FANART)
        item.setInfo(type = 'audio', infoLabels = {
                'title' : channel['title']
        })

        if type(channel['mediaFile']) is list:
            url = channel['mediaFile'][0]
        else:
            url = channel['mediaFile']
        xbmcplugin.addDirectoryItem(HANDLE, url + ' live=1', item)

    xbmcplugin.endOfDirectory(HANDLE)

if __name__ == '__main__':
    ADDON = xbmcaddon.Addon()
    HANDLE = int(sys.argv[1])

    LOGO_PATH = os.path.join(ADDON.getAddonInfo('path'), 'resources', 'logos')
    ICON = os.path.join(ADDON.getAddonInfo('path'), 'icon.png')
    FANART = os.path.join(ADDON.getAddonInfo('path'), 'fanart.jpg')

    try:
        showChannels()
    except Exception:
        buggalo.onExceptionRaised()

