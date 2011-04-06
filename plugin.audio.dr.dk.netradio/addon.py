import os
import re
import sys

import xbmcgui
import xbmcplugin

import danishaddons
import danishaddons.web

BASE_URL = 'http://www.dr.dk/netradio/wmp.asp'

def showChannels():
    icon = os.path.join(danishaddons.ADDON_PATH, 'icon.png')

    format = danishaddons.ADDON.getSetting('format')
    if format == 'WMA':
        html = danishaddons.web.downloadAndCacheUrl(BASE_URL, os.path.join(danishaddons.ADDON_DATA_PATH, 'channels.html'), 24 * 60)

        for m in re.finditer('<td nowrap="nowrap">(.*?)</td>.*?\n.*?<a href="([^"]+)">%s</a>' % getQuality(), html):
            name = danishaddons.web.decodeHtmlEntities(m.group(1))
            asxUrl = m.group(2)

            item = xbmcgui.ListItem(name, iconImage = icon)
            item.setProperty('IsPlayable', 'true')
            item.setInfo(type = 'audio', infoLabels = {
                    'title' : name
            })
            url = danishaddons.ADDON_PATH + '?url=' + asxUrl
            xbmcplugin.addDirectoryItem(danishaddons.ADDON_HANDLE, url, item)
    else: # format == 'AAC'
        for idx in range(1, 31):
            name = danishaddons.msg(30100 + idx)
            url = danishaddons.msg(30200 + idx)
            item = xbmcgui.ListItem(name, iconImage = icon)
            item.setProperty('IsPlayable', 'true')
            item.setProperty("IsLive", "true")
            item.setInfo(type = 'audio', infoLabels = {
                    'title' : name
            })
            xbmcplugin.addDirectoryItem(danishaddons.ADDON_HANDLE, url, item)

    xbmcplugin.endOfDirectory(danishaddons.ADDON_HANDLE)

def playStream(url):
    playlist = danishaddons.web.downloadUrl(url)
    m = re.search('<TITLE>(.*?)</TITLE>.*?<Ref href="(.*?)"/>', playlist, re.DOTALL)
    
    title = m.group(1)
    streamUrl = m.group(2)

    item = xbmcgui.ListItem(title = title, path = streamUrl)
    item.setInfo('music', {
        'artist' : 'DR',
        'title' : title
    })
    xbmcplugin.setResolvedUrl(danishaddons.ADDON_HANDLE, True, item)


def getQuality():
    quality = danishaddons.ADDON.getSetting('quality')
    if quality == 'High':
        return 'H\&oslash;j'
    elif quality == 'Medium':
        return 'Mellem'
    else:
        return 'Lav'

if __name__ == '__main__':
    danishaddons.init(sys.argv)

    if danishaddons.ADDON_PARAMS.has_key('url'):
        playStream(danishaddons.ADDON_PARAMS['url'])
    else:
        showChannels()

