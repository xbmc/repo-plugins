
import xbmc, xbmcgui, xbmcplugin, xbmcaddon, urllib, re, string, sys, os, time, buggalo, urllib2, base64, ast
import simplejson as json

plugin =  'Revision3'
__author__ = 'stacked <stacked.xbmc@gmail.com>'
__url__ = 'http://code.google.com/p/plugin/'
__date__ = '05-12-2013'
__version__ = '3.0.14'
settings = xbmcaddon.Addon(id='plugin.video.revision3')
buggalo.SUBMIT_URL = 'http://www.xbmc.byethost17.com/submit.php'
dbg = False
dbglevel = 3
next_thumb = os.path.join( settings.getAddonInfo( 'path' ), 'resources', 'media', 'next.png' )
downloads_thumb = os.path.join( settings.getAddonInfo( 'path' ), 'resources', 'media', 'downloads.png' )
archived_thumb = os.path.join( settings.getAddonInfo( 'path' ), 'resources', 'media', 'archived.png' )
recent_thumb = os.path.join( settings.getAddonInfo( 'path' ), 'resources', 'media', 'recent.png' )
featured_thumb = os.path.join( settings.getAddonInfo( 'path' ), 'resources', 'media', 'featured.png' )
networks_thumb = os.path.join( settings.getAddonInfo( 'path' ), 'resources', 'media', 'networks.png' )
play_thumb = os.path.join( settings.getAddonInfo( 'path' ), 'resources', 'media', 'play.png' )
fanart_bg = os.path.join( settings.getAddonInfo( 'path' ), 'fanart.jpg' )
BASE = 'http://revision3.com/api/'
KEY = base64.b64decode(settings.getLocalizedString( 30025 ))

import CommonFunctions
common = CommonFunctions
common.plugin = plugin + ' ' + __version__

import SimpleDownloader as downloader
downloader = downloader.SimpleDownloader()

from addonfunc import addListItem, playListItem, getUrl, getPage, setViewMode, getParameters, retry

@retry((IndexError, TypeError, ValueError))
def build_main_directory(url):
	data = json.loads(getUrl(url))['shows']
	if settings.getSetting('folder') == 'true' and settings.getSetting( 'downloadPath' ) and url == BASE + 'getShows' + KEY:
		u = { 'mode': None, 'url': settings.getSetting( 'downloadPath' ) }
		infoLabels = { "Title": settings.getLocalizedString( 30012 ), "Plot": settings.getLocalizedString( 30022 ) }
		addListItem('[ ' + settings.getLocalizedString( 30012 ) + ' ]', downloads_thumb, u, True, 0, infoLabels, fanart_bg)
	if url == BASE + 'getShows' + KEY:
		#Featured
		u = { 'mode': '1', 'name': settings.getLocalizedString( 30023 ), 'url': BASE + 'getEpisodes' + KEY + '&grouping=featured', 'slug': 'None' }
		infoLabels = { "Title": settings.getLocalizedString( 30023 ), "Plot": settings.getLocalizedString( 30024 ) }
		addListItem('[ ' + settings.getLocalizedString( 30023 ) + ' ]', featured_thumb, u, True, 0, infoLabels, fanart_bg)
		#Most Recent
		u = { 'mode': '1', 'name': settings.getLocalizedString( 30013 ), 'url': BASE + 'getEpisodes' + KEY + '&grouping=latest', 'slug': 'None' }
		infoLabels = { "Title": settings.getLocalizedString( 30013 ), "Plot": settings.getLocalizedString( 30018 ) }
		addListItem('[ ' + settings.getLocalizedString( 30013 ) + ' ]', recent_thumb, u, True, 0, infoLabels, fanart_bg)
		#Networks
		u = { 'mode': '4' }
		infoLabels = { "Title": settings.getLocalizedString( 30027 ), "Plot": settings.getLocalizedString( 30028 ) }
		addListItem('[ ' + settings.getLocalizedString( 30027 ) + ' ]', networks_thumb, u, True, 0, infoLabels, fanart_bg)
		#Archived Shows
		u = { 'mode': '3', 'url': BASE + 'getShows' + KEY + '&grouping=archived' }
		infoLabels = { "Title": settings.getLocalizedString( 30014 ), "Plot": settings.getLocalizedString( 30019 ) }
		addListItem('[ ' + settings.getLocalizedString( 30014 ) + ' ]', archived_thumb, u, True, 0, infoLabels, fanart_bg)
	daily_data = {}
	for daily_show in data:
		if daily_show['parent_id'] != None:
			name = daily_show['name']
			thumb = daily_show['images']['logo'].replace('\\','')
			url = BASE + 'getEpisodes' + KEY + '&show_id=' + daily_show['id']
			daily_data[daily_show['parent_id']] = { 'name': name, 'url': url, 'plot': daily_show['summary'], 'thumb': thumb}
	totalItems = len(data) - len(daily_data)
	for show in data:
		if show['parent_id'] == None:
			if show['id'] in daily_data:
				daily_info = daily_data[show['id']]
			else:
				daily_info = 'None'
			slug = show['slug']
			if not settings.getSetting(slug):
				fanart = fanart_bg
			else:
				fanart = settings.getSetting(slug)
			name = show['name']
			#fanart = show['images']['hero'].replace('\\','')
			url = BASE + 'getEpisodes' + KEY + '&show_id=' + show['id']
			u = { 'mode': '1', 'name': name, 'url': url, 'slug': slug, 'daily_info': daily_info }
			infoLabels = { "Title": name, "Plot": show['summary'] }
			addListItem(name, show['images']['logo'].replace('\\',''), u, True, totalItems, infoLabels, fanart)
	xbmcplugin.addSortMethod( handle = int(sys.argv[ 1 ]), sortMethod = xbmcplugin.SORT_METHOD_UNSORTED )
	setViewMode("515")
	xbmcplugin.endOfDirectory(int(sys.argv[1]))

@retry((IndexError, TypeError, ValueError))
def build_sub_directory(url, name, slug, offset, daily_info):
	if slug == None:
		dialog = xbmcgui.Dialog()
		ok = dialog.ok( plugin , settings.getLocalizedString( 30029 ) )
		build_main_directory(BASE + 'getShows' + KEY)
		return
	saveurl = url
	data = json.loads(getUrl(url + '&offset=' + str(offset * 25)))
	if len(data['episodes']) == 0:
		dialog = xbmcgui.Dialog()
		ok = dialog.ok( plugin , settings.getLocalizedString( 30026 ) + ' ' + name + '.' )
		return
	if slug != 'None':
		try:
			downloads = 'http://revision3.com/' + slug + '/' + slug + '_downloads'
			fresult = getPage(downloads)['content']
			match = re.compile( '<a href="(.+?)" target="_blank">1920x1200</a>' ).findall(fresult)
			if len(match) > 1:
				fanart = match[1]
			else:
				fanart = match[0]
			settings.setSetting(slug, fanart)
		except:
			fanart = 'http://videos.revision3.com/revision3/images/shows/%s/%s_hero.jpg' % (slug, slug)
			if getPage(fanart)['error'] == 'HTTP Error 404: Not Found':
				fanart = fanart_bg
				settings.setSetting(slug, fanart)
			else:
				settings.setSetting(slug, fanart)
	else:
		fanart = fanart_bg
	if daily_info != 'None' and settings.getSetting('daily') == 'true':
		daily_info = ast.literal_eval(daily_info)
		u = { 'mode': '1', 'name': daily_info['name'], 'url': daily_info['url'], 'slug': slug, 'daily_info': 'None' }
		infoLabels = { "Title": daily_info['name'], "Plot": daily_info['plot'] }
		addListItem('[ ' + daily_info['name'] + ' ]', daily_info['thumb'], u, True, 0, infoLabels, fanart)
	if settings.getSetting('download') == '' or settings.getSetting('download') == 'false':
		if settings.getSetting('playall') == 'true':
			playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
			playlist.clear()
			u = { 'mode': '6' }
			infoLabels = { "Title": settings.getLocalizedString( 30030 ), "Plot": settings.getLocalizedString( 30031 ) }
			addListItem('* ' + settings.getLocalizedString( 30030 ) + ' *', play_thumb, u, True, 0, infoLabels, fanart)
	for episode in data['episodes']:
		studio = episode['show']['name']
		thumb = episode['images']['medium']
		url = episode['media']
		plot = episode['summary'].encode('ascii', 'ignore')
		name = episode['name'].encode('ascii', 'ignore')
		episodenum = episode['number']
		date = episode['published'].rsplit('T')[0]
		duration = int(episode['duration'])
		infoLabels = { "Title": name, "Studio": studio, "Plot": plot, "Episode": int(episodenum), "Aired": date }
		u = { 'mode': '2', 'name': name, 'url': url, 'plot': plot, 'studio': studio, 'episode': episodenum, 'thumb': thumb, 'date': date }
		addListItem(plot, thumb, u, False, len(data['episodes']), infoLabels, fanart, duration)
	if (int(data['total']) - ((offset + 1) * 25)) > 0:
		u = { 'mode': '1', 'name': studio, 'url': saveurl, 'slug': slug, 'offset': offset + 1, 'daily_info': 'None' }
		infoLabels = { "Title": settings.getLocalizedString( 30016 ), "Plot": settings.getLocalizedString( 30016 ) }
		addListItem(settings.getLocalizedString( 30016 ) + ' (' + str( offset + 2 ) + ')', next_thumb, u, True, 0, infoLabels, fanart)
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_UNSORTED )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_EPISODE )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_STUDIO )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_VIDEO_RUNTIME )
	setViewMode("503")
	xbmcplugin.endOfDirectory(int(sys.argv[1]))

@retry((IndexError, TypeError))	
def build_networks_directory():
	html = getUrl('http://revision3.com/networks')
	cards = common.parseDOM(html, "ul", attrs = { "class": "Cards show-grid" })
	item = common.parseDOM(cards, "li", attrs = { "class": "Grid2 Card item" })
	for network in item:
		image = common.parseDOM(network, "img", attrs = { "class": "thumbnail" }, ret="src")[0]
		url = common.parseDOM(network, "a", ret="href")[0]
		meta = common.parseDOM(network, "div", attrs = { "class": "meta" })
		name = common.parseDOM(meta, "strong")[0]
		plot = common.parseDOM(meta, "p")[0].rsplit('\n        ')[1]
		u = { 'mode': '5', 'url': url }
		infoLabels = { "Title": name, "Plot": plot }
		addListItem(name, image, u, True, len(item), infoLabels, fanart_bg)
	xbmcplugin.addSortMethod( handle = int(sys.argv[ 1 ]), sortMethod = xbmcplugin.SORT_METHOD_UNSORTED )
	setViewMode("515")
	xbmcplugin.endOfDirectory(int(sys.argv[1]))

@retry((IndexError, TypeError))	
def build_networks_sub_directory(url, offset):
	saveurl = url
	html = getUrl('http://revision3.com' + url + '/episodePage?limit=25&offset=' + str(offset * 25))
	networkItem = common.parseDOM(html, "li", attrs = { "class": "networkItem" })
	if len(networkItem) == 0:
		dialog = xbmcgui.Dialog()
		ok = dialog.ok( plugin , settings.getLocalizedString( 30026 ) + ' this page.' )
		return
	if settings.getSetting('download') == '' or settings.getSetting('download') == 'false':
		if settings.getSetting('playall') == 'true':
			playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
			playlist.clear()
			u = { 'mode': '6' }
			infoLabels = { "Title": settings.getLocalizedString( 30030 ), "Plot": settings.getLocalizedString( 30031 ) }
			addListItem('* ' + settings.getLocalizedString( 30030 ) + ' *', play_thumb, u, True, 0, infoLabels, fanart_bg)
	for item in networkItem:
		url = common.parseDOM(item, "a", attrs = { "class": "playlistPlay clear" }, ret = "href")[0][1:]
		thumbnail = common.parseDOM(item, "div", attrs = { "class": "thumbnail" })
		image = common.parseDOM(thumbnail, "img", ret = "src")[0].replace('small.thumb.jpg','medium.thumb.jpg')
		meta = common.parseDOM(item, "div", attrs = { "class": "meta" })
		name = common.parseDOM(meta, "div", attrs = { "class": "title" })[0]
		studio = common.parseDOM(meta, "div", attrs = { "class": "showtitle" })[0]
		plot = common.parseDOM(meta, "div", attrs = { "class": "itemPreview" })[0].encode('ascii', 'ignore')
		infoLabels = { "Title": name, "Studio": studio, "Plot": plot }
		u = { 'mode': '2', 'name': name, 'url': url, 'plot': plot, 'studio': studio, 'episode': '0', 'thumb': image, 'date': '0000-00-00' }
		addListItem(name, image, u, False, len(networkItem), infoLabels, fanart_bg)
	if len(networkItem) == 25:
		u = { 'mode': '5', 'url': saveurl, 'offset': offset + 1 }
		infoLabels = { "Title": settings.getLocalizedString( 30016 ), "Plot": settings.getLocalizedString( 30016 ) }
		addListItem(settings.getLocalizedString( 30016 ) + ' (' + str( offset + 2 ) + ')', next_thumb, u, True, 0, infoLabels, fanart_bg)
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_UNSORTED )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_EPISODE )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_STUDIO )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_VIDEO_RUNTIME )
	setViewMode("503")
	xbmcplugin.endOfDirectory(int(sys.argv[1]))
	
@retry((IndexError, TypeError))
def get_video(url, name, plot, studio, episode, thumb, date):
	if '{' in url:
		url = ast.literal_eval(url)
		try:
			path = url[settings.getSetting('format').lower().replace('hd','hd720p30').replace('high','large').replace('low','small')]['url']
		except:
			if 'hd' in url:
				path = url['hd']['url']
			elif 'large' in url:
				path = url['large']['url']
			elif 'small' in url:
				path = url['small']['url']
			else:
				path = url.items()[0][1]['url']
	else:
		oembed = getUrl('http://revision3.com/api/oembed/?url=http://revision3.com/%s/&format=json' % url)
		video_id = re.compile('html5player\-v(.+?)\?external').findall(oembed)[0]
		api = getUrl('http://revision3.com/api/flash?video_id=' + video_id)
		videos_api = common.parseDOM(api, "media", ret = "type")
		videos_api[:] = (value for value in videos_api if value != 'thumbnail')
		durl = {}
		for type_api in videos_api:
			content_api = clean(common.parseDOM(api, "media", attrs = { "type": type_api })[0])
			durl[type_api] = content_api
		try:
			path = durl[settings.getSetting('format').lower()]
		except:
			if 'high' in durl:
				path = durl['high']
			elif 'low' in durl:
				path = durl['low']
			else:
				path = str(durl.items()[0][1])
	if settings.getSetting('download') == 'true':
		while not settings.getSetting('downloadPath'):
			if settings.getSetting('download') == 'false':
				xbmc.executebuiltin("Container.Refresh")
				return
			dialog = xbmcgui.Dialog()
			ok = dialog.ok(plugin, settings.getLocalizedString( 30011 ))
			settings.openSettings()
		params = { "url": path, "download_path": settings.getSetting('downloadPath'), "Title": name }
		downloader.download(clean_file(name) + '.' + path.split('/')[-1].split('.')[-1], params)
	else:
		infoLabels = { "Title": name, "Studio": 'Revision3: ' + studio, "Plot": plot, "Episode": int(episode), "Aired": date  }
		playListItem(label = name, image = thumb, path = path, infoLabels = infoLabels, PlayPath = False)
		
def playall():
	playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
	xbmc.Player().play(playlist)
	return

def clean(name):
	remove = [('&amp;','&'), ('&quot;','"'), ('&#039;','\''), ('\r\n',' '), ('\n',' '), ('&apos;','\''), ('&#150;','-'), ('%3A',':'), ('%2F','/'), ('<link>',''), ('</link>','')]
	for trash, crap in remove:
		name = name.replace(trash,crap)
	return name
	
def clean_file(name):
    remove=[('\"',''),('\\',''),('/',''),(':',' - '),('|',''),('>',''),('<',''),('?',''),('*','')]
    for old, new in remove:
        name=name.replace(old,new)
    return name

params = getParameters(sys.argv[2])
url = None
name = None
mode = None
plot = None
studio = None
episode = None
thumb = None
date = None
slug = None
daily_info = 'None'
offset = 0

try:
	url = urllib.unquote_plus(params["url"])
except:
	pass
try:
	name = urllib.unquote_plus(params["name"])
except:
	pass
try:
	mode = int(params["mode"])
except:
	pass
try:
	plot = urllib.unquote_plus(params["plot"])
except:
	pass
try:
	studio = urllib.unquote_plus(params["studio"])
except:
	pass
try:
	episode = int(params["episode"])
except:
	pass
try:
	thumb = urllib.unquote_plus(params["thumb"])
except:
	pass
try:
	date = urllib.unquote_plus(params["date"])
except:
	pass
try:
	slug = urllib.unquote_plus(params["slug"])
except:
	pass
try:
	daily_info = urllib.unquote_plus(params["daily_info"])
except:
	pass
try:
	offset = int( params['offset'] )
except:
	pass

try:
	if mode == None:
		url = BASE + 'getShows' + KEY
		build_main_directory(url)
	elif mode == 1:
		build_sub_directory(url, name, slug, offset, daily_info)
	elif mode == 2:
		get_video(url, name, plot, studio, episode, thumb, date)
	elif mode == 3:
		build_main_directory(url)
	elif mode == 4:
		build_networks_directory()
	elif mode == 5:
		build_networks_sub_directory(url, offset)
	elif mode == 6:
		playall()
except Exception:
	buggalo.onExceptionRaised()
