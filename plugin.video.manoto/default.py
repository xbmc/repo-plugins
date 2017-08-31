import xbmc, xbmcgui, os, xbmcaddon

__settings__ = xbmcaddon.Addon()
home = __settings__.getAddonInfo('path')
icon = xbmc.translatePath(os.path.join(home, 'icon.png'))
li = xbmcgui.ListItem ('manoto')
li.setArt({ 'thumb': icon })
li.setInfo('video', {'plot': 'Live Stream'})

url = 'https://d1v7e0o3q8z5j0.cloudfront.net/Live.m3u8'
xbmc.Player().play(url, li, False)
