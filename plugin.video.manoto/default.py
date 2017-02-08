import xbmc, xbmcgui, os, xbmcaddon

__settings__ = xbmcaddon.Addon()
home = __settings__.getAddonInfo('path')
icon = xbmc.translatePath(os.path.join(home, 'icon.png'))
li = xbmcgui.ListItem ('manoto')
li.setArt({ 'thumb': icon })
li.setInfo('video', {'plot': 'Live Stream'})

url = 'http://manotolive-i.akamaihd.net/hls/live/251779/livexhq/master_Layer1.m3u8'
xbmc.Player().play(url, li, False)
