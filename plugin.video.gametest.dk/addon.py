#
#      Copyright (C) 2013 Tommy Winther
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
#  along with this Program; see the file LICENSE.txt. If not, write to
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#  http://www.gnu.org/copyleft/gpl.html
#
import re
import os
import sys
import urllib2
import buggalo

import xbmcgui
import xbmcaddon
import xbmcplugin

BASE_URL = 'http://www.gametest.dk/'
PLAY_VIDEO_PATH = 'plugin://plugin.video.youtube/?action=play_video&videoid=%s'
PLAYLIST_PATH = 'plugin://plugin.video.youtube/?channel=GametestDanmark&path=%2froot%2fsubscriptions&user_feed=uploads'


if __name__ == '__main__':
    ADDON = xbmcaddon.Addon()
    HANDLE = int(sys.argv[1])

    ICON = os.path.join(ADDON.getAddonInfo('path'), 'icon.png')
    FANART = os.path.join(ADDON.getAddonInfo('path'), 'fanart.jpg')

    try:
        u = urllib2.urlopen(BASE_URL)
        html = u.read()
        u.close()

        m = re.search('//www.youtube.com/embed/([^"]+)"', html, re.DOTALL)
        if m:
            videoId = m.group(1)
            item = xbmcgui.ListItem(ADDON.getLocalizedString(30000), iconImage=ICON)
            item.setProperty('Fanart_Image', FANART)
            item.setProperty("IsPlayable", "true")
            xbmcplugin.addDirectoryItem(HANDLE, PLAY_VIDEO_PATH % videoId, item)

            item = xbmcgui.ListItem(ADDON.getLocalizedString(30001), iconImage=ICON)
            item.setProperty('Fanart_Image', FANART)
            xbmcplugin.addDirectoryItem(HANDLE, PLAYLIST_PATH, item, True)

        xbmcplugin.endOfDirectory(HANDLE)
    except:
        buggalo.onExceptionRaised()

