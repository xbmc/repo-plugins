# coding=utf-8

##################################
# ZattooBox extensions
# Base Class
# (c) 2014-2020 Pascal Nançoz
##################################

import os

class ZBExtension(object):
	ZapiSession = None
	ZBProxy = None
	ExtensionsPath = None

	def __init__(self, zapiSession, zbProxy):
		self.ZapiSession = zapiSession
		self.ZBProxy = zbProxy
		self.ExtensionsPath = os.path.join(zbProxy.SourcePath, 'resources/data/extensions/')
		self.init()

	def init(self):
		raise NotImplementedError('Not implemented')

	def get_items(self):
		raise NotImplementedError('Not implemented')

	def activate_item(self, title, args):
		raise NotImplementedError('Not implemented')



