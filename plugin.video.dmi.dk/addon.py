import sys

import xbmcgui
import xbmcplugin

import simplejson
import danishaddons
import danishaddons.web

BASE_URL = 'http://tv.dmi.dk%s'
JSON_URL = BASE_URL % '/js/photos?raw&'

def showOverview():
    json = danishaddons.web.downloadUrl(JSON_URL)
    clips = simplejson.loads(json)

    for clip in clips['photos']:
        print BASE_URL % clip['portrait_download']
        item = xbmcgui.ListItem(clip['content_text'], iconImage = BASE_URL % clip['portrait_download'])
        item.setInfo(type = 'video', infoLabels = {
            'title' : clip['content_text']
        })
        item.setProperty('Fanart_Image', BASE_URL % clip['large_download'])

        url = BASE_URL % clip['video_hd_download']
        xbmcplugin.addDirectoryItem(danishaddons.ADDON_HANDLE, url, item)

    xbmcplugin.endOfDirectory(danishaddons.ADDON_HANDLE)

if __name__ == '__main__':
    danishaddons.init(sys.argv)

    showOverview()
