# -*- coding: utf-8 -*-
import libard
import resources.lib.jsonparser as jsonparser

class sportschau(libard.libard):
	def __init__(self):
		libard.libard.__init__(self)
		self.defaultMode = 'main'
		self.modes['main'] = self.main
		self.modes['listStreams'] = self.listStreams
		self.modes['listCategory'] = self.listCategory
		self.playbackModes['playStream'] = self.playStream
		
	def main(self):
		d = {'items':[]}
		d['items'].append({'metadata':{'name':self.translation(32143)}, 'params':{'mode':'listStreams', 'url':'https://exporte.wdr.de/SportschauAppServer/streams'}, 'type':'dir'})#Live
		self.params = {'name':'home','client':'sportschau'}
		ardresult = self.libArdListDefaultPage()
		for item in ardresult['items']:
			if not 'Livestream' in item['metadata']['name']:
				d['items'].append(item)
		return d
			
	def listStreams(self):
		return jsonparser.getStreams(self.params['url'])

	def listCategory(self):
		return jsonparser.getCategory(self.params['url'])
		
	def playStream(self):
		return jsonparser.getStream(self.params['url'])

o = sportschau()
o.action()