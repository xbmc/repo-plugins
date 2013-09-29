import sys
import os
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import urllib2

addon = xbmcaddon.Addon(id='plugin.image.ilpiolatracker')
thisPlugin = int(sys.argv [1])
if (addon.getSetting('readkey')==''):
    dialog = xbmcgui.Dialog()
    dialog.ok(addon.getLocalizedString(id=30000 ), addon.getLocalizedString(id=30005))
else:
    u1='http://m.ilpiola.it/t/q.php?f=g&k='+addon.getSetting('readkey')
    i=1
    while i <= 20:
        u=u1+'&z='+str(i)
        iconimage=os.path.join(addon.getAddonInfo('path'),"resources","media","zoom"+str(i)+".png")
        liz=xbmcgui.ListItem(unicode('Zoom='+str(i)), iconImage=iconimage,thumbnailImage=iconimage)
        liz.setInfo( type="Image", infoLabels={ "Title": 'Zoom='+str(i) })
        xbmcplugin.addDirectoryItem(handle=thisPlugin,url=u,listitem=liz,isFolder=False)
        i=i+1
    xbmcplugin.endOfDirectory(handle=thisPlugin, succeeded=True, updateListing=False, cacheToDisc=True)
