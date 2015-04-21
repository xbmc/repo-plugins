# coding=utf-8

##################################
# ZattooBox Playable item
# 
# (c) 2014-2015 Pascal Nançoz
##################################

from resources.lib.core.zbdirectoryitem import ZBDirectoryItem
import xbmcgui

class ZBPlayableItem(ZBDirectoryItem):
	Title2 = None

	def __init__(self, host, args, title, image, title2):
		super(ZBPlayableItem, self).__init__(host, args, title, image)
		self.Title2 = title2

	def get_listItem(self):
		li = xbmcgui.ListItem(label=self.Title, label2=self.Title2, iconImage=self.Image)
		li.setProperty('IsPlayable', 'true')
		return li