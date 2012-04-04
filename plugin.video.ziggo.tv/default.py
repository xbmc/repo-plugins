import sys, os, xbmc, xbmcgui, xbmcaddon, xbmcplugin, urllib2

addon      = xbmcaddon.Addon(id='plugin.video.ziggo.tv')
pluginpath = addon.getAddonInfo('path')
imagepath  = os.path.join(xbmc.translatePath(pluginpath),'resources','images')

def additem(channel_id, title):
    resp = urllib2.urlopen('http://tv.wezelkrozum.nl/redirectToStream.php?provider=0&quality=4&id=' + str(channel_id))
    streamurl = resp.geturl()
    listitem = xbmcgui.ListItem(title, thumbnailImage = os.path.join(imagepath,title + '.gif'))
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), streamurl, listitem, totalItems=0)

try:
    resp = urllib2.urlopen('http://tv.wezelkrozum.nl/redirectToStream.php?provider=0&quality=4&id=106')
    streamurl = resp.geturl()
except:
    dialog = xbmcgui.Dialog()
    ok = dialog.ok('Ziggo TV streams', 'There was an error connecting to\n http://tv.wezelkrozum.nl/redirectToStream.php?provider=0&quality=4&id=106')
else:
    additem(106, 'Nederland 1')
    additem(107, 'Nederland 2')
    additem(108, 'Nederland 3')
    additem(109, 'RTL 4')
    additem(121, 'RTL 5')
    additem(120, 'SBS 6')
    additem(122, 'RTL 7')
    additem(7,   'Net 5')
    additem(119, 'Veronica & Disney XD')
    additem(157, 'RTL 8')    
    additem(31,  'National Geographic')
    additem(42,  'Eurosport')
finally:
    xbmcplugin.endOfDirectory(int(sys.argv[1]))