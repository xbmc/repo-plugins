import os
import re
import sys
import urllib2

import xbmcgui
import xbmcplugin
import xbmcaddon

VIDEO_PODCAST_URL = 'http://www.dr.dk/podcast/api/GetByFirst?type=tv&take=1000'

class DrDkPodcast(object):
    def showOverview(self):
        u = urllib2.urlopen(VIDEO_PODCAST_URL)
        html = u.read()
        u.close()

        fanart = os.path.join(ADDON.getAddonInfo('path'), 'fanart.jpg')
        for m in re.finditer(b"{\"Title\":\"(.*?)\",\"Type\":\"(.*?)\",\"Channel\":\"(.*?)\",\"ChannelGroup\":\"(.*?)\",\"ImageLinkScaled\":\"(.*?)\",\"XmlLink\":\"(.*?)\"", html, re.DOTALL):
            title = m.group(1)
            description = ''
            url = m.group(6)

            item = xbmcgui.ListItem(title, iconImage = m.group(5))
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
