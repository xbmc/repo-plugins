
import xbmc, xbmcgui, xbmcplugin, xbmcaddon, urllib, re, string, sys, os, time, buggalo, urllib2

plugin =  'Revision3'
__author__ = 'stacked <stacked.xbmc@gmail.com>'
__url__ = 'http://code.google.com/p/plugin/'
__date__ = '01-01-2013'
__version__ = '3.0.12'
settings = xbmcaddon.Addon(id='plugin.video.revision3')
buggalo.SUBMIT_URL = 'http://www.xbmc.byethost17.com/submit.php'
dbg = False
dbglevel = 3
next_thumb = os.path.join( settings.getAddonInfo( 'path' ), 'resources', 'media', 'next.png' )
more_thumb = os.path.join( settings.getAddonInfo( 'path' ), 'resources', 'media', 'more.png' )
downloads_thumb = os.path.join( settings.getAddonInfo( 'path' ), 'resources', 'media', 'downloads.png' )
old_thumb = os.path.join( settings.getAddonInfo( 'path' ), 'resources', 'media', 'old.png' )
current_thumb = os.path.join( settings.getAddonInfo( 'path' ), 'resources', 'media', 'current.png' )
search_thumb = os.path.join( settings.getAddonInfo( 'path' ), 'resources', 'media', 'search.png' )
fanart_bg = os.path.join( settings.getAddonInfo( 'path' ), 'fanart.jpg' )

import CommonFunctions
common = CommonFunctions
common.plugin = plugin + ' ' + __version__

import SimpleDownloader as downloader
downloader = downloader.SimpleDownloader()

from addonfunc import addListItem, playListItem, getUrl, getPage, setViewMode, getParameters, retry

@retry(IndexError)
def build_main_directory(url):
	path = url
	html = getUrl(url)
	shows = common.parseDOM(html, "ul", attrs = { "id": "shows" })[0]
	url_name = re.compile('<h3><a href="(.+?)">(.+?)</a></h3>').findall(shows)
	image = re.compile('class="thumbnail"><img src="(.+?)" /></a>').findall(shows)
	plot = common.parseDOM(shows, "p", attrs = { "class": "description" })
	if settings.getSetting('folder') == 'true' and settings.getSetting( 'downloadPath' ) and path == 'http://revision3.com/shows/':
		u = { 'mode': None, 'url': settings.getSetting("downloadPath") }
		infoLabels = { "Title": settings.getLocalizedString( 30012 ), "Plot": settings.getLocalizedString( 30022 ) }
		addListItem('[ ' + settings.getLocalizedString( 30012 ) + ' ]', downloads_thumb, u, True, infoLabels, fanart_bg)
	if path == 'http://revision3.com/shows/':
		u = { 'mode': '1', 'name': urllib.quote_plus(settings.getLocalizedString( 30013 )), 'url': urllib.quote_plus('http://revision3.com/episodes/page?&hideArrows=1&type=recent&page=1') }
		infoLabels = { "Title": settings.getLocalizedString( 30013 ), "Plot": settings.getLocalizedString( 30018 ) }
		addListItem('[ ' + settings.getLocalizedString( 30013 ) + ' ]', current_thumb, u, True, infoLabels, fanart_bg)
		u = { 'mode': '3', 'url': urllib.quote_plus('http://revision3.com/shows/archive') }
		infoLabels = { "Title": settings.getLocalizedString( 30014 ), "Plot": settings.getLocalizedString( 30019 ) }
		addListItem('[ ' + settings.getLocalizedString( 30014 ) + ' ]', old_thumb, u, True, infoLabels, fanart_bg)
		u = { 'mode': '4', 'url': urllib.quote_plus('search') }
		infoLabels = { "Title": settings.getLocalizedString( 30015 ), "Plot": settings.getLocalizedString( 30020 ) }
		addListItem('[ ' + settings.getLocalizedString( 30015 ) + ' ]', search_thumb, u, True, infoLabels, fanart_bg)
	count = 0
	for url, name in url_name:
		fanart = url.replace('/','')
		if not settings.getSetting(fanart):
			fanart = fanart_bg
		else:
			fanart = settings.getSetting(fanart)
		url = 'http://revision3.com' + url + '/episodes'
		u = { 'mode': '1', 'name': urllib.quote_plus(name), 'url': urllib.quote_plus(url) }
		infoLabels = { "Title": name, "Plot": clean(plot[count]) }
		addListItem(name, image[count].replace('160x160','200x200'), u, True, infoLabels, fanart)
		count += 1
	xbmcplugin.addSortMethod( handle = int(sys.argv[ 1 ]), sortMethod = xbmcplugin.SORT_METHOD_UNSORTED )
	setViewMode("515")
	xbmcplugin.endOfDirectory(int(sys.argv[1]))

@retry(IndexError)
def build_sub_directory(url, name):
	saveurl = url
	studio = name
	savestudio = name
	html = getUrl(url)
	ret = common.parseDOM(html, "div", attrs = { "id": "main-episodes" })
	pageLoad = common.parseDOM(ret, "a", ret = "onclick")
	if len(ret) == 0:
		ret = common.parseDOM(html, "div", attrs = { "id": "all-episodes" })
		pageLoad = common.parseDOM(ret, "a", ret = "onclick")
	if len(ret) == 0:
		ret = common.parseDOM(html, "ul", attrs = { "class": "episode-grid" })
		pageLoad = common.parseDOM(html, "a", ret = "onclick")
	current = common.parseDOM(html, "span", attrs = { "class": "active" })
	episodes = common.parseDOM(ret, "li", attrs = { "class": "episode item" })
	img = common.parseDOM(episodes[0], "img", ret = "src")[0]
	if settings.getLocalizedString( 30013 ) != name:
		try:
			downloads = 'http://revision3.com/' + img.rsplit('/')[6] + '/' + img.rsplit('/')[6] + '_downloads'
			fresult = getPage(downloads)['content']
			data = re.compile( '<a href="(.+?)" target="_blank">1920x1200</a>' ).findall(fresult)
			if len(data) > 1:
				fanart = data[1]
			else:
				fanart = data[0]
			settings.setSetting(img.rsplit('/')[6], fanart)
		except:
			fanart = 'http://statics.revision3.com/_/images/shows/' + img.rsplit('/')[6] + '/show_background.jpg'
			if getPage(fanart)['error'] == 'HTTP Error 404: Not Found':
				settings.setSetting(img.rsplit('/')[6], fanart_bg)
			else:
				settings.setSetting(img.rsplit('/')[6], fanart)		
	try:
		child = common.parseDOM(html, "div", attrs = { "id": "child-episodes" })
		label = common.parseDOM(html, "a", attrs = { "href": "#child-episodes" })[0]
		childshow = common.parseDOM(child, "a", attrs = { "class": "thumbnail" }, ret = "href" )[0].rsplit('/')[1]
		csaveurl = 'http://revision3.com/' + childshow + '/episodePage?type=recent&limit=15&hideShow=1&hideArrows=1&page=1'
		u = { 'mode': '1', 'name': urllib.quote_plus(studio), 'url': urllib.quote_plus(csaveurl) }
		infoLabels = { "Title": label, "Plot": label }
		addListItem('[ ' + label + ' ]', more_thumb, u, True, infoLabels, fanart)
	except:
		pass
	try:
		strs = 'http://revision3.com' + pageLoad[-1:][0].rsplit('\'')[1]
		params = getParameters(strs)
		saveurl = strs.rstrip('&page=' + params['page']) + '&page=' + str( int(current[0]) + 1 )
		if int(params['page']) > int(current[0]):
			next = True
		else:
			next = False
	except:
		next = False
	for data in episodes:
		thumb = common.parseDOM(data, "img", ret = "src")[0].replace('small.thumb','medium.thumb')
		show_id = thumb.split('/')[6]
		if not settings.getSetting(show_id):
			fanart = fanart_bg
		else:
			fanart = settings.getSetting(show_id)
		plot = clean(common.parseDOM(data, "img", ret = "alt")[0])
		name = clean(common.stripTags(common.parseDOM(data, "a")[1]))
		cut = common.parseDOM(data, "a")[1]
		try:
			studio = clean(common.parseDOM(cut, "strong")[0])
		except:
			pass
		name = name.replace(studio + '   ','')
		url = 'http://revision3.com' + common.parseDOM(data, "a", attrs = { "class": "thumbnail" }, ret = "href")[0]
		try:
			episode = name.rsplit(' ')[1]
			date = name.rsplit(' ')[3].rsplit('/')[2] + '-'  + name.rsplit(' ')[3].rsplit('/')[0] + '-' + name.rsplit(' ')[3].rsplit('/')[1]
		except:
			episode = '0'
			date = '0000-00-00'
		length = name[-6:].rstrip(')').replace('(','').split(':')
		duration = int(length[0]) * 60 + int(length[1])
		infoLabels = { "Title": plot, "Studio": studio, "Plot": plot, "Episode": int(episode), "Aired": date }
		u = { 'mode': '2', 'name': urllib.quote_plus(plot), 'url': urllib.quote_plus(url), 'plot': urllib.quote_plus(infoLabels['Plot'].encode('ascii', 'ignore')), 'studio': urllib.quote_plus(infoLabels['Studio']), 'episode': urllib.quote_plus(str(infoLabels['Episode'])), 'thumb': urllib.quote_plus(thumb), 'date': urllib.quote_plus(infoLabels['Aired']) }
		addListItem(plot, thumb, u, False, infoLabels, fanart, duration)
	if next == True:
		u = { 'mode': '1', 'name': urllib.quote_plus(savestudio), 'url': urllib.quote_plus(saveurl) }
		infoLabels = { "Title": settings.getLocalizedString( 30016 ), "Plot": settings.getLocalizedString( 30016 ) }
		addListItem(settings.getLocalizedString( 30016 ) + ' (' + str( int(current[0]) + 1 ) + ')', next_thumb, u, True, infoLabels, fanart_bg)
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_UNSORTED )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_EPISODE )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_STUDIO )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_VIDEO_RUNTIME )
	setViewMode("503")
	xbmcplugin.endOfDirectory(int(sys.argv[1]))
	
@retry((IndexError, TypeError))
def get_video(url, name, plot, studio, episode, thumb, date):
	result = getUrl(url)
	video_id = re.compile('player\.loadRevision3Item\(\'video_id\',(.+?)\);').findall(result)[0].replace(' ','')
	api = getUrl('http://revision3.com/api/flash?video_id=' + video_id)
	videos_api = common.parseDOM(api, "media", ret = "type")
	videos_api[:] = (value for value in videos_api if value != 'thumbnail')
	durl = {}
	for type_api in videos_api:
		content_api = clean(common.parseDOM(api, "media", attrs = { "type": type_api })[0])
		durl[type_api] = content_api
	list = ['MP4','Quicktime','Xvid','WMV','Unknown File Type']
	for type in list:
		content = common.parseDOM(result, "div", attrs = { "id": "action-panels-download-" + type })
		videos = common.parseDOM(content, "a", attrs = { "class": "sizename" })
		links = common.parseDOM(content, "a", attrs = { "class": "sizename" }, ret="href")
		count = 0
		for add in videos:
			if type == 'Unknown File Type':
				code = type
			else:
				code = type + ':' + add
			durl[code] = links[count]
			count += 1
	dictList = [] 
	for key, value in durl.iteritems():
		dictList.append(key)
	quality = settings.getSetting('type')
	try:
		try:
			purl = durl[quality]
		except:
			if quality == 'MP4:HD':
				if 'Quicktime:HD' in durl:
					quality_api = 'Quicktime:HD'
				else:
					quality_api = 'hd'
			if quality == 'MP4:Large':
				if 'Quicktime:Large' in durl:
					quality_api = 'Quicktime:Large'
				else:
					quality_api = 'high'
			if quality == 'MP4:Phone':
				quality_api = 'low'
			purl = durl[quality_api]
		ret = None
	except:
		dialog = xbmcgui.Dialog()
		ret = dialog.select(settings.getLocalizedString( 30017 ), dictList)
		purl = durl[dictList[ret]]
	if ret != -1:
		if settings.getSetting('download') == 'true':
			while not settings.getSetting('downloadPath'):
				if settings.getSetting('download') == 'false':
					xbmc.executebuiltin("Container.Refresh")
					return
				dialog = xbmcgui.Dialog()
				ok = dialog.ok(plugin, settings.getLocalizedString( 30011 ))
				settings.openSettings()
			params = { "url": purl, "download_path": settings.getSetting('downloadPath'), "Title": name }
			downloader.download(clean_file(name) + '.' + purl.split('/')[-1].split('.')[-1], params)
		else:
			infoLabels = { "Title": name, "Studio": 'Revision3: ' + studio, "Plot": plot, "Episode": int(episode), "Aired": date  }
			playListItem(label = name, image = thumb, path = purl, infoLabels = infoLabels, PlayPath = False)

@retry(IndexError)
def build_search_directory(url):
	if url == 'search':
		try:
			search = common.getUserInput("Enter search term", "").replace(' ','+')
			url = 'http://revision3.com/search/page?type=video&q=' + search + '&limit=10&page=1'
		except:
			return
	html = getUrl(url).encode('ascii', 'ignore')
	current = common.parseDOM(html, "span", attrs = { "class": "active" })
	pageLoad = common.parseDOM(html, "a", ret = "onclick")
	try:
		strs = 'http://revision3.com' + pageLoad[-1:][0].rsplit('\'')[1]
		params = getParameters(strs)
		saveurl = strs.rstrip('&page=' + params['page']) + '&page=' + str( int(current[0]) + 1 )
		if int(params['page']) > int(current[0]):
			next = True
		else:
			next = False
	except:
		next = False
	episodes = common.parseDOM(html, "li", attrs = { "class": "video" })
	if len(episodes) == 0:
		dialog = xbmcgui.Dialog()
		ok = dialog.ok( plugin , settings.getLocalizedString( 30009 ) + '\n' + settings.getLocalizedString( 30010 ) )
		return
	for data in episodes:
		thumb = common.parseDOM(data, "img", ret = "src")[0]
		url = common.parseDOM(data, "a", attrs = { "class": "thumbnail" }, ret = "href" )[0]
		url = clean(url.replace('http://www.videosurf.com/webui/inc/go.php?redirect=','')).replace('&client_id=revision3','')
		title = clean(common.parseDOM(data, "a", attrs = { "class": "title" })[0])
		plot = clean(common.stripTags(common.parseDOM(data, "div", attrs = { "class": "description" })[0]))
		try:
			studio = title.rsplit(' - ')[1]
		except:
			studio = 'Search'
		infoLabels = { "Title": title, "Studio": studio, "Plot": plot, "Episode": 0, "Aired": "0000-00-00" }
		u = { 'mode': '2', 'name': urllib.quote_plus(title), 'url': urllib.quote_plus(url), 'plot': urllib.quote_plus(infoLabels['Plot']), 'studio': urllib.quote_plus(infoLabels['Studio']), 'episode': urllib.quote_plus(str(infoLabels['Episode'])), 'thumb': urllib.quote_plus(thumb), 'date': urllib.quote_plus(infoLabels['Aired']) }
		addListItem(title, thumb, u, False, infoLabels, fanart_bg)
	if next == True:
		u = { 'mode': '4', 'url': urllib.quote_plus(saveurl), 'name': urllib.quote_plus(studio) }
		infoLabels = { "Title": settings.getLocalizedString( 30016 ), "Plot": settings.getLocalizedString( 30016 ) }
		addListItem(settings.getLocalizedString( 30016 ) + ' (' + str( int(current[0]) + 1 ) + ')', next_thumb, u, True, infoLabels, fanart_bg)
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_UNSORTED )
	setViewMode("503")
	xbmcplugin.endOfDirectory(int(sys.argv[1]))

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
	if mode == None:
		url = 'http://revision3.com/shows/'
		build_main_directory(url)
	elif mode == 1:
		build_sub_directory(url, name)
	elif mode == 2:
		get_video(url, name, plot, studio, episode, thumb, date)
	elif mode == 3:
		build_main_directory(url)
	elif mode == 4:
		build_search_directory(url)
except Exception:
	buggalo.onExceptionRaised()
