# coding=utf-8

##################################
# ZattooBox Folder item
# 
# (c) 2014-2020 Pascal Nançoz
##################################

from resources.lib.core.zbdirectoryitem import ZBDirectoryItem
import xbmcgui

class ZBFolderItem(ZBDirectoryItem):

	def __init__(self, host, args, title, image):
		super(ZBFolderItem, self).__init__(host, args, title, image)
		self.IsFolder = True

	def get_listItem(self):
		return xbmcgui.ListItem(self.Title, iconImage=self.Image)