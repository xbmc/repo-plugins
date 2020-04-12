# coding=utf-8

##################################
# ZattooBox Addon proxy
#
# (c) 2014-2020 Pascal Nançoz
##################################

import xbmc, xbmcplugin, xbmcgui

class ZBAddonProxy(object):
	Addon = None
	Handle = None
	URLBase = None
	SourcePath = None
	StoragePath = None

	def __init__(self, addon, urlBase, handle):
		self.Addon = addon
		self.URLBase = urlBase
		self.Handle = handle
		self.SourcePath = xbmc.translatePath(addon.getAddonInfo('path')).decode('utf-8')		
		self.StoragePath = xbmc.translatePath(addon.getAddonInfo('profile')).decode('utf-8')

	def get_string(self, code):
		return self.Addon.getLocalizedString(code)

	#Add a collection of ZBDirectoryItem
	def add_directoryItems(self, items):
		xbmcplugin.setContent(self.Handle, 'movies')
		for item in items:
			li = item.get_listItem()
			xbmcplugin.addDirectoryItem(
				handle=self.Handle,
				url='%s?%s' % (self.URLBase, item.get_url()),
				listitem=li,
				isFolder=item.IsFolder
			)
		xbmcplugin.endOfDirectory(self.Handle)

	def play_stream(self, url):
		li = xbmcgui.ListItem()
		li.setInfo(type="Video", infoLabels={})
		li.setPath(url)
		xbmcplugin.setResolvedUrl(self.Handle, True, li)		




