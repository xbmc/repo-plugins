import re
import os
import sys
import urllib2
import cgi as urlparse

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

        # Latest show
        m = re.search('Sendt den ([^<]+).*?<ul>(.*?)</ul>', html, re.DOTALL)
        date = m.group(1)
        title = ADDON.getLocalizedString(30000) % date
        games = m.group(2).replace('<li>', '').replace('</li>', '\n')

        path = ADDON.getAddonInfo('path')
        icon = os.path.join(path, 'icon.png')
        item = xbmcgui.ListItem(title, iconImage = icon)
        item.setProperty('Fanart_Image', FANART)
        item.setInfo('video', {
            'title' : title,
            'plot' : str(ADDON.getLocalizedString(30001)) + games,
            'date' : date.replace('-', '.')
        })
        url = FLV_URL % ('file', 'Programmet')
        xbmcplugin.addDirectoryItem(HANDLE, url, item)

        # Categories
        for idx, c in enumerate(CATEGORIES):
            item = xbmcgui.ListItem(ADDON.getLocalizedString(c['title']), iconImage = icon)
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
    ADDON = xbmcaddon.Addon(id = 'plugin.video.gametest.dk')
    PATH = sys.argv[0]
    HANDLE = int(sys.argv[1])
    PARAMS = urlparse.parse_qs(sys.argv[2][1:])

    FANART = os.path.join(ADDON.getAddonInfo('path'), 'fanart.jpg')

    gt = Gametest()
    if PARAMS.has_key('reviews'):
        gt.showReviews()
    elif PARAMS.has_key('retro'):
        gt.showPage('retro')
    elif PARAMS.has_key('stunts'):
        gt.showPage('stunts')
    else:
        gt.showOverview()

