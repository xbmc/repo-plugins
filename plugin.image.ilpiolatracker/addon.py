import sys
import os
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import urllib2

addon = xbmcaddon.Addon(id='plugin.image.ilpiolatracker')
thisPlugin = int(sys.argv [1])
xbmcplugin.setContent(thisPlugin, 'images')
if (addon.getSetting('readkey')==''):
    dialog = xbmcgui.Dialog()
    dialog.ok(addon.getLocalizedString(id=30000 ), addon.getLocalizedString(id=30005))
else:
    u1='http://m.ilpiola.it/t2/'+addon.getSetting('readkey') + '/g/'
    i=1
    while i <= 20:
        u=u1+str(i)+'.png'
        iconimage=os.path.join(addon.getAddonInfo('path'),"resources","media","zoom"+str(i)+".png")
        liz=xbmcgui.ListItem(unicode('Zoom='+str(i)), iconImage=iconimage,thumbnailImage=iconimage)
        liz.setInfo( type="Image", infoLabels={ "Title": 'Zoom='+str(i) })
        xbmcplugin.addDirectoryItem(handle=thisPlugin,url=u,listitem=liz,isFolder=False)
        i=i+1
    xbmcplugin.endOfDirectory(handle=thisPlugin, succeeded=True, updateListing=False, cacheToDisc=False)

