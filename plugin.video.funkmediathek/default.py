# -*- coding: utf-8 -*-
import libmediathek3 as libMediathek
import resources.lib.jsonparser as jsonParser

translation = libMediathek.getTranslation
skipToSeries = libMediathek.getSetting('skipToSeries') == 'true'

def main():
	if skipToSeries:
		params['url'] = 'https://api.funk.net/v1.1/content/series/?page=0&size=50'
		return listDir()
	else:
		l = []
		l.append({'_name':translation(30503,'plugin.video.funkmediathek'), 'mode':'listDir', '_type': 'dir', 'url':'https://api.funk.net/v1.1/content/formats/?page=0&size=50'})
		l.append({'_name':translation(30504,'plugin.video.funkmediathek'), 'mode':'listDir', '_type': 'dir', 'url':'https://api.funk.net/v1.1/content/series/?page=0&size=50'})
		return l
	
def listDir():
	return jsonParser.parse(params['url'])
	
def play():
	import nexx
	nexx.operations = {'byid':'2835669fdcfe2d07351d633353bf87a8'}
	nexx.cid = '114994613565243649'
	nexx.channelId = '741'
	nexx.origin = 'https://www.funk.net'
	return nexx.getVideoUrl(params['sourceId'])


modes = {
'main': main,
'listDir': listDir,
'play': play
}	

def list():	
	global params
	params = libMediathek.get_params()
	
	mode = params.get('mode','main')
	if mode == 'play':
		libMediathek.play(play())
	else:
		l = modes.get(mode)()
		libMediathek.addEntries(l)
		libMediathek.endOfDirectory()
list()