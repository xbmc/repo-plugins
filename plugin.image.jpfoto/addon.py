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
import urllib2
import urlparse
import re

import buggalo

import xbmcgui
import xbmcaddon
import xbmcplugin

BASE_URL = 'http://foto.jp.dk/'


class JPFotoAddon(object):
    def showCategories(self):
        u = urllib2.urlopen(BASE_URL)
        html = u.read()
        u.close()

        for m in re.finditer('href="/fotosite_sek_frontpage.php\?kategori=([0-9]+)">([^<]+)</a>', html):
            id = m.group(1)
            title = m.group(2).decode('iso-8859-1')

            item = xbmcgui.ListItem(title, iconImage = ICON)
            xbmcplugin.addDirectoryItem(HANDLE, PATH + '?category=' + id, item, True)

        xbmcplugin.endOfDirectory(HANDLE)

    def showCategory(self, category):
        u = urllib2.urlopen(BASE_URL + 'fotosite_sek_frontpage.php?kategori=' + category)
        html = u.read()
        u.close()

        for m in re.finditer('class="(mid|sm)Art">(.*?)/(mid|sm)Art -->', html, re.DOTALL):
            m = re.search('src="(thumbs/[^"]+)".*?href="fotosite_albumview.php\?serie=([0-9]+)">([^<]+)</a>.*?Foto: ([^<]+)<[^>]+>([^<]+)</div>', m.group(2), re.DOTALL)

            image = BASE_URL + m.group(1)
            id = m.group(2)
            title = m.group(3).decode('iso-8859-1')

            item = xbmcgui.ListItem(title, iconImage = image)
            xbmcplugin.addDirectoryItem(HANDLE, PATH + '?serie=' + id, item, True)

        xbmcplugin.endOfDirectory(HANDLE)

    def showSerie(self, serie):
        u = urllib2.urlopen(BASE_URL + 'fotosite_albumview.php?serie=' + serie)
        html = u.read()
        u.close()

        for m in re.finditer('class="ico"><a href="(thumbsnc/[^"]+)".*?title="(.*?)::(.*?)::', html, re.DOTALL):
            path = BASE_URL + m.group(1)
            album = m.group(2).decode('iso-8859-1')
            title = m.group(3).decode('iso-8859-1')

            if title.strip() == '':
                title = album
            item = xbmcgui.ListItem(title, path = path)
            item.setInfo('pictures', {
                'title' : title
            })
            xbmcplugin.addDirectoryItem(HANDLE, path, item)

        xbmcplugin.endOfDirectory(HANDLE)

if __name__ == '__main__':
    ADDON = xbmcaddon.Addon()
    PATH = sys.argv[0]
    HANDLE = int(sys.argv[1])
    PARAMS = urlparse.parse_qs(sys.argv[2][1:])

    ICON = os.path.join(ADDON.getAddonInfo('path'), 'icon.png')

    buggalo.SUBMIT_URL = 'http://tommy.winther.nu/exception/submit.php'
    try:
        jpfoto = JPFotoAddon()
        if PARAMS.has_key('category'):
            jpfoto.showCategory(PARAMS['category'][0])
        elif PARAMS.has_key('serie'):
            jpfoto.showSerie(PARAMS['serie'][0])
        else:
            jpfoto.showCategories()
    except Exception:
        buggalo.onExceptionRaised()
