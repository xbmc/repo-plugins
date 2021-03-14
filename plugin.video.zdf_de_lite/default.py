# -*- coding: utf-8 -*-
import libzdf

class zdf(libzdf.libzdf):
	def __init__(self):
		self.apiVersion = 2
		self.baseApi = 'https://api.zdf.de'
		self.userAgent = 'Mozilla/5.0 (X11; Linux x86_64; rv:66.0) Gecko/20100101 Firefox/66.0'
		self.channels =	['ZDF','ZDFinfo','ZDFneo',]
		self.tokenUrl = 'https://zdf-cdn.live.cellular.de/mediathekV2/token'
		self.API_CLIENT_ID = False
		self.API_CLIENT_KEY = False
		libzdf.libzdf.__init__(self)

o = zdf()
o.action()