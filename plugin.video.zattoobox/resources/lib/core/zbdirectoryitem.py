# coding=utf-8

##################################
# ZattooBox Directory item
# Base class
# (c) 2014-2020 Pascal Nançoz
##################################

import xbmcgui, urllib

class ZBDirectoryItem(object):
	Host = None
	Args = None	
	Title = None
	Image = None
	IsFolder = False

	def __init__(self, host, args, title, image):
		self.Host = host
		self.Args = args
		self.Title = title
		self.Image = image

	def get_listItem(self):
		raise NotImplementedError('Not implemented')

	def get_url(self):
		return 'ext=%s&%s' % (type(self.Host).__name__, urllib.urlencode(self.Args))

