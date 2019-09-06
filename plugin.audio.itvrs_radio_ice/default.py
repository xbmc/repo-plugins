#!/usr/bin/python

import sys
import xbmcgui
import xbmcplugin

addon_handle = int(sys.argv[1])

xbmcplugin.setContent(addon_handle, 'audio')

url = 'http://stream.zeno.fm/3611cwn8mbruv'
li = xbmcgui.ListItem(label='ITVRS - Radio Ice', iconImage='DefaultAudio.png')
li.setInfo('music', {'Title': 'ITVRS - Radio Ice', 'Album': 'ITVRS - Radio Ice'})
xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li)

xbmcplugin.endOfDirectory(addon_handle)
