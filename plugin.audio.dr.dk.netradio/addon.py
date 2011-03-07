import os
import re
import sys

import xbmcgui
import xbmcplugin

import danishaddons
import danishaddons.web

BASE_URL = 'http://www.dr.dk/netradio/wmp.asp'

RTMP_URL = 'rtmp://live.gss.dr.dk/live/'
CHANNELS = \
    ('DR P1', 'Channel3_HQ'),\
    ('DR P2', 'Channel4_HQ'),\
    ('DR P3', 'Channel5_HQ'),\
    ('DR P4 København', 'Channel8_HQ'),\
    ('DR P4 Sjælland', 'Channel11_HQ'),\
    ('DR P4 Østjylland', 'Channel14_HQ'),\
    ('DR P4 Syd', 'Channel12_HQ'),\
    ('DR P4 Fyn', 'Channel7_HQ'),\
    ('DR P4 Nordjylland', 'Channel10_HQ'),\
    ('DR P4 Midt & Vest', 'Channel9_HQ'),\
    ('DR P4 Trekanten', 'Channel13_HQ'),\
    ('DR P4 Bornholm', 'Channel6_HQ'),\
    ('DR P4 Esbjerg', 'Channel15_HQ'),\
    ('DR P4 NordvestSjælland', 'Channel16_HQ'),\
    ('DR P5', 'Channel16_HQ'),\
    ('DR Barometer', 'Channel17_HQ'),\
    ('DR Hit', 'Channel21_HQ'),\
    ('DR Soft', 'Channel28_HQ'),\
    ('DR Boogieradio', 'Channel18_HQ'),\
    ('DR Jazz', 'Channel22_HQ'),\
    ('DR Oline', 'Channel24_HQ'),\
    ('DR Dansktop', 'Channel19_HQ'),\
    ('DR Rock', 'Channel27_HQ'),\
    ('DR Unga Bunga', 'Channel29_HQ'),\
    ('DR Evergreen', 'Channel20_HQ'),\
    ('DR P5000', 'Channel2_HQ'),\
    ('DR Klassisk', 'Channel23_HQ'),\
    ('DR R&B', 'Channel26_HQ'),\
    ('DR World', 'Channel30_HQ'),\
    ('DR Nyheder', 'Channel1_HQ')

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
        for c in CHANNELS:
            name = c[0]
            url = RTMP_URL + c[1]
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

