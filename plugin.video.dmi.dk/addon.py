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
#  along with XBMC; see the file COPYING.  If not, write to
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#  http://www.gnu.org/copyleft/gpl.html
#
import os
import sys
import urllib2

import xbmcaddon
import xbmcgui
import xbmcplugin

import buggalo

try:
    import json
except:
    import simplejson as json

BASE_URL = 'http://tv.dmi.dk%s'
JSON_URL = BASE_URL % '/js/photos?raw&'


def showOverview():
    u = urllib2.urlopen(JSON_URL)
    data = u.read()
    u.close()

    clips = json.loads(data)
    for clip in clips['photos']:
        item = xbmcgui.ListItem(clip['content_text'], iconImage=BASE_URL % clip['portrait_download'] + '.jpg')
        item.setProperty('Fanart_Image', FANART_IMAGE)
        item.setInfo(type='video', infoLabels={
            'title': clip['content_text']
        })
        item.setProperty('Fanart_Image', BASE_URL % clip['large_download'])

        url = BASE_URL % clip['video_hd_download']
        xbmcplugin.addDirectoryItem(HANDLE, url, item)

    xbmcplugin.endOfDirectory(HANDLE)


if __name__ == '__main__':
    ADDON = xbmcaddon.Addon()
    PATH = sys.argv[0]
    HANDLE = int(sys.argv[1])
    FANART_IMAGE = os.path.join(ADDON.getAddonInfo('path'), 'fanart.jpg')

    buggalo.SUBMIT_URL = 'http://tommy.winther.nu/exception/submit.php'
    try:
        showOverview()
    except Exception:
        buggalo.onExceptionRaised()
