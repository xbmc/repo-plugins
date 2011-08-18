import os
import sys
import simplejson
import urllib2

import xbmcaddon
import xbmcgui
import xbmcplugin


BASE_URL = 'http://tv.dmi.dk%s'
JSON_URL = BASE_URL % '/js/photos?raw&'

def showOverview():
    u = urllib2.urlopen(JSON_URL)
    json = u.read()
    u.close()

    clips = simplejson.loads(json)
    for clip in clips['photos']:
        print os.path.join(ADDON.getAddonInfo('path'), 'fanart.jpg')

        item = xbmcgui.ListItem(clip['content_text'], iconImage = BASE_URL % clip['portrait_download'] + '.jpg')
        item.setProperty('Fanart_Image', os.path.join(ADDON.getAddonInfo('path'), 'fanart.jpg'))
        item.setInfo(type = 'video', infoLabels = {
            'title' : clip['content_text']
        })
        item.setProperty('Fanart_Image', BASE_URL % clip['large_download'])

        url = BASE_URL % clip['video_hd_download']
        xbmcplugin.addDirectoryItem(HANDLE, url, item)

    xbmcplugin.endOfDirectory(HANDLE)



if __name__ == '__main__':
    ADDON = xbmcaddon.Addon(id = 'plugin.video.dmi.dk')
    PATH = sys.argv[0]
    HANDLE = int(sys.argv[1])

    showOverview()
