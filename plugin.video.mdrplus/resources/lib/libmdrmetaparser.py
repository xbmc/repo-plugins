# -*- coding: utf-8 -*-
import json
import re
import xml.etree.ElementTree as ET
import requests

class parser:
	def __init__(self):
		self.result = {'items':[],'pagination':{'currentPage':0}}

	def parseVideos(self,url='http://www.mdr.de/tv/programm/mordenimnorden100-meta.xml'):
		response = requests.get(url).text
		root = ET.fromstring(response)
		
		l = []
		#document,broadcasts,broadcast,
		for broadcast in root[0]:
			d = {'type':'video', 'params':{'mode':'libMdrPlay'}, 'metadata':{'art':{}}}
			for node in broadcast[0]:
				if node.tag == 'videos':
					d['params']['url'] = node[0][0][0][1].text#todo: makemrobust
				elif node.tag == 'properties':
					for node2 in node:#mdr-core:episodeText
						if node2.attrib.get('name','') == 'mdr-core:episodeText':
							d['metadata']['name'] = node2[0].text
						if node2.attrib.get('name','') == 'mdr-core:broadcastSeriesTitle':
							d['metadata']['tvshowtitle'] = node2[0].text
						if node2.attrib.get('name','') == 'mdr-core:headline':
							if not '_name' in d:
								d['metadata']['name'] = node2[0].text
							if not '_tvshowtitle' in d:
								d['metadata']['tvshowtitle'] = node2[0].text
						if node2.attrib.get('name','') == 'mdr-core:fsk':
							d['metadata']['mpaa'] = node2[0].text
						if node2.attrib.get('name','') == 'mdr-core:language':
							d['metadata']['lang'] = node2[0].text
						if node2.attrib.get('name','') == 'mdr-core:episodeNumber':
							d['metadata']['episode'] = node2[0].text
						if node2.attrib.get('name','') == 'mdr-core:duration':
							s = node2[0].text.split(':')
							d['metadata']['duration'] = str(int(s[0]) * 3600 + int(s[1]) * 60 + int(s[2]))
				elif node.tag == 'childNodes':
					for node2 in node:
						if node2.attrib.get('name','') == 'mdr-core:teaserImage':
							try:
								d['metadata']['art']['thumb'] = _getThumb(node2)
								#for node3 in node2[0]:
								#	if node3.attrib.get('name','') == 'sophora:reference':
								#		d['thumb'] = node3[1][0][0].text.replace('.html','-resimage_v-variantBig16x9_w-960.png?version=4333')
							except: pass
						elif node2.attrib.get('name','') == 'mdr-core:copyText':
							try:
								for node3 in node2:
									if node3.tag == 'childNodes':
										for property in node3[0][0]:
											if property.attrib.get('name','') == 'sophora-extension:text':
												if property[0].text is not None:
													d['metadata']['plot'] = property[0].text.replace('<br/>','\n')
							except: pass
			self.result['items'].append(d)
		return self.result

	def parseMdrPlus(self,url):
		response = requests.get(url).text
		root = ET.fromstring(response)
		for property1 in root.find('childNodes').find('childNode').find('childNodes').find('childNode').find('childNodes').find('childNode').find('properties'):
			if property1.attrib.get('name','') == 'sophora:reference':
				#for document in property1.find('property').find('document').find('customElements').find('queryResult'):
				for document in property1.find('document').find('customElements').find('queryResult'):
					
					d = {'type':'video', 'params':{'mode':'libMdrPlay'}, 'metadata':{'art':{}}}
					if document.find('customElements').find('duration') is not None:
						d['metadata']['duration'] = self._durationToS(document.find('customElements').find('duration').text)
					d['params']['url'] = document.find('customElements').find('metaxmlUrl').text
					for property2 in document.find('properties'):
						if property2.attrib.get('name','') == 'mdr-core:headline':
							d['metadata']['name'] = property2[0].text
						if property2.attrib.get('name','') == 'mdr-core:teaserText':
							if property2[0].text is not None:
								d['metadata']['plot'] = property2[0].text
					for childNode in document.find('childNodes'):
						if childNode.attrib.get('name','') == 'mdr-core:teaserImage':
							d['metadata']['art']['thumb'] = self._getThumb(childNode)
					self.result['items'].append(d)
		return self.result

	def parsePlus(self,url):
		response = requests.get(url).text
		root = ET.fromstring(response)
		for document in root.find('customElements').find('queryResult'):
			d = {'type':'video', 'params':{'mode':'libMdrPlay'}, 'metadata':{'art':{}}}
			d['params']['url'] = document.find('customElements').find('metaxmlUrl').text
			if document.find('customElements').find('duration') is not None:
				d['metadata']['duration'] = self._durationToS(document.find('customElements').find('duration').text)
			for property2 in document.find('properties'):
				if property2.attrib.get('name','') == 'mdr-core:headline':
					d['metadata']['name'] = property2[0].text
					if d['metadata']['name'].startswith('Livestream: '): d['metadata']['name'] = d['metadata']['name'][12:]
					elif d['metadata']['name'].startswith('Livestream - '): d['metadata']['name'] = d['metadata']['name'][13:]
				if property2.attrib.get('name','') == 'mdr-core:teaserText':
					if property2[0].text is not None:
						d['metadata']['plot'] = property2[0].text
			for childNode in document.find('childNodes'):
				if childNode.attrib.get('name','') == 'mdr-core:teaserImage':
					d['metadata']['art']['thumb'] = self._getThumb(childNode)
			self.result['items'].append(d)
		return self.result

	def parseVideo(self,url):
		d = {'media':[]}
		if url.endswith('m3u8'):
			d['media'] = [{'url':video, 'type':'video', 'stream':'HLS'}]
			return d #m3u8 already supplied!?!?'
		if 'eventlivestreamzweiww-1378' in url:
			d['media'] = [{'url':'https://mdrevent2hls-lh.akamaihd.net/i/livetvmdrevent2_ww@513991/master.m3u8', 'type':'video', 'stream':'HLS'}]
			return d
		response = requests.get(url).text
		video = re.compile('<adaptiveHttpStreamingRedirectorUrl>(.+?)</adaptiveHttpStreamingRedirectorUrl>', re.DOTALL).findall(response)[0]
		d['media'] = [{'url':video, 'type':'video', 'stream':'HLS'}]
		if '<videoSubtitleUrl>' in response:
			sub = re.compile('<videoSubtitleUrl>(.+?)</videoSubtitleUrl>', re.DOTALL).findall(response)[0]
			d['subtitle'] = [{'url':sub, 'type': 'ttml', 'lang':'de'}]
		return d

	def _getThumb(self,teaserImage):
		for property in teaserImage.find('properties'):
			if property.attrib.get('name','') == 'sophora:reference':
				return property.find('document').find('customElements').find('teaserimageResponsive').find('url').text.replace('**imageVariant**','variantBig16x9').replace('**width**','960')
				try:
				#	return property.find('document').find('customElements').find('htmlUrl').text.replace('.html','-resimage_v-variantBig16x9_w-960.png?version=4333')
					return property.find('document').find('customElements').find('teaserimageResponsive').find('url').text.replace('**imageVariant**','variantBig16x9').replace('**width**','960')
				except: 
					return ''
					
	def _durationToS(self,d):
		s = d.split(':')
		if len(s) == 2:
			return str(int(s[0]) * 60 + int(s[1]))
		else:
			return '0'