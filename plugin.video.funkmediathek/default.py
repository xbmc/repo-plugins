# -*- coding: utf-8 -*-
import libmediathek3 as libMediathek
import xbmc
import xbmcaddon
import xbmcplugin
import resources.lib.jsonparser as jsonParser
import resources.lib.kalturaparser as kalturaParser

base = 'https://www.funk.net'

translation = xbmcaddon.Addon().getLocalizedString

#squashShows = xbmcaddon.Addon().getSetting('squashShows') == 'true'
#preferOV = xbmcaddon.Addon().getSetting('preferOV') == 'true'
skipToSeries = xbmcaddon.Addon().getSetting('skipToSeries') == 'true'

def main():
	if skipToSeries:
		params['url'] = 'https://api.funk.net/v1.0/content/series/?page=0&size=50'
		return listDir()
	else:
		l = []
		l.append({'_name':translation(30503), 'mode':'listDir', '_type': 'dir', 'url':'https://api.funk.net/v1.0/content/formats/?page=0&size=50'})
		l.append({'_name':translation(30504),  'mode':'listDir',   '_type': 'dir', 'url':'https://api.funk.net/v1.0/content/series/?page=0&size=50'})
		return l
	
def listDir():
	return jsonParser.parse(params['url'])
	
def play():
	return kalturaParser.getVideoUrl(params['entryId'])


modes = {
'main': main,
'listDir': listDir,
'play': play
}	

def list():	
	global params
	params = libMediathek.get_params()
	global pluginhandle
	pluginhandle = int(sys.argv[1])
	
	mode = params.get('mode','main')
	if mode == 'play':
		libMediathek.play(play())
	else:
		l = modes.get(mode)()
		libMediathek.addEntries(l)
		xbmcplugin.endOfDirectory(int(sys.argv[1]),cacheToDisc=True)	
list()