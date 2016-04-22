import sys
import xbmcplugin
import xbmcgui

addon_handle = int(sys.argv[1])

xbmcplugin.setContent(addon_handle, 'Live TV')

url='rtmp://live.lasiciliaweb.it:1935/tg/as'

li = xbmcgui.ListItem('Live TV', iconImage='icon.pgn')

xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li)

xbmcplugin.endOfDirectory(addon_handle)