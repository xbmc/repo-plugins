########################################

import os, sys, xbmc, xbmcgui, xbmcplugin, xbmcaddon
	
#SG!Radio by Sean, GadgetReactor

# Various constants used throughout the script
HANDLE = int(sys.argv[1])
ADDON = xbmcaddon.Addon(id='plugin.audio.sgradio')
LANGUAGE  = ADDON.getLocalizedString
THUMBNAIL_PATH = os.path.join( ADDON.getAddonInfo( 'path' ), 'resources', 'media')

def start() :

	li = xbmcgui.ListItem(label=LANGUAGE(30000), thumbnailImage=os.path.join(THUMBNAIL_PATH, 'ria897.jpg'))
	xbmcplugin.addDirectoryItem(handle=HANDLE, url="http://mediacorp.rastream.com/897fm?type=.mp3", listitem=li, isFolder=False)
	li = xbmcgui.ListItem(label=LANGUAGE(30001), thumbnailImage=os.path.join(THUMBNAIL_PATH, 'gold905.jpg'))		
	xbmcplugin.addDirectoryItem(handle=HANDLE, url="http://mediacorp.rastream.com/905fm?type=.mp3", listitem=li, isFolder=False)
	li = xbmcgui.ListItem(label=LANGUAGE(30002), thumbnailImage=os.path.join(THUMBNAIL_PATH, 'hot913.jpg'))
	xbmcplugin.addDirectoryItem(handle=HANDLE, url="http://sph.rastream.com/913fm?type=.mp3", listitem=li, isFolder=False)
	li = xbmcgui.ListItem(label=LANGUAGE(30003), thumbnailImage=os.path.join(THUMBNAIL_PATH, 'kiss92.jpg'))
	xbmcplugin.addDirectoryItem(handle=HANDLE, url="http://sph.rastream.com/sph-kiss92?type=.mp3", listitem=li, isFolder=False)
	li = xbmcgui.ListItem(label=LANGUAGE(30004), thumbnailImage=os.path.join(THUMBNAIL_PATH, 'YES933.jpg'))
	xbmcplugin.addDirectoryItem(handle=HANDLE, url="http://mediacorp.rastream.com/933fm?type=.mp3", listitem=li, isFolder=False)
	li = xbmcgui.ListItem(label=LANGUAGE(30005), thumbnailImage=os.path.join(THUMBNAIL_PATH, 'warna.jpg'))
	xbmcplugin.addDirectoryItem(handle=HANDLE, url="http://mediacorp.rastream.com/942fm?type=.mp3", listitem=li, isFolder=False)
	li = xbmcgui.ListItem(label=LANGUAGE(30006), thumbnailImage=os.path.join(THUMBNAIL_PATH, 'class95.jpg'))
	xbmcplugin.addDirectoryItem(handle=HANDLE, url="http://mediacorp.rastream.com/950fm?type=.mp3", listitem=li, isFolder=False)
	li = xbmcgui.ListItem(label=LANGUAGE(30007), thumbnailImage=os.path.join(THUMBNAIL_PATH, 'capital958.jpg'))
	xbmcplugin.addDirectoryItem(handle=HANDLE, url="http://mediacorp.rastream.com/958fm?type=.mp3", listitem=li, isFolder=False)
	li = xbmcgui.ListItem(label=LANGUAGE(30008), thumbnailImage=os.path.join(THUMBNAIL_PATH, 'love972.jpg'))
	xbmcplugin.addDirectoryItem(handle=HANDLE, url="http://mediacorp.rastream.com/972fm?type=.mp3", listitem=li, isFolder=False)
	li = xbmcgui.ListItem(label=LANGUAGE(30009), thumbnailImage=os.path.join(THUMBNAIL_PATH, '987FM.jpg'))
	xbmcplugin.addDirectoryItem(handle=HANDLE, url="http://mediacorp.rastream.com/987fm?type=.mp3", listitem=li, isFolder=False)
	li = xbmcgui.ListItem(label=LANGUAGE(30010), thumbnailImage=os.path.join(THUMBNAIL_PATH, 'lush995.jpg'))
	xbmcplugin.addDirectoryItem(handle=HANDLE, url="http://mediacorp.rastream.com/995fm?type=.mp3", listitem=li, isFolder=False)
	li = xbmcgui.ListItem(label=LANGUAGE(30011), thumbnailImage=os.path.join(THUMBNAIL_PATH, 'ufm.png'))
	xbmcplugin.addDirectoryItem(handle=HANDLE, url="http://sph.rastream.com/1003fm?type=.mp3", listitem=li, isFolder=False)	
	setViewMode("500")		
	xbmcplugin.endOfDirectory( HANDLE )		
	
def setViewMode(id):
	if xbmc.getSkinDir() == "skin.confluence":
		xbmc.executebuiltin("Container.SetViewMode(" + id + ")")
			
start()