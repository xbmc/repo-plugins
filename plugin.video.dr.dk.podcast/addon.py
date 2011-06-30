import os
import re
import sys
import urllib2

import xbmcgui
import xbmcplugin
import xbmcaddon

VIDEO_PODCAST_URL = 'http://www.dr.dk/podcast/Video'

class DrDkPodcast(object):
    def showOverview(self):
        u = urllib2.urlopen(VIDEO_PODCAST_URL)
        html = u.read()
        u.close()

        icon = os.path.join(ADDON.getAddonInfo('path'), 'icon.png')
        fanart = os.path.join(ADDON.getAddonInfo('path'), 'fanart.jpg')

        for m in re.finditer('<h2>.*?<a href="[^"]+">([^<]+)</a>\s+</h2>\s+<p>([^<]*)</p>.*?(http://vpodcast.dr.dk/feeds/.*?\\.xml)', html, re.DOTALL):
            title = m.group(1)
            description = m.group(2)
            url = m.group(3)

            item = xbmcgui.ListItem(title, iconImage = icon)
            item.setProperty('Fanart_Image', fanart)
            item.setInfo(type = 'video', infoLabels = {
                'title' : title,
                'plot' : description
            })
            url = url.replace('http://', 'rss://')
            xbmcplugin.addDirectoryItem(HANDLE, url, item, True)

        xbmcplugin.endOfDirectory(HANDLE)


if __name__ == '__main__':
    ADDON = xbmcaddon.Addon(id = 'plugin.video.dr.dk.podcast')
    HANDLE = int(sys.argv[1])

    addon = DrDkPodcast()
    addon.showOverview()
