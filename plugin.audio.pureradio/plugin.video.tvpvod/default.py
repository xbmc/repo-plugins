# -*- coding: utf-8 -*-

import urllib
import urllib2
import urlparse
import json
import xbmcgui
import xbmcplugin
import xbmcaddon

__settings__ = xbmcaddon.Addon('plugin.video.tvpvod')

BASE_URL = sys.argv[0]
ADDON_HANDLE = int(sys.argv[1])

MAIN_URL = 'http://vod.tvp.customers.multiscreen.tv/'
MENU_URL = MAIN_URL + 'navigation/'
URL_PARAMS = 'pageSize=%u&thumbnailSize=240&deviceType=1&pageNo=%u' 
SERIES_URL = MAIN_URL + 'Movies/SeriesJSON?' + URL_PARAMS + '&parentId=%s'
EPISODES_URL = MAIN_URL + 'Movies/EpisodesJSON?' + URL_PARAMS + '&parentId=%s'
VIDEO_URL = 'http://www.tvp.pl/shared/cdn/tokenizer_v2.php?object_id=%s'

def getMainMenu():
	li = []
	jsonData = json.load(getUrlRequestData(MENU_URL))
	for item in jsonData:
		if item['Title'] == 'VOD':
			for category in item['SubCategories']:
				item = xbmcgui.ListItem(category['Title'], category['Url'])
				li.append((buildUrl({'mode': category['ListType'], 'ident': category['Id']}), item, True))
			break
	xbmcplugin.addDirectoryItems(ADDON_HANDLE, li, len(li))
	xbmcplugin.endOfDirectory(ADDON_HANDLE)

def getSeries(ident, pageNumber, pageSize):
	li = []
	jsonData = json.load(getUrlRequestData(SERIES_URL % (pageSize, pageNumber, ident)))
	for series in jsonData:
		item = xbmcgui.ListItem(series['title'], series['lead_root'])
		li.append((buildUrl({'mode': 'episodes', 'ident': series['asset_id']}), item, True))
	xbmcplugin.addDirectoryItems(ADDON_HANDLE, li, len(li))
	xbmcplugin.endOfDirectory(ADDON_HANDLE)

def getEpisodes(ident, pageNumber, pageSize):
	li = []
	jsonData = json.load(getUrlRequestData(EPISODES_URL % (pageSize, pageNumber, ident)))
	for episode in jsonData:
		videoInfo = {
			'mode': 'video',
			'ident': episode['asset_id'],
			'title': (episode['website_title']+', '+episode['title']).encode('utf-8'),
		}
		item = xbmcgui.ListItem(videoInfo['title'])
		li.append((buildUrl(videoInfo), item, False))
	xbmcplugin.addDirectoryItems(ADDON_HANDLE, li, len(li))
	xbmcplugin.endOfDirectory(ADDON_HANDLE)

def getPlayer(ident, title):
	jsonData = json.load(getUrlRequestData(VIDEO_URL % (ident)))
	formats = jsonData['formats']
	videos = []
	for video in formats:
		if video['mimeType'] == 'video/mp4':
			videos.append((video['url'], int(video['totalBitrate'])))
	videos.sort(key=lambda tup: tup[1])
	li = xbmcgui.ListItem()
	li.setInfo('video', {'title': title})
	videoCount = len(videos)
	if int(__settings__.getSetting('resolution')) == 0:
		xbmc.Player().play(videos[0][0], li)
	elif int(__settings__.getSetting('resolution')) == 2:
		xbmc.Player().play(videos[videoCount-1][0], li)
	else:
		xbmc.Player().play(videos[int(videoCount/2)][0], li)

def getUrlRequestData(url):
	request = urllib2.Request(url)
	try:
		return urllib2.build_opener().open(request)
	except:
		return None

def buildUrl(query):
	return BASE_URL + '?' + urllib.urlencode(query)


xbmcplugin.setContent(ADDON_HANDLE, 'episodes')

params = {}
try:
	params = dict(arg.split("=") for arg in ((sys.argv[2][1:]).split("&")))
	for key in params:
		try: params[key] = urllib.unquote_plus(params[key])
		except: pass
except:
	params = {}

mode = params.get('mode', None)

if not mode:
	getMainMenu()
elif mode == 'series':
	getSeries(params.get('ident', None), int(params.get('pageNumber', 0)), int(params.get('pageSize', 9999)))
elif mode == 'episodes':
	getEpisodes(params.get('ident', None), int(params.get('pageNumber', 0)), int(params.get('pageSize', 9999)))
else:
	getPlayer(params.get('ident', None), params.get('title', None))
