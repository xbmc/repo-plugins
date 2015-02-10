import os
import sys
import urlparse
import re
import urllib2
import xbmcgui
import xbmcplugin
import xbmcaddon

BASE_URL = 'http://gaffa.dk/tv/archive/'
VIDEO_URL = 'http://videobackup.gaffa.dk/videos/%s.mov'

class GaffaTVAddon(object):
    def showOverview(self):
        u = urllib2.urlopen(BASE_URL)
        html = u.read()
        u.close()

        for m in re.finditer("<option[ ]+value='([0-9]+)'>([^<]+)</option>", html):
            category_id = m.group(1)
            title = m.group(2)

            item = xbmcgui.ListItem(title, iconImage = ICON)
            item.setProperty('Fanart_Image', FANART)
            item.setInfo(type='video', infoLabels={
                'title': title
                })

            url = PATH + '?id=' + category_id + '&page=1'
            xbmcplugin.addDirectoryItem(HANDLE, url, item, isFolder = True)

        xbmcplugin.endOfDirectory(HANDLE)

    def showCategory(self, category_id, page = 1):
        url = BASE_URL + str(category_id)
        if page > 1:
            url += '/page:%s' % page
        print url

        u = urllib2.urlopen(url)
        html = u.read()
        u.close()

        for m in re.finditer('<a href="/tv/clip/([0-9]+)" title="(.*?)"><img src=\'([^\']+)\'.*?<p>(.*?)</p>', html, re.DOTALL):
            title = m.group(2)[9:]
            icon = m.group(3).replace('_193.jpg', '_640.jpg')
            description = m.group(4)

            m = re.search('splash/(.*?)_193', m.group(3))
            if m:
                url = VIDEO_URL % m.group(1)

            item = xbmcgui.ListItem(title, iconImage = icon, thumbnailImage = icon)
            item.setProperty('Fanart_Image', icon)
            item.setInfo(type='video', infoLabels={
                'title': title,
                'plot' : description,
                'studio' : ADDON.getAddonInfo('name')
            })

            xbmcplugin.addDirectoryItem(HANDLE, url, item)

        if re.search('class="next"', html) is not None:
            item = xbmcgui.ListItem(ADDON.getLocalizedString(30000), iconImage = ICON)
            item.setProperty('Fanart_Image', FANART)
            url = PATH + '?id=' + category_id + '&page=' + str(page + 1)
            xbmcplugin.addDirectoryItem(HANDLE, url, item, True)

        xbmcplugin.endOfDirectory(HANDLE)

if __name__ == '__main__':
    ADDON = xbmcaddon.Addon(id = 'plugin.video.gaffa.tv')
    PATH = sys.argv[0]
    HANDLE = int(sys.argv[1])
    PARAMS = urlparse.parse_qs(sys.argv[2][1:])

    ICON = os.path.join(ADDON.getAddonInfo('path'), 'icon.png')
    FANART = os.path.join(ADDON.getAddonInfo('path'), 'fanart.jpg')

    gtv = GaffaTVAddon()
    if PARAMS.has_key('id') and PARAMS.has_key('page'):
        gtv.showCategory(PARAMS['id'][0], int(PARAMS['page'][0]))
    elif PARAMS.has_key('id'):
        gtv.showCategory(PARAMS['id'])
    else:
        gtv.showOverview()
