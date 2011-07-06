import sys
import simplejson
import urllib2

import xbmcgui
import xbmcplugin

CHANNELS_URL = 'http://www.dr.dk/LiveNetRadio/datafeed/channels.js.drxml'

def showChannels():
    u = urllib2.urlopen(CHANNELS_URL)
    data = u.read()
    u.close()

    channels = simplejson.loads(data[39:-3])

    for channel in channels:
        item = xbmcgui.ListItem(channel['title'], iconImage = channel['logo'])
        item.setProperty('IsPlayable', 'true')
        item.setProperty("IsLive", "true")
        item.setInfo(type = 'audio', infoLabels = {
                'title' : channel['title']
        })

        if type(channel['mediaFile']) is list:
            xbmcplugin.addDirectoryItem(HANDLE, channel['mediaFile'][0], item)
        else:
            xbmcplugin.addDirectoryItem(HANDLE, channel['mediaFile'], item)

    xbmcplugin.endOfDirectory(HANDLE)

if __name__ == '__main__':
    HANDLE = int(sys.argv[1])
    showChannels()

