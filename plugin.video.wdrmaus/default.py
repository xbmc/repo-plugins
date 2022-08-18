# -*- coding: utf-8 -*-
import libwdr
import re
import requests

xml = 'http://www.wdrmaus.de/_export/videositemap.php5'

class wdrmaus(libwdr.libwdr):
	def __init__(self):
		libwdr.libwdr.__init__(self)
		self.modes['mausListVideos'] = self.mausListVideos

	def libWdrListMain(self):
		response = requests.get(xml).text
		categories = re.compile('<video:category>(.+?)</video:category>', re.DOTALL).findall(response)
		result = {'items':[],'name':'root'}
		names = []
		for cat in categories:
			if not cat in names:
				result['items'].append({'metadata':{'name':cat}, 'params':{'mode':'mausListVideos', 'cat':cat}, 'type':'dir'})
				names.append(cat)
		return result
	
	def mausListVideos(self):
		result = {'items':[]}
		response = requests.get(xml).text
		videos = re.compile('<url>(.+?)</url>', re.DOTALL).findall(response)
		for video in videos:
			if self.params['cat'] == re.compile('<video:category>(.+?)</video:category>', re.DOTALL).findall(video)[0]:
				d = {'metadata':{'art':{}}, 'params':{'mode':'libWdrPlayJs'}, 'type':'video'}
				d['metadata']['name'] = re.compile('<video:title><!\[CDATA\[(.+?)\]\]></video:title>', re.DOTALL).findall(video)[0].replace('![CDATA[','').replace(']]','')
				d['metadata']['art']['thumb'] = re.compile('<video:thumbnail_loc>(.+?)</video:thumbnail_loc>', re.DOTALL).findall(video)[0].replace('<![CDATA[','').replace(']]>','')
				d['params']['url'] = re.compile('<video:player_loc.+?>(.+?)</video:player_loc>', re.DOTALL).findall(video)[0].replace('<![CDATA[','').replace(']]>','')
				result['items'].append(d)
		return result

o = wdrmaus()
o.action()