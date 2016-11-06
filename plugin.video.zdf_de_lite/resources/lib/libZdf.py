# -*- coding: utf-8 -*-
import xbmc,xbmcplugin,xbmcgui,xbmcaddon
import urllib
import sys
import libMediathek2 as libMediathek
import libZdfJsonParser
from datetime import date, timedelta

addonID = 'plugin.video.zdf_de_lite'
translation = xbmcaddon.Addon(id='script.module.libMediathek').getLocalizedString
showSubtitles = xbmcaddon.Addon().getSetting('subtitle') == 'true'
#params = {}

#https://api.zdf.de/content/documents/zdf-startseite-100.json?profile=default
#https://api.zdf.de/content/documents/meist-gesehen-100.json?profile=teaser
#https://api.zdf.de/content/documents/meist-gesehen-100.json?profile=default
#https://api.zdf.de/content/documents/sendungen-100.json?profile=default
#api.zdf.de/search/documents?hasVideo=true&q=*&types=page-video&sender=ZDFneo&paths=%2Fzdf%2Fcomedy%2Fneo-magazin-mit-jan-boehmermann%2Ffilter%2C%2Fzdf%2Fcomedy%2Fneo-magazin-mit-jan-boehmermann&sortOrder=desc&limit=1&editorialTags=&sortBy=date&contentTypes=episode&exclEditorialTags=&allEditorialTags=false
#api.zdf.de/search/documents?hasVideo=true&q=*&types=page-video&sender=ZDFneo&paths=%2Fzdf%2Fnachrichten%2Fzdfspezial%2Ffilter%2C%2Fzdf%nachrichten%2Fzdfspezial&sortOrder=desc&limit=1&editorialTags=&sortBy=date&contentTypes=episode&exclEditorialTags=&allEditorialTags=false
#https://api.zdf.de/cmdm/epg/broadcasts?from=2016-10-28T05%3A30%3A00%2B02%3A00&to=2016-10-29T05%3A29%3A00%2B02%3A00&limit=500&profile=teaser
#https://api.zdf.de/cmdm/epg/broadcasts?from=2016-10-28T05%3A30%3A00%2B02%3A00&to=2016-10-29T05%3A29%3A00%2B02%3A00&limit=500&profile=teaser&tvServices=ZDF

channels = 	[
				'3sat',
				'ZDF',
				'ZDFinfo',
				'ZDFneo',
			]

def libZdfListMain():
	l = []
	l.append({'_name':translation(31031), 'mode':'libZdfListPage', 'type': 'dir', 'url':'https://api.zdf.de/content/documents/meist-gesehen-100.json?profile=default'})
	l.append({'_name':translation(31032), 'mode':'libZdfListAZ', 'type': 'dir'})
	l.append({'_name':translation(31033), 'mode':'libZdfListDate', 'type': 'dir'})
	l.append({'_name':translation(31034), 'mode':'libZdfListPage', 'type': 'dir', 'url':'https://api.zdf.de/search/documents?q=%2A&contentTypes=category'})
	l.append({'_name':translation(31039), 'mode':'libZdfSearch',   'type': 'dir'})
	"""
	l.append({'_name':translation(31032), 'mode':'listLetters',    'type': 'dir'})
	l.append({'_name':translation(31035), 'mode':'xmlListPage', 'type': 'dir', 'url':'http://www.zdf.de/ZDFmediathek/xmlservice/web/themen'})
	"""
	return l
	
def libZdfListAZ():
	return libZdfJsonParser.getAZ()
	
def libZdfListPage(url=False,type=False):
	return libZdfJsonParser.parsePage(params['url'])
	
def libZdfListVideos():
	return libZdfJsonParser.getVideos(params['url'])

def libZdfPlay():
	return libZdfJsonParser.getVideoUrl(params['url'])
	
def libZdfListDate():
	return libMediathek.populateDirDate('libZdfListDateChannels')
		
def libZdfListDateChannels():
	datum = params['datum']
	day = date.today() - timedelta(int(datum))
	yyyymmdd = day.strftime('%Y-%m-%d')
	l = []
	for channel in channels:
		dict = {}
		dict['mode'] = 'libZdfListPage'
		dict['name'] = channel
		dict['type'] = 'dir'
		dict['url']  = 'https://api.zdf.de/cmdm/epg/broadcasts?from='+yyyymmdd+'T00%3A00%3A00%2B02%3A00&to='+yyyymmdd+'T23%3A59%3A59%2B02%3A00&limit=500&profile=teaser&tvServices=ZDF'
		l.append(dict)
	return l
	
def libZdfSearch():
	keyboard = xbmc.Keyboard('', translation(31039))
	keyboard.doModal()
	if keyboard.isConfirmed() and keyboard.getText():
		search_string = urllib.quote_plus(keyboard.getText())
		params['url'] = "https://api.zdf.de/search/documents?q="+search_string
		return libZdfListPage()
		
def libZdfGetVideoHtml(url):
	import _utils
	import re
	response = _utils.getUrl(url)
	return libZdfJsonParser.getVideoUrl(re.compile('"contentUrl": "(.+?)"', re.DOTALL).findall(response)[0])

def list():	
	global params
	params = libMediathek.get_params()
	global pluginhandle
	pluginhandle = int(sys.argv[1])
	
	mode = params.get('mode','libZdfListMain')
	if mode == 'libZdfPlay':
		libMediathek.play(libZdfPlay())
		
	else:
		l = modes.get(mode,libZdfListMain)()
		libMediathek.addEntries(l)
		xbmcplugin.endOfDirectory(int(sys.argv[1]),cacheToDisc=True)	
	
modes = {
	'libZdfListMain':libZdfListMain,
	'libZdfListAZ':libZdfListAZ,
	'libZdfListVideos':libZdfListVideos,
	'libZdfListDate':libZdfListDate,
	'libZdfListDateChannels':libZdfListDateChannels,
	
	'libZdfSearch':libZdfSearch,
	'libZdfListPage':libZdfListPage,
	'libZdfPlay':libZdfPlay,
	}	