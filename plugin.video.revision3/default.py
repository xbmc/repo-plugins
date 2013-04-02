
import xbmc, xbmcgui, xbmcplugin, xbmcaddon, urllib, re, string, sys, os, time, buggalo, urllib2, base64
import simplejson as json

plugin =  'Revision3'
__author__ = 'stacked <stacked.xbmc@gmail.com>'
__url__ = 'http://code.google.com/p/plugin/'
__date__ = '04-01-2013'
__version__ = '2.0.13'
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
fanart_bg = os.path.join( settings.getAddonInfo( 'path' ), 'fanart.jpg' )
BASE = 'https://revision3.com/api/'
KEY = base64.b64decode(settings.getLocalizedString( 30025 ))

import CommonFunctions
common = CommonFunctions
common.plugin = plugin + ' ' + __version__

import SimpleDownloader as downloader
downloader = downloader.SimpleDownloader()

from addonfunc import addListItem, playListItem, getUrl, getPage, setViewMode, getParameters, retry

@retry((IndexError, TypeError))
def build_main_directory(url):
	data = json.loads(getUrl(url))['shows']
	if settings.getSetting('folder') == 'true' and settings.getSetting( 'downloadPath' ) and url == BASE + 'getShows' + KEY:
		u = { 'mode': None, 'url': settings.getSetting( 'downloadPath' ) }
		infoLabels = { "Title": settings.getLocalizedString( 30012 ), "Plot": settings.getLocalizedString( 30022 ) }
		addListItem('[ ' + settings.getLocalizedString( 30012 ) + ' ]', downloads_thumb, u, True, infoLabels, fanart_bg)
	if url == BASE + 'getShows' + KEY:
		#Featured
		u = { 'mode': '1', 'name': settings.getLocalizedString( 30023 ), 'url': BASE + 'getEpisodes' + KEY + '&grouping=featured', 'slug': 'None' }
		infoLabels = { "Title": settings.getLocalizedString( 30023 ), "Plot": settings.getLocalizedString( 30024 ) }
		addListItem('[ ' + settings.getLocalizedString( 30023 ) + ' ]', featured_thumb, u, True, infoLabels, fanart_bg)
		#Most Recent
		u = { 'mode': '1', 'name': settings.getLocalizedString( 30013 ), 'url': BASE + 'getEpisodes' + KEY + '&grouping=latest', 'slug': 'None' }
		infoLabels = { "Title": settings.getLocalizedString( 30013 ), "Plot": settings.getLocalizedString( 30018 ) }
		addListItem('[ ' + settings.getLocalizedString( 30013 ) + ' ]', recent_thumb, u, True, infoLabels, fanart_bg)
		#Networks
		u = { 'mode': '4' }
		infoLabels = { "Title": settings.getLocalizedString( 30027 ), "Plot": settings.getLocalizedString( 30028 ) }
		addListItem('[ ' + settings.getLocalizedString( 30027 ) + ' ]', networks_thumb, u, True, infoLabels, fanart_bg)
		#Archived Shows
		u = { 'mode': '3', 'url': BASE + 'getShows' + KEY + '&grouping=archived' }
		infoLabels = { "Title": settings.getLocalizedString( 30014 ), "Plot": settings.getLocalizedString( 30019 ) }
		addListItem('[ ' + settings.getLocalizedString( 30014 ) + ' ]', archived_thumb, u, True, infoLabels, fanart_bg)
	for show in data:
		slug = show['slug']
		if not settings.getSetting(slug):
			fanart = fanart_bg
		else:
			fanart = settings.getSetting(slug)
		name = show['name']
		#fanart = show['images']['hero'].replace('\\','')
		url = BASE + 'getEpisodes' + KEY + '&show_id=' + show['id']
		u = { 'mode': '1', 'name': name, 'url': url, 'slug': slug }
		infoLabels = { "Title": name, "Plot": show['summary'] }
		addListItem(name, show['images']['logo'].replace('\\',''), u, True, infoLabels, fanart)
	xbmcplugin.addSortMethod( handle = int(sys.argv[ 1 ]), sortMethod = xbmcplugin.SORT_METHOD_UNSORTED )
	setViewMode("515")
	xbmcplugin.endOfDirectory(int(sys.argv[1]))

@retry((IndexError, TypeError))
def build_sub_directory(url, name, slug, offset):
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
				settings.setSetting(slug, fanart_bg)
			else:
				settings.setSetting(slug, fanart)
	for episode in data['episodes']:
		studio = episode['show']['name']
		thumb = episode['images']['medium']
		url = episode['slug']
		if not settings.getSetting(episode['show']['slug']):
			fanart = fanart_bg
		else:
			fanart = settings.getSetting(episode['show']['slug'])
		plot = episode['summary'].encode('ascii', 'ignore')
		name = episode['name'].encode('ascii', 'ignore')
		episodenum = episode['number']
		date = episode['published'].rsplit('T')[0]
		duration = int(episode['duration'])
		infoLabels = { "Title": name, "Studio": studio, "Plot": plot, "Episode": int(episodenum), "Aired": date }
		u = { 'mode': '2', 'name': name, 'url': url, 'plot': plot, 'studio': studio, 'episode': episodenum, 'thumb': thumb, 'date': date }
		addListItem(plot, thumb, u, False, infoLabels, fanart, duration)
	if (int(data['total']) - ((offset + 1) * 25)) > 0:
		u = { 'mode': '1', 'name': studio, 'url': saveurl, 'slug': slug, 'offset': offset + 1 }
		infoLabels = { "Title": settings.getLocalizedString( 30016 ), "Plot": settings.getLocalizedString( 30016 ) }
		addListItem(settings.getLocalizedString( 30016 ) + ' (' + str( offset + 2 ) + ')', next_thumb, u, True, infoLabels, fanart_bg)
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
		addListItem(name, image, u, True, infoLabels, fanart_bg)
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
	for item in networkItem:
		url = common.parseDOM(item, "a", attrs = { "class": "playlistPlay clear" }, ret = "href")[0][1:]
		thumbnail = common.parseDOM(item, "div", attrs = { "class": "thumbnail" })
		image = common.parseDOM(thumbnail, "img", ret = "src")[0].replace('small.thumb.jpg','medium.thumb.jpg')
		meta = common.parseDOM(item, "div", attrs = { "class": "meta" })
		name = common.parseDOM(meta, "div", attrs = { "class": "title" })[0]
		studio = common.parseDOM(meta, "div", attrs = { "class": "showtitle" })[0]
		plot = common.parseDOM(meta, "div", attrs = { "class": "itemPreview" })[0]
		infoLabels = { "Title": name, "Studio": studio, "Plot": plot }
		u = { 'mode': '2', 'name': name, 'url': url, 'plot': plot, 'studio': studio, 'episode': '0', 'thumb': image, 'date': '0000-00-00' }
		addListItem(name, image, u, False, infoLabels, fanart_bg)
	if len(networkItem) == 25:
		u = { 'mode': '5', 'url': saveurl, 'offset': offset + 1 }
		infoLabels = { "Title": settings.getLocalizedString( 30016 ), "Plot": settings.getLocalizedString( 30016 ) }
		addListItem(settings.getLocalizedString( 30016 ) + ' (' + str( offset + 2 ) + ')', next_thumb, u, True, infoLabels, fanart_bg)
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_UNSORTED )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_EPISODE )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_STUDIO )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_VIDEO_RUNTIME )
	setViewMode("503")
	xbmcplugin.endOfDirectory(int(sys.argv[1]))
	
@retry((IndexError, TypeError))
def get_video(url, name, plot, studio, episode, thumb, date):
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
		url = durl[settings.getSetting('format').lower()]
	except:
		if 'high' in durl:
			url = durl['high']
		elif 'low' in durl:
			url = durl['low']
		else:
			url = str(durl.items()[0][1])
	if settings.getSetting('download') == 'true':
		while not settings.getSetting('downloadPath'):
			if settings.getSetting('download') == 'false':
				xbmc.executebuiltin("Container.Refresh")
				return
			dialog = xbmcgui.Dialog()
			ok = dialog.ok(plugin, settings.getLocalizedString( 30011 ))
			settings.openSettings()
		params = { "url": url, "download_path": settings.getSetting('downloadPath'), "Title": name }
		downloader.download(clean_file(name) + '.' + url.split('/')[-1].split('.')[-1], params)
	else:
		infoLabels = { "Title": name, "Studio": 'Revision3: ' + studio, "Plot": plot, "Episode": int(episode), "Aired": date  }
		playListItem(label = name, image = thumb, path = url, infoLabels = infoLabels, PlayPath = False)

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
	offset = int( params['offset'] )
except:
	pass

try:
	if mode == None:
		url = BASE + 'getShows' + KEY
		build_main_directory(url)
	elif mode == 1:
		build_sub_directory(url, name, slug, offset)
	elif mode == 2:
		get_video(url, name, plot, studio, episode, thumb, date)
	elif mode == 3:
		build_main_directory(url)
	elif mode == 4:
		build_networks_directory()
	elif mode == 5:
		build_networks_sub_directory(url, offset)
except Exception:
	buggalo.onExceptionRaised()
