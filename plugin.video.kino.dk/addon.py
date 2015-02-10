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
import re
import xml.etree.ElementTree
import datetime
import time

import buggalo

import xbmcgui
import xbmcaddon
import xbmcplugin

DATA_URL = 'http://www.kino.dk/kinotv.rss'


class KinoTVAddon(object):
    def showClips(self):
        u = urllib2.urlopen(DATA_URL)
        response = u.read()
        u.close()
        doc = xml.etree.ElementTree.fromstring(response)

        for clip in doc.findall('channel/item'):
            title = clip.findtext('title')
            image = clip.find('image').attrib.get('url')
            date = self.parseDate(clip.findtext('pubDate'))

            infoLabels = dict()
            infoLabels['studio'] = ADDON.getAddonInfo('name')
            infoLabels['title'] = title
            infoLabels['plot'] = clip.findtext('body')
            infoLabels['plotoutline'] = re.sub('<[^>]+>', '', clip.findtext('description'))
            infoLabels['date'] = date.strftime('%d.%m.%Y')
            infoLabels['year'] = int(date.strftime('%Y'))

            item = xbmcgui.ListItem(title, iconImage=image, thumbnailImage=image)
            item.setInfo('video', infoLabels)
            item.setProperty('Fanart_Image', image)
            url = clip.findtext('flv')
            if not url:
                url = clip.findtext('mp4')
            xbmcplugin.addDirectoryItem(HANDLE, url, item)

        xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_DATE)
        xbmcplugin.endOfDirectory(HANDLE)

    @staticmethod
    def parseDate(dateStr):
        try:
            return datetime.datetime.strptime(dateStr[0:-6], '%a, %d %b %Y %H:%M:%S')
        except TypeError:
            return datetime.datetime.fromtimestamp(time.mktime(time.strptime(dateStr[0:-6], '%a, %d %b %Y %H:%M:%S')))

if __name__ == '__main__':
    ADDON = xbmcaddon.Addon()
    HANDLE = int(sys.argv[1])
    ICON = os.path.join(ADDON.getAddonInfo('path'), 'icon.png')

    buggalo.SUBMIT_URL = 'http://tommy.winther.nu/exception/submit.php'
    try:
        kinotv = KinoTVAddon()
        kinotv.showClips()
    except Exception:
        buggalo.onExceptionRaised()
