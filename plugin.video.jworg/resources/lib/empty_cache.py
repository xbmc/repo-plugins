"""
Clear cache, so next html or json load will be reloaded
"""
import xbmcgui
import xbmcaddon

try:
	import StorageServer
except:
 	import storageserverdummy as StorageServer

cache = StorageServer.StorageServer("plugin://plugin.video.jworg/", 24) 
cache.delete("%")
cache_month = StorageServer.StorageServer("plugin://plugin.video.jworg/" + "month", 24 * 7) 
cache_month.delete("%")

dialog = xbmcgui.Dialog()

plugin = xbmcaddon.Addon("plugin.video.jworg")
confirm_title = plugin.getLocalizedString( 30023 )
confirm_text = plugin.getLocalizedString( 30024 )

dialog.ok( confirm_title, confirm_text )