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
#  along with this Program; see the file LICENSE.txt.  If not, write to
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#  http://www.gnu.org/copyleft/gpl.html
#
import os
import sys

import buggalo

import xbmcgui
import xbmcaddon
import xbmcplugin

FEEDS = {
    30100: 'rss://borsen.dk/podcast/alle',
    30101: 'rss://borsen.dk/podcast/investor',
    30103: 'rss://borsen.dk/podcast/karriere',
    30104: 'rss://borsen.dk/podcast/politik',
    30105: 'rss://borsen.dk/podcast/privatokonomi',
    30106: 'rss://borsen.dk/podcast/okonomi',
    30107: 'rss://borsen.dk/podcast/finans'
}

if __name__ == '__main__':
    ADDON = xbmcaddon.Addon()
    HANDLE = int(sys.argv[1])
    ICON = os.path.join(ADDON.getAddonInfo('path'), 'icon.png')
    FANART = os.path.join(ADDON.getAddonInfo('path'), 'fanart.jpg')

    buggalo.SUBMIT_URL = 'http://tommy.winther.nu/exception/submit.php'
    try:
        for stringId in FEEDS.keys():
            item = xbmcgui.ListItem(ADDON.getLocalizedString(stringId), iconImage=ICON)
            item.setProperty('Fanart_Image', FANART)
            xbmcplugin.addDirectoryItem(HANDLE, FEEDS[stringId], item, isFolder=True)

        xbmcplugin.endOfDirectory(HANDLE)
    except Exception:
        buggalo.onExceptionRaised()
