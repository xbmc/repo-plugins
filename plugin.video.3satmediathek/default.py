# -*- coding: utf-8 -*-
import libzdf

class tsat(libzdf.libzdf):
	def __init__(self):
		self.baseApi = 'https://api.3sat.de'
		self.userAgent = '3Sat-App/3.53.800'
		self.channels =	['3sat']
		self.tokenUrl = False
		self.API_CLIENT_ID = '8764caa8'
		self.API_CLIENT_KEY = '60a8d9c60feb563dd70001e46e147d1b'
		libzdf.libzdf.__init__(self)
		

	def libZdfListMain(self):
		l = []
		#l.append({'metadata':{'name':self.translation(32031)}, 'params':{'mode':'libZdfListPage', 'url':f'{self.baseApi}/content/documents/meist-gesehen-100.json?profile=default'}, 'type':'dir'})#endpoint out of service atm
		l.append({'metadata':{'name':self.translation(32132)}, 'params':{'mode':'libZdfListShows'}, 'type':'dir'})
		l.append({'metadata':{'name':self.translation(32133)}, 'params':{'mode':'libMediathekListDate','subParams':f'{{"mode":"libZdfListChannelDateVideos","channel":"3sat"}}'}, 'type':'dir'})
		l.append({'metadata':{'name':self.translation(32134)}, 'params':{'mode':'libZdfListPage', 'url':f'{self.baseApi}/search/documents?q=%2A&contentTypes=category'}, 'type':'dir'})
		l.append({'metadata':{'name':self.translation(32139)}, 'params':{'mode':'libMediathekSearch', 'searchMode':'libZdfListSearch'}, 'type':'dir'})
		return {'items':l,'name':'root'}

	def libZdfListChannelDateVideos(self):
		self.params['url'] = f"{self.baseApi}/content/documents/zdf/programm?profile=video-app&maxResults=200&airtimeDate={self.params['yyyymmdd']}T00:00:00.000Z&includeNestedObjects=true"
		return self.libZdfListPage()

o = tsat()
o.action()