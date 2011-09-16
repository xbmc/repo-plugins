import xbmc, xbmcgui, xbmcplugin, xbmcaddon
import urllib2
import re
import os
import sys
import cgi as urlparse

BASE_URL = 'http://onside.dk'

class OnsideTV(object):
    def listCategories(self):
        html = self.downloadUrl(BASE_URL + '/onsidetv')
        for m in re.finditer('<a href="/onsidetv/([^/]+)/[^<]+>([^<]+)</a>', html, re.DOTALL):
            slug = m.group(1)
            name = m.group(2)

            item = xbmcgui.ListItem(name[5:], iconImage=ICON)
            item.setProperty('Fanart_Image', FANART)
            xbmcplugin.addDirectoryItem(HANDLE, PATH + '?slug='+ slug + '&page=1', item, True)

        xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_LABEL)
        xbmcplugin.endOfDirectory(HANDLE)

    def listPrograms(self, slug, page):
        print BASE_URL + '/onsidetv/' + slug + '/' + str(page)
        html = self.downloadUrl(BASE_URL + '/onsidetv/' + slug + '/' + str(page))
        for m in re.finditer('<a href="/fodbold-video/([^"]+)".*?<img src="(.*?)".*?class="video-title">(.*?)</div>.*?class="desc">(.*?)</div>.*?class="date">(.*?)</div>', html, re.DOTALL):
            slug = m.group(1)
            image = m.group(2)
            title = m.group(3)
            description = m.group(4)
            dateStr = m.group(5)

            icon = BASE_URL + image
            icon = icon.replace('136x91', 'onsidetv_658x366')
            item = xbmcgui.ListItem(title, iconImage = icon, thumbnailImage = icon)
            item.setProperty('IsPlayable', 'true')
            item.setProperty('Fanart_Image', icon)
            item.setInfo(type = 'video', infoLabels = {
                'title' : title,
                'plot' : description,
                'date' : dateStr[0:10]
            })
            xbmcplugin.addDirectoryItem(HANDLE, PATH + '?play=' + slug, item)

        if ADDON.getSetting('show.load.next.page') == 'true':
            m = re.search('<a href="/onsidetv/([^/]+)/\d+">&gt;&gt;', html)
            if m:
                item = xbmcgui.ListItem(ADDON.getLocalizedString(30000), iconImage=ICON)
                item.setProperty('Fanart_Image', FANART)
                xbmcplugin.addDirectoryItem(HANDLE, PATH + '?slug='+ m.group(1) + '&page=' + str(page + 1), item, True)

        xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_DATE)
        xbmcplugin.endOfDirectory(HANDLE)

    def playProgram(self, slug):
        url = BASE_URL + '/fodbold-video/' + slug
        html = self.downloadUrl(url)
        m = re.search('id="onside_video_player" href="(.*?)"', html)

        item = xbmcgui.ListItem(path = m.group(1))
        xbmcplugin.setResolvedUrl(HANDLE, True, item)

    def downloadUrl(self, url):
        u = urllib2.urlopen(url)
        data = u.read()
        u.close()
        return data

if __name__ == '__main__':
    ADDON = xbmcaddon.Addon(id = 'plugin.video.onside.tv')
    PATH = sys.argv[0]
    HANDLE = int(sys.argv[1])
    PARAMS = urlparse.parse_qs(sys.argv[2][1:])

    FANART = os.path.join(ADDON.getAddonInfo('path'), 'fanart.jpg')
    ICON = os.path.join(ADDON.getAddonInfo('path'), 'icon.png')

    otv = OnsideTV()
    if PARAMS.has_key('slug'):
        otv.listPrograms(PARAMS['slug'][0], int(PARAMS['page'][0]))
    elif PARAMS.has_key('play'):
        otv.playProgram(PARAMS['play'][0])
    else:
        otv.listCategories()
