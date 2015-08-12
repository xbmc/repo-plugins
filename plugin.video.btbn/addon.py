import sys
import xbmcgui
import xbmcplugin

addon_handle = int(sys.argv[1])

xbmcplugin.setContent(addon_handle, 'movies')

url = 'http://media.btbn.tv/btbn/mp4:halfwaytree/playlist.m3u8'
li = xbmcgui.ListItem('Watch BTBN Live!', iconImage='icon.png')
xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li)

xbmcplugin.endOfDirectory(addon_handle)