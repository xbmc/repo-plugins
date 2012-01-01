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
#  along with this Program; see the file LICENSE.txt. If not, write to
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#  http://www.gnu.org/copyleft/gpl.html
#
import re
import os
import sys
import urllib2
import urlparse
import buggalo

import xbmcgui
import xbmcaddon
import xbmcplugin

BASE_URL = 'http://www.gametest.dk/'
FLV_URL = BASE_URL + 'gametesttest/reviews/%s/%s.flv'
REVIEWS_URL = BASE_URL + 'index.php?anmeldelser=alle'
PAGE_URL = BASE_URL + 'index.php?page=%s'

CATEGORIES = [
    {'title' : 30010, 'params' : 'reviews=1'},
    {'title' : 30011, 'params' : 'retro=1'},
    {'title' : 30012, 'params' : 'stunts=1'},
]

class Gametest(object):
    def showOverview(self):
        html = self.downloadUrl(BASE_URL)
        infoLabels = dict()

        # Latest show
        m = re.search('Sendt den ([^<]+)?.*?<ul>(.*?)</ul>', html, re.DOTALL)
        if m:
            date = m.group(1)
            if date:
                date = m.group(1).replace('-', '.')
                infoLabels['title'] = ADDON.getLocalizedString(30000) + ': ' + date
                infoLabels['date'] = date
            else:
                infoLabels['title'] = ADDON.getLocalizedString(30000)
            infoLabels['plot'] = m.group(2).replace('<li>', '').replace('</li>', '\n')
        else:
            infoLabels['title'] = ADDON.getLocalizedString(30000)

        item = xbmcgui.ListItem(infoLabels['title'], iconImage = ICON)
        item.setProperty('Fanart_Image', FANART)
        item.setInfo('video', infoLabels)
        url = FLV_URL % ('file', 'Programmet')
        xbmcplugin.addDirectoryItem(HANDLE, url, item)

        # Categories
        for idx, c in enumerate(CATEGORIES):
            item = xbmcgui.ListItem(ADDON.getLocalizedString(c['title']), iconImage = ICON)
            item.setProperty('Fanart_Image', FANART)
            url = PATH + '?' + c['params']
            xbmcplugin.addDirectoryItem(HANDLE, url, item, True)

        xbmcplugin.setContent(HANDLE, 'episodes')
        xbmcplugin.endOfDirectory(HANDLE)

    def showReviews(self):
        html = self.downloadUrl(REVIEWS_URL)

        for m in re.finditer("index.php\?play=(.*?)&type=anmeldelse'><img src=' (.*?)'.*?anmeldelse'>(.*?)</a>.*?af: (.*?)</a>(.*?)time'>(.*?)</p>", html, re.DOTALL):
            slug = m.group(1)
            icon = m.group(2)
            title = m.group(3)
            author = m.group(4)
            rating = m.group(5).count('good.png')
            date = m.group(6)

            item = xbmcgui.ListItem(title, iconImage = BASE_URL + icon)
            item.setProperty('Fanart_Image', FANART)
            item.setInfo('video', {
                'title' : title,
                'date' : date.replace('-', '.'),
                'year' : int(date[6:]),
                'credits' : author,
                'plot' : title,
                'rating' : rating
            })
            url = FLV_URL % ('file', slug)
            xbmcplugin.addDirectoryItem(HANDLE, url, item)

        xbmcplugin.setContent(HANDLE, 'episodes')
        xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_DATE)
        xbmcplugin.endOfDirectory(HANDLE)

    def showPage(self, page):
        html = self.downloadUrl(PAGE_URL % page)

        for m in re.finditer("index.php\?play=(.*?)&type=.*?src=[ \"](.*?)[ \"](.*?<b>(.*?)</b>.*?af:.*?>(.*?)</a>)?", html, re.DOTALL):
            slug = m.group(1)
            icon = m.group(2)
            title = m.group(4)
            author = m.group(5)

            item = xbmcgui.ListItem(title, iconImage = BASE_URL + icon)
            item.setProperty('Fanart_Image', FANART)
            item.setInfo('video', {
                'title' : title,
                'credits' : author,
                'plot' : title
            })

            url = FLV_URL % ('stunts', slug)
            xbmcplugin.addDirectoryItem(HANDLE, url, item)

        xbmcplugin.setContent(HANDLE, 'episodes')
        xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_LABEL)
        xbmcplugin.endOfDirectory(HANDLE)

    def downloadUrl(self, url):
        u = urllib2.urlopen(url)
        data = u.read()
        u.close()
        return data


if __name__ == '__main__':
    ADDON = xbmcaddon.Addon()
    PATH = sys.argv[0]
    HANDLE = int(sys.argv[1])
    PARAMS = urlparse.parse_qs(sys.argv[2][1:])

    ICON = os.path.join(ADDON.getAddonInfo('path'), 'icon.png')
    FANART = os.path.join(ADDON.getAddonInfo('path'), 'fanart.jpg')

    gt = Gametest()
    try:
        if PARAMS.has_key('reviews'):
            gt.showReviews()
        elif PARAMS.has_key('retro'):
            gt.showPage('retro')
        elif PARAMS.has_key('stunts'):
            gt.showPage('stunts')
        else:
            gt.showOverview()
    except Exception:
        buggalo.onExceptionRaised()

