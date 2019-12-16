# -*- coding: utf-8 -*-
import libmediathek3 as libMediathek
import resources.lib.jsonparser as jsonParser

translation = libMediathek.getTranslation
skipToSeries = libMediathek.getSetting('skipToSeries') == 'true'

def main():
	return jsonParser.parseMain()
	
def listSeasons():
	return jsonParser.parseSeasons(params['id'], params)
	
def listEpisodes():
	return jsonParser.parseEpisodes(params['id'])
	
def listVideos():
	return jsonParser.parseVideos(params['id'])
	
def play():
	import nexx
	#nexx.operations = {'byid':'2835669fdcfe2d07351d633353bf87a8'}
	nexx.operations = {'byid':'f058a27469d8b709c3b9db648cae47c2'}
	#nexx.cid = '114994613565243649'
	nexx.cid = '1152923389105252956'
	nexx.channelId = '741'
	nexx.origin = 'https://www.funk.net'
	return nexx.getVideoUrl(params['sourceId'])


modes = {
'main': main,
'listSeasons': listSeasons,
'listEpisodes': listEpisodes,
'listVideos': listVideos,
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
