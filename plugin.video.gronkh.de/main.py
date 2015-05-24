#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys, urlparse, urllib, json, datetime, os, hashlib, sqlite3, time, uuid, platform

import xbmcaddon, xbmcplugin, xbmcgui, xbmcvfs

from bs4 import BeautifulSoup
import requests

addonname		= 'plugin.video.gronkh.de'
addon 			= xbmcaddon.Addon(id=addonname)
loc 			= addon.getLocalizedString
cachedir		= 'special://userdata/addon_data/plugin.video.gronkh.de/caches/'

if sys.argv[1] == 'clearcache':
	dirs, files = xbmcvfs.listdir(cachedir)
	for f in files:
		xbmcvfs.delete(cachedir + f)
	dialog = xbmcgui.Dialog()
	dialog.notification('gronkh.DE', loc(30004), xbmcgui.NOTIFICATION_INFO, 5000)
	quit()

addon_handle 	= int(sys.argv[1])
addondir 		= xbmc.translatePath(addon.getAddonInfo('profile'))

icondir			= 'special://home/addons/plugin.video.gronkh.de/resources/media/'
fanart			= 'special://home/addons/plugin.video.gronkh.de/fanart.jpg'

setting 		= addon.getSetting
params 			= urlparse.parse_qs(sys.argv[2][1:])

baseurl			= 'http://gronkh.1750studios.com/api/v1/'

twitchStreamInfo= 'https://api.twitch.tv/kraken/streams/'

twitchnames		= ['gronkh']

if not setting('user-id'):
	addon.setSetting('user-id', uuid.uuid4().hex[:16])

##### Helpers
def makeUrl(params):
	return sys.argv[0] + '?' + urllib.urlencode(params)

def getUserAgent():
	if setting('user-agent'):
		return setting('user-agent') + addon.getAddonInfo('version')
	kodiversion = xbmc.getInfoLabel('System.BuildVersionShort')
	addonversion = addon.getAddonInfo('version')
	busytext = xbmc.getLocalizedString(503)
	os = xbmc.getInfoLabel('System.OsVersionInfo')
	# This has to be done, since Kodi sometimes returns "Busy", what is wrong … and then even localized…
	while os == busytext.encode('utf-8'):
		os = xbmc.getInfoLabel('System.OsVersionInfo')
	useragent = 'Kodi/' + kodiversion + ' (' + os + ') ' + addonname + '/'
	addon.setSetting('user-agent', useragent)
	return useragent + addonversion

def getCachedJson(url):
	headers = {
		"DNT": 1 if (setting('donottrack') == True) else 0,
		"X-UID": setting('user-id'),
		"User-Agent": getUserAgent(),
		"X-Resolution": xbmc.getInfoLabel('System.ScreenResolution').split('@')[0]
	}
	if not xbmcvfs.exists(cachedir):
		xbmcvfs.mkdirs(cachedir)

	if not xbmcvfs.exists(os.path.join(cachedir, 'etags.json')):
		etagsf = xbmcvfs.File(os.path.join(cachedir, 'etags.json'), 'w')
		etagsf.write('{}')
		etagsf.close()

	etagsf = xbmcvfs.File(os.path.join(cachedir, 'etags.json'), 'r')
	etags = json.loads(etagsf.read())
	etagsf.close()

	if url not in etags:
		r = requests.get(baseurl + url + '/', headers=headers)
		etags[url] = {}
		etags[url]['path'] = cachedir + hashlib.md5(url).hexdigest() + '.json'
		etags[url]['etag'] = r.headers['Etag']

		f = xbmcvfs.File(etags[url]['path'], 'w')
		f.write(r.content)
		f.close()

		j = json.loads(r.content)
		
	else:
		headers['If-None-Match'] = etags[url]['etag']
		print headers
		r = requests.get(baseurl + url + '/', headers=headers)
		if r.status_code == 304:
			etagsf = xbmcvfs.File(etags[url]['path'], 'r')
			j = json.loads(etagsf.read())
			etagsf.close()
		else:
			etags[url]['path'] = cachedir + hashlib.md5(url).hexdigest() + '.json'
			etags[url]['etag'] = r.headers['Etag']

			f = xbmcvfs.File(etags[url]['path'], 'w')
			f.write(r.content)
			f.close()

			j = json.loads(r.content)

	etagsf = xbmcvfs.File(os.path.join(cachedir, 'etags.json'), 'w')
	etagsf.write(json.dumps(etags))
	etagsf.close()

	return j

def makeTimeString(s):
	m, s = divmod(s, 60)
	h, m = divmod(m, 60)
	if h is not 0:
		return "%d:%02d:%02d" % (h, m, s)
	else:
		return "%02d:%02d" % (m, s)

##### Functions
def index(author=None):
	if author:
		li = xbmcgui.ListItem(loc(30001))
		li.setIconImage(icondir + 'games.png')
		li.setThumbnailImage(icondir + 'games.png')
		li.setArt({'fanart' : fanart})
		params = {'mode' : 'LPs', 'author' : author}
		xbmcplugin.addDirectoryItem(handle=addon_handle, url=makeUrl(params), listitem=li, isFolder=True)

		li = xbmcgui.ListItem(loc(30002))
		li.setIconImage(icondir + 'tests.png')
		li.setThumbnailImage(icondir + 'tests.png')
		li.setArt({'fanart' : fanart})
		params = {'mode' : 'LTs', 'author' : author}
		xbmcplugin.addDirectoryItem(handle=addon_handle, url=makeUrl(params), listitem=li, isFolder=True)
	else:
		li = xbmcgui.ListItem(loc(30010))
		li.setIconImage(icondir + 'recent.png')
		li.setThumbnailImage(icondir + 'recent.png')
		li.setArt({'fanart' : fanart})
		params = {'mode' : 'recent'}
		xbmcplugin.addDirectoryItem(handle=addon_handle, url=makeUrl(params), listitem=li, isFolder=True)

		li = xbmcgui.ListItem(loc(30007))
		li.setIconImage(icondir + 'live.png')
		li.setThumbnailImage(icondir + 'live.png')
		li.setArt({'fanart' : fanart})
		params = {'mode' : 'live'}
		xbmcplugin.addDirectoryItem(handle=addon_handle, url=makeUrl(params), listitem=li, isFolder=True)

		li = xbmcgui.ListItem(loc(30001))
		li.setIconImage(icondir + 'games.png')
		li.setThumbnailImage(icondir + 'games.png')
		li.setArt({'fanart' : fanart})
		params = {'mode' : 'LPs'}
		xbmcplugin.addDirectoryItem(handle=addon_handle, url=makeUrl(params), listitem=li, isFolder=True)

		li = xbmcgui.ListItem(loc(30002))
		li.setIconImage(icondir + 'tests.png')
		li.setThumbnailImage(icondir + 'tests.png')
		li.setArt({'fanart' : fanart})
		params = {'mode' : 'LTs'}
		xbmcplugin.addDirectoryItem(handle=addon_handle, url=makeUrl(params), listitem=li, isFolder=True)

		li = xbmcgui.ListItem(loc(30003))
		li.setIconImage(icondir + 'authors.png')
		li.setThumbnailImage(icondir + 'authors.png')
		li.setArt({'fanart' : fanart})
		params = {'mode' : 'show_authors'}
		xbmcplugin.addDirectoryItem(handle=addon_handle, url=makeUrl(params), listitem=li, isFolder=True)

	xbmcplugin.endOfDirectory(addon_handle)

def showAuthors():
	authors = getCachedJson('authors')
	for author in authors['authors']:
		li = xbmcgui.ListItem(author['name'])
		li.setIconImage(author['avatar'])
		li.setThumbnailImage(author['avatar'])
		li.setArt({'fanart' : author['fanart']})
		params = {'author' : author['name']}
		xbmcplugin.addDirectoryItem(handle=addon_handle, url=makeUrl(params),
			listitem=li, isFolder=True)
		xbmcplugin.addSortMethod(addon_handle,
			sortMethod=xbmcplugin.SORT_METHOD_LABEL)
	xbmcplugin.endOfDirectory(addon_handle)

def showTests(author=None):
	if author:
		games = getCachedJson('tests/' + author)
		for game in games['tests']:
			li = xbmcgui.ListItem(game['gamename'])
			li.setIconImage(game['thumb'])
			li.setThumbnailImage(game['thumb'])
			params = {'mode' : 'play_video', 'game' : json.dumps(game)}
			li.setInfo('video', {
									'title' : game['gamename'],
									'episode': 1,
									'season': 1,
									'director': game['author'],
									'plot': game['description'],
									'rating': game['rating'],
									'duration': makeTimeString(game['duration']),
									'votes': str(game['votes']) + ' ' + loc(30008),
									'premiered': game['aired']
								})
			li.setArt({'thumb': game['thumb'],
						'poster': game['poster'],
						'fanart': game['thumb']})
			li.setProperty('isPlayable','true')
			li.addStreamInfo('video', {'duration': game['duration']})
			xbmcplugin.addDirectoryItem(handle=addon_handle, url=makeUrl(params),
				listitem=li)
			xbmcplugin.addSortMethod(addon_handle,
				sortMethod=xbmcplugin.SORT_METHOD_LABEL)
		xbmcplugin.endOfDirectory(addon_handle)
	else:
		games = getCachedJson('tests')
		for game in games['tests']:
			li = xbmcgui.ListItem(game['gamename'])
			li.setIconImage(game['thumb'])
			li.setThumbnailImage(game['thumb'])
			params = {'mode' : 'play_video', 'game' : json.dumps(game)}
			li.setInfo('video', {
									'title' : game['gamename'],
									'episode': 1,
									'season': 1,
									'director': game['author'],
									'plot': game['description'],
									'rating': game['rating'],
									'duration': makeTimeString(game['duration']),
									'votes': str(game['votes']) + ' ' + loc(30008),
									'premiered': game['aired']
								})
			li.setArt({'thumb': game['thumb'],
						'poster': game['poster'],
						'fanart': game['thumb']})
			li.setProperty('isPlayable','true')
			li.addStreamInfo('video', {'duration': game['duration']})
			xbmcplugin.addDirectoryItem(handle=addon_handle, url=makeUrl(params),
				listitem=li)
			xbmcplugin.addSortMethod(addon_handle,
				sortMethod=xbmcplugin.SORT_METHOD_LABEL)
		xbmcplugin.endOfDirectory(addon_handle)

def showLPs(author=None):
	if author:
		games = getCachedJson('lets-plays/' + author)
		for game in games['lets-plays']:
			li = xbmcgui.ListItem(game['gamename'])
			li.setIconImage(game['postersmall'])
			li.setThumbnailImage(game['posterbig'])
			li.setArt({'fanart' : fanart})
			params = {'mode' : 'show_episodes', 'game' : json.dumps(game)}
			xbmcplugin.addDirectoryItem(handle=addon_handle, url=makeUrl(params),
				listitem=li, isFolder=True)
			xbmcplugin.addSortMethod(addon_handle,
				sortMethod=xbmcplugin.SORT_METHOD_LABEL)
		xbmcplugin.endOfDirectory(addon_handle)
	else:
		games = getCachedJson('lets-plays')
		for game in games['lets-plays']:
			li = xbmcgui.ListItem(game['gamename'] + ' (' + game['author'] + ')')
			li.setIconImage(game['postersmall'])
			li.setThumbnailImage(game['posterbig'])
			li.setArt({'fanart' : fanart})
			params = {'mode' : 'show_episodes', 'game' : json.dumps(game)}
			xbmcplugin.addDirectoryItem(handle=addon_handle, url=makeUrl(params),
				listitem=li, isFolder=True)
			xbmcplugin.addSortMethod(addon_handle,
				sortMethod=xbmcplugin.SORT_METHOD_LABEL)
		xbmcplugin.endOfDirectory(addon_handle)

def showEpisodes(game):
	gamej = json.loads(game)
	episodes = getCachedJson('episodes/' + gamej['slug'])
	for episode in episodes['episodes']:
		li = xbmcgui.ListItem(episode['episodename'].split(': ')[-1])
		li.setIconImage(episode['thumb'])
		li.setThumbnailImage(episode['thumb'])
		params = {'mode' : 'play_video', 'game' : json.dumps(gamej), 'episode': json.dumps(episode)}
		li.setInfo('video', {
								'title' : episode['episodename'].split(': ')[-1],
								'originaltitle': gamej['gamename'],
								'episode': episode['episode'],
								'season': 1,
								'director': gamej['author'],
								'plot': episode['description'],
								'rating': episode['rating'],
								'duration': makeTimeString(episode['duration']),
								'votes': str(episode['votes']) + ' ' + loc(30008),
								'premiered': episode['aired']
							})
		li.setArt({'thumb': episode['thumb'],
					'poster': gamej['posterbig'],
					'fanart': episode['thumb']})
		li.setProperty('isPlayable','true')
		li.addStreamInfo('video', {'duration': episode['duration']})
		xbmcplugin.setContent(addon_handle, 'episodes')
		xbmcplugin.addDirectoryItem(handle=addon_handle, url=makeUrl(params),
			listitem=li)
		xbmcplugin.addSortMethod(addon_handle,
			sortMethod=xbmcplugin.SORT_METHOD_EPISODE)
	xbmcplugin.endOfDirectory(addon_handle)

def showRecentEpisodes():
	episodes = getCachedJson('recent')
	for episode in episodes['episodes']:
		gamej = episode['game']
		li = xbmcgui.ListItem(episode['episodename'].split(': ')[-1])
		li.setIconImage(episode['thumb'])
		li.setThumbnailImage(episode['thumb'])
		params = {'mode' : 'play_video', 'game' : json.dumps(gamej), 'episode': json.dumps(episode)}
		li.setInfo('video', {
								'title' : episode['episodename'].split(': ')[-1],
								'originaltitle': gamej['gamename'],
								'episode': episode['episode'],
								'season': 1,
								'director': gamej['author'],
								'plot': episode['description'],
								'rating': episode['rating'],
								'duration': makeTimeString(episode['duration']),
								'votes': str(episode['votes']) + ' ' + loc(30008),
								'premiered': episode['aired']
							})
		li.setArt({'thumb': episode['thumb'],
					'poster': gamej['posterbig'],
					'fanart': episode['thumb']})
		li.setProperty('isPlayable','true')
		li.addStreamInfo('video', {'duration': episode['duration']})
		xbmcplugin.setContent(addon_handle, 'episodes')
		xbmcplugin.addDirectoryItem(handle=addon_handle, url=makeUrl(params),
			listitem=li)
		xbmcplugin.addSortMethod(addon_handle,
			sortMethod=xbmcplugin.SORT_METHOD_NONE)
	xbmcplugin.endOfDirectory(addon_handle)

def startVideo(g, e=None):
	game = json.loads(g)
	if e == None:
		li = xbmcgui.ListItem(path='plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=' + game['youtube'])
		li.setIconImage(game['thumb'])
		li.setThumbnailImage(game['thumb'])
		li.setInfo('video', {
								'title' : game['gamename'],
								'episode': 1,
								'season': 1,
								'director': game['author'],
								'plot': game['description'],
								'rating': game['rating'],
								'duration': makeTimeString(game['duration']),
								'votes': str(game['votes']) + ' ' + loc(30008),
								'premiered': game['aired']
							})
		li.setArt({'thumb': game['thumb'],
					'poster': game['poster'],
					'fanart': game['thumb']})
		li.setProperty('isPlayable','true')
		li.addStreamInfo('video', {'duration': game['duration']})
		xbmcplugin.setResolvedUrl(handle=addon_handle, succeeded=True, listitem=li)
	else:
		episode = json.loads(e)
		li = xbmcgui.ListItem(path='plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=' + episode['youtube'])
		li.setIconImage(episode['thumb'])
		li.setThumbnailImage(episode['thumb'])
		li.setInfo('video', {
								'title' : episode['episodename'].split(': ')[-1],
								'originaltitle': game['gamename'],
								'episode': episode['episode'],
								'season': 1,
								'director': game['author'],
								'plot': episode['description'],
								'tracknumber': episode['episode'],
								'rating': episode['rating'],
								'duration': makeTimeString(episode['duration']),
								'votes': str(episode['votes']) + ' ' + loc(30008),
								'premiered': episode['aired']
							})
		li.setArt({'thumb': episode['thumb'],
					'poster': game['posterbig'],
					'fanart': episode['thumb']})
		li.setProperty('isPlayable','true')
		li.addStreamInfo('video', {'duration': episode['duration']})
		xbmcplugin.setResolvedUrl(handle=addon_handle, succeeded=True, listitem=li)

def showLiveStreams():
	for name in twitchnames:
		r = requests.get(twitchStreamInfo + name, headers={'Accept': 'application/vnd.twitchtv.v3+json'})
		stream = json.loads(r.content)['stream']
		z = 0
		if stream:
			while 'bio' in stream['channel']:
				r = requests.get(twitchStreamInfo + name, headers={'Accept': 'application/vnd.twitchtv.v3+json'})
				stream = json.loads(r.content)['stream']
				z = z + 1
				if z > 5:
					dialog = xbmcgui.Dialog()
					dialog.notification('gronkh.DE', loc(30009), xbmcgui.NOTIFICATION_ERROR, 10000)
					quit()
		if stream:
			li = None
			if stream['game']:
				li = xbmcgui.ListItem(stream['channel']['display_name'] + ' - ' + loc(30006) + ': ' + stream['game'])
			else:
				li = xbmcgui.ListItem(stream['channel']['display_name'] + ' - ' + stream['channel']['status'])
			li.setIconImage(stream['channel']['logo'] + '?' + unicode(time.time()))
			li.setThumbnailImage(stream['preview']['large'] + '?' + unicode(time.time()))
			li.setArt({	'fanart' : stream['channel']['profile_banner'],
						'clearlogo' : stream['channel']['logo'],
						'banner' : stream['channel']['banner']})
			li.setInfo('video', {
									'director': stream['channel']['display_name'],
									'plotoutline': stream['channel']['status']
								})
			li.setProperty('isPlayable','true')
			params = {'mode' : 'start_livestream', 'stream' : json.dumps(stream), 'name': name}
			xbmcplugin.addDirectoryItem(handle=addon_handle, url=makeUrl(params),
				listitem=li)
		else:
			li = xbmcgui.ListItem(u'[' + name + u'] – ' + loc(30005))
			li.setArt({	'fanart' : fanart})
			li.setInfo('video', {
									'title' : u'[' + name + u'] – ' + loc(30005),
									'episode': 1,
									'season': 1,
									'director': name
								})
			li.setProperty('isPlayable','true')
			params = {'mode' : 'start_livestream', 'stream' : json.dumps(stream), 'name': name}
			xbmcplugin.addDirectoryItem(handle=addon_handle, url=makeUrl(params),
				listitem=li)
	xbmcplugin.addSortMethod(addon_handle, sortMethod=xbmcplugin.SORT_METHOD_LABEL)
	xbmcplugin.endOfDirectory(addon_handle)

def startLiveStream(stream, name):
	r = requests.get('https://api.twitch.tv/api/channels/' + name + '/access_token')
	j = json.loads(r.content)

	token 	= j['token']
	sig 	= j['sig']

	if stream:
			li = None
			if stream['game']:
				li = xbmcgui.ListItem(stream['channel']['display_name'] + ' - ' + loc(30006) + ': ' + stream['game'],
					path='http://usher.twitch.tv/api/channel/hls/' +
					name + '.m3u8?player=twitchweb&token=' +
					token + '&sig=' +
					sig + '&allow_audio_only=true&allow_source=true&type=any&p=666')
			else:
				li = xbmcgui.ListItem(stream['channel']['display_name'] + ' - ' + stream['channel']['status'],
					path='http://usher.twitch.tv/api/channel/hls/' +
					name + '.m3u8?player=twitchweb&token=' +
					token + '&sig=' +
					sig + '&allow_audio_only=true&allow_source=true&type=any&p=666')
			li.setIconImage(stream['channel']['logo'])
			li.setThumbnailImage(stream['preview']['large'] + '?' + unicode(time.time()))
			li.setArt({	'fanart' : stream['channel']['profile_banner'],
						'clearlogo' : stream['channel']['logo'],
						'banner' : stream['channel']['banner']})
			li.setInfo('video', {
									'director': stream['channel']['display_name'],
									'plotoutline': stream['channel']['status']
								})
			li.setProperty('isPlayable','true')
			xbmcplugin.setResolvedUrl(handle=addon_handle, succeeded=True, listitem=li)
	else:
		li = xbmcgui.ListItem(u'[' + name + u'] – ' + loc(30005),
			path='http://usher.twitch.tv/api/channel/hls/' +
			name + '.m3u8?player=twitchweb&token=' +
			token + '&sig=' +
			sig + '&allow_audio_only=true&allow_source=true&type=any&p=666')
		if stream:
			li.setIconImage(stream['preview']['medium'])
			li.setThumbnailImage(stream['preview']['large'])
		li.setArt({	'fanart' : fanart})
		li.setInfo('video', {
								'title' : u'[' + name + u'] – ' + loc(30005),
								'episode': 1,
								'season': 1,
								'director': name
							})
		li.setProperty('isPlayable','true')
		xbmcplugin.setResolvedUrl(handle=addon_handle, succeeded=True, listitem=li)

if 'mode' in params:
	if params['mode'][0] == 'show_authors':
		showAuthors()
	elif params['mode'][0] == 'LTs':
		if 'author' in params:
			showTests(params['author'][0])
		else:
			showTests()
	elif params['mode'][0] == 'LPs':
		if 'author' in params:
			showLPs(params['author'][0])
		else:
			showLPs()
	elif params['mode'][0] == 'show_episodes':
		showEpisodes(params['game'][0])
	elif params['mode'][0] == 'play_video':
		if 'episode' in params:
			startVideo(params['game'][0], params['episode'][0])
		else:
			startVideo(params['game'][0])
	elif params['mode'][0] == 'live':
		showLiveStreams()
	elif params['mode'][0] == 'start_livestream':
		startLiveStream(json.loads(params['stream'][0]), params['name'][0])
	elif params['mode'][0] == 'recent':
		showRecentEpisodes()
else:
	if 'author' in params:
		index(params['author'][0])
	else:
		index()