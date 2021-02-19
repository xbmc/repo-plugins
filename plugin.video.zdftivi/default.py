# -*- coding: utf-8 -*-
import libzdf

class tivi(libzdf.libzdf):
	def __init__(self):
		self.apiVersion = 2
		self.baseApi = 'https://api.zdf.de'
		self.userAgent = 'Mozilla/5.0 (X11; Linux x86_64; rv:66.0) Gecko/20100101 Firefox/66.0'
		self.channels =	['ZDF','ZDFinfo','ZDFneo',]
		self.tokenUrl = 'https://zdf-cdn.live.cellular.de/mediathekV2/token'
		self.API_CLIENT_ID = False
		self.API_CLIENT_KEY = False
		libzdf.libzdf.__init__(self)


	def libZdfListMain(self):
		l = []#https://api.zdf.de/content/documents/zdf/kinder/sendungen-a-z

		l.append({'metadata':{'name':self.translation(32132)}, 'params':{'mode':'libZdfListShows', 'uri':'/content/documents/kindersendungen-a-z-100.json?profile=default'}, 'type':'dir'})
		l.append({'metadata':{'name':self.translation(32133)}, 'params':{'mode':'libMediathekListDate','subParams':f'{{"mode":"libZdfListChannelDateVideos","channel":"KI.KA"}}'}, 'type':'dir'})
		return {'items':l,'name':'root'}
		
		#TODO:
		#l.append({'metadata':{'name':self.translation(32134)}, 'params':{'mode':'libZdfListPage', 'url':f'{self.baseApi}/content/documents/zdftivi-fuer-kinder-100.json?profile=default'}, 'type':'dir'})#weird response layout
		#alternative pages:
		#https://api.zdf.de/content/documents/zdftivi-fuer-kinder-100.json?profile=default
		#https://api.zdf.de/content/documents/zdftivi-sendung-verpasst-100.json?profile=default&airtimeBegin=2018-02-20T05%3A30%3A00%2B02%3A00&airtimeEnd=2018-02-24T05%3A29%3A00%2B02%3A00


o = tivi()
o.action()