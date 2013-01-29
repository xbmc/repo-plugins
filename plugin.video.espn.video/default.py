
import xbmc, xbmcgui, xbmcplugin, xbmcaddon, urllib, re, string, sys, os, buggalo

plugin = "ESPN Video"
__author__ = 'stacked <stacked.xbmc@gmail.com>'
__url__ = 'http://code.google.com/p/plugin/'
__date__ = '01-27-2013'
__version__ = '2.0.4'
settings = xbmcaddon.Addon(id='plugin.video.espn.video')
buggalo.SUBMIT_URL = 'http://www.xbmc.byethost17.com/submit.php'
dbg = False
dbglevel = 3
next_thumb = os.path.join( settings.getAddonInfo( 'path' ), 'resources', 'media', 'next.png' )
tvshows_thumb = os.path.join( settings.getAddonInfo( 'path' ), 'resources', 'media', 'tvshows.png' )
original_thumb = os.path.join( settings.getAddonInfo( 'path' ), 'resources', 'media', 'original.png' )
categories_thumb = os.path.join( settings.getAddonInfo( 'path' ), 'resources', 'media', 'categories.png' )
search_thumb = os.path.join( settings.getAddonInfo( 'path' ), 'resources', 'media', 'search.png' )
history_thumb = os.path.join( settings.getAddonInfo( 'path' ), 'resources', 'media', 'history.png' )

import CommonFunctions
common = CommonFunctions
common.plugin = plugin + ' ' + __version__

from addonfunc import addListItem, playListItem, getUrl, getPage, setViewMode, getParameters, retry

@retry(IndexError)
def build_main_directory():
	main=[
		( settings.getLocalizedString( 30000 ), tvshows_thumb, 'menu2949050', '1' ),
		#( settings.getLocalizedString( 30001 ), original_thumb, 'menu3385449', '1' ),
		( settings.getLocalizedString( 30002 ), categories_thumb, 'menu2949049', '1' ),
		( settings.getLocalizedString( 30005 ), search_thumb, 'search', '2' )
		]
	for name, thumbnailImage, url, mode in main:
		u = { 'mode': mode, 'thumb': thumbnailImage, 'url': url, 'name': name }
		infoLabels = { "Title": name, "Plot": name }
		addListItem(label = '[ ' + name + ' ]', image = thumbnailImage, url = u, isFolder = True, infoLabels = infoLabels)
	if settings.getSetting('presets_search') != '' and settings.getSetting('history') == 'true':
		u = { 'mode': '4' }
		infoLabels = { "Title": settings.getLocalizedString( 30006 ), "Plot": settings.getLocalizedString( 30006 ) }
		addListItem(label = '[ ' + settings.getLocalizedString( 30006 ) + ' ]', image = history_thumb, url = u, isFolder = True, infoLabels = infoLabels)
	build_video_directory('http://espn.go.com/video/format/libraryPlaylist?categoryid=2378529', 'The Latest', 'null')
	setViewMode("503")

@retry(IndexError)
def build_sub_directory(url, thumb):
	saveurl = url
	html = getUrl('http://espn.go.com/video/')
	menu = common.parseDOM(html, "div", attrs = { "id": url })
	channel = common.parseDOM(menu, "li", attrs = { "class": "channel" })
	title = common.parseDOM(channel, "a")
	id = common.parseDOM(menu, "li", attrs = { "class": "channel" }, ret = "id")
	item_count = 0
	if saveurl == 'menu2949050':
		shows=[
			( settings.getLocalizedString( 30009 ), 'sportscenter' ),
			( settings.getLocalizedString( 30010 ), 'first%20take' ),
			( settings.getLocalizedString( 30011 ), 'pti' ),
			( settings.getLocalizedString( 30012 ), 'ath' )
			]	
		for name, search in shows:
			url = 'http://search.espn.go.com/results?searchString=' + search + '&start=0&dims=6'
			u = { 'mode': '2', 'name': settings.getLocalizedString( 30005 ), 'url': url, 'type': 'history' }
			infoLabels = { "Title": name, "Plot": name }
			addListItem(label = name, image = tvshows_thumb, url = u, isFolder = True, infoLabels = infoLabels)
	for name in title:
		name = name.rsplit('(')[0]
		url = 'http://espn.go.com/video/format/libraryPlaylist?categoryid=' + id[item_count].replace('channel','')
		u = { 'mode': '2', 'name': name, 'url': url, 'type': 'null' }
		infoLabels = { "Title": name, "Plot": name }
		addListItem(label = name, image = thumb, url = u, isFolder = True, infoLabels = infoLabels)
		item_count += 1	
	xbmcplugin.addSortMethod( handle = int(sys.argv[1]), sortMethod = xbmcplugin.SORT_METHOD_NONE )
	setViewMode("503")
	xbmcplugin.endOfDirectory( int( sys.argv[1] ) )

@retry(IndexError)
def build_video_directory(url, name, type):
	nextname = name
	if name == settings.getLocalizedString( 30005 ):
		if page == 0 and type != 'history':
			try:
				newStr = common.getUserInput(settings.getLocalizedString( 30005 ), '').replace(' ','%20')
			except:
				return
			presets = settings.getSetting( "presets_search" )
			if presets == '':
				save_str = newStr
			else:
				if presets.find(newStr + ' |') == -1:
					save_str = presets + ' | ' + newStr
				else:
					save_str = presets
			settings.setSetting("presets_search", save_str)
		else:
			newStr = getParameters(url)["searchString"]
		url = 'http://search.espn.go.com/results?searchString=' + newStr + '&start=' + str(int(page) * 16) + '&dims=6'
		nexturl = url
		html = getUrl(url).decode('ascii', 'ignore')
		results = common.parseDOM(html, "li", attrs = { "class": "result video-result" })
		titledata = common.parseDOM(results, "h3")
		title = common.parseDOM(titledata, "a", attrs = { "rel": "nofollow" })
		if len(title) == 0:
			dialog = xbmcgui.Dialog()
			ok = dialog.ok( plugin , settings.getLocalizedString( 30013 ) + '\n' + settings.getLocalizedString( 30014 ) )
			remove_menu(newStr,'search')
			return
		img = common.parseDOM(results, "a", attrs = { "class": "list-thumb" })
		desc = common.parseDOM(results, "p")
		thumb = common.parseDOM(img, "img", ret = "src" )
		pagenum = common.parseDOM(html, "div", attrs = { "class": "page-numbers" })[0]
		maxlength = common.parseDOM(pagenum, "span")[1].replace('of ','')
		value = common.parseDOM(pagenum, "input", attrs = { "id": "page-number" }, ret = "value" )[0]
		pagecount = [ value, maxlength ]
	else:
		nexturl = url
		html = getUrl(url + "&pageNum=" + str(int(page)) + "&sortBy=&assetURL=http://assets.espn.go.com&module=LibraryPlaylist&pagename=vhub_index")
		videocell = common.parseDOM(html, "div", attrs = { "class": "video-cell" })
		title = common.parseDOM(videocell, "h5")
		thumb = common.parseDOM(videocell, "img", ret = "src")
		desc = common.parseDOM(common.parseDOM(videocell, "p", attrs = { "class": "watch-now" }), "a", ret = "href")
		pagecount = common.parseDOM(html, "div", attrs = { "class": "page-numbers" })[0].rsplit(' of ')
	item_count = 0
	for name in title:
		if '/espn360/' not in thumb[item_count]:
			if 'http://' in desc[item_count]:
				plot = name
			else:
				plot = desc[item_count]
			try:
				data = thumb[item_count].replace('_thumdnail_wbig.jpg','').replace('.jpg','').rsplit('motion/')
				url = data[1]
			except:
				data = thumb[item_count].replace('_thumdnail_wbig.jpg','').replace('.jpg','').rsplit('/')[-4:]
				if len(data) >= 4:
					url = data[0] + '/' + data[1] + '/' + data[2] + '/' + data[3]
				else:
					url = 'null'
			thumbnailImage = thumb[item_count].replace('_thumdnail_wbig','')
			u = { 'mode': '3', 'name': name, 'url': url.replace('motion/',''), 'thumb': thumbnailImage, 'plot': plot }
			infoLabels = { "Title": name, "Plot": plot }
			addListItem(label = name, image = thumbnailImage, url = u, isFolder = False, infoLabels = infoLabels)
		item_count += 1
	if pagecount[0] != pagecount[1]:
		u = { 'mode': '2', 'name': nextname, 'url': nexturl, 'page': str(int(page) + 1), 'type': 'null' }
		infoLabels = { "Title": settings.getLocalizedString( 30003 ), "Plot": settings.getLocalizedString( 30003 ) }
		addListItem(label = settings.getLocalizedString( 30003 ), image = next_thumb, url = u, isFolder = True, infoLabels = infoLabels)
	xbmcplugin.addSortMethod( handle = int(sys.argv[1]), sortMethod = xbmcplugin.SORT_METHOD_NONE )
	setViewMode("503")
	xbmcplugin.endOfDirectory( int( sys.argv[1] ) )
	
def build_history_directory():
	presets = settings.getSetting( "presets_search" )
	if presets != '':
		save = presets.split( " | " )
	else:
		save = []
	cm = []
	for name in save:
		url = 'http://search.espn.go.com/results?searchString=' + name + '&start=0&dims=6'
		name = name.replace('%20', ' ')
		cm = [ ( 'Remove', "XBMC.RunPlugin(%s?mode=5&name=%s&url=%s)" % ( sys.argv[ 0 ], urllib.quote_plus(name), urllib.quote_plus('search') ), ) ]
		cm += [ ( 'Edit', "XBMC.RunPlugin(%s?mode=6&name=%s&url=%s)" % ( sys.argv[ 0 ], urllib.quote_plus(name), urllib.quote_plus('search') ), ) ]
		listitem = xbmcgui.ListItem( label = name, iconImage = "DefaultFolder.png", thumbnailImage = history_thumb )
		listitem.setInfo(type = 'video', infoLabels = { "Title": name, "Plot": name })
		listitem.addContextMenuItems( cm, replaceItems = False )
		u = sys.argv[0] + "?mode=2" + "&name=" + urllib.quote_plus( settings.getLocalizedString( 30005 ) ) + "&url=" + urllib.quote_plus( url ) + "&type=" + urllib.quote_plus( 'history' )
		ok = xbmcplugin.addDirectoryItem( handle = int( sys.argv[1] ), url = u, listitem = listitem, isFolder = True )	
	xbmcplugin.addSortMethod( handle = int(sys.argv[1]), sortMethod = xbmcplugin.SORT_METHOD_NONE )
	setViewMode("503")
	xbmcplugin.endOfDirectory( int( sys.argv[1] ) )
	
def remove_menu(name, url):
	presets = settings.getSetting( "presets_search" )
	save = presets.split( " | " )
	del save[save.index(name.replace(' ','%20'))]
	sets = ''
	x=0
	for item in save:
		if x == 0:
			sets = sets + item
		else:
			sets = sets + ' | ' + item
		x=x+1
	settings.setSetting("presets_search", sets)
	xbmc.executebuiltin( "Container.Refresh" )

def edit_menu(name, url):
	presets = settings.getSetting( "presets_search" )
	save = presets.split( " | " )
	del save[save.index(name.replace(' ','%20'))]
	x=0
	for item in save:
		if x == 0:
			sets = item
		else:
			sets = sets + ' | ' + item
		x=x+1
	newStr = common.getUserInput(settings.getLocalizedString( 30008 ), name).replace(' ','%20')
	if len(save) == 0:
		sets = newStr
	else:
		sets = sets + ' | ' + newStr
	settings.setSetting("presets_search", sets)
	xbmc.executebuiltin( "Container.Refresh" )

def play_video(url, name, thumb, plot):
	infoLabels = { "Title": name, "Studio": plugin, "Plot": plot }
	result = getPage("http://vod.espn.go.com/motion/" + url + ".smil?FLVPlaybackVersion=2.1")
	if '404' in str(result["error"]):
		dialog = xbmcgui.Dialog()
		ok = dialog.ok(plugin, settings.getLocalizedString( 30004 ))
		return
	else:
		playpath = "mp4:" + url + "_" + settings.getSetting("quality") + ".mp4"
		url = 'rtmp://svod.espn.go.com/motion/'
		playListItem(label = name, image = thumb, path = url, infoLabels = infoLabels, PlayPath = playpath)

params = getParameters(sys.argv[2])
mode = None
name = None
url = None
thumb = None
plot = None
page = 0
try:
	url=urllib.unquote_plus(params["url"])
except:
	pass
try:
	name=urllib.unquote_plus(params["name"])
except:
	pass
try:
	mode=int(params["mode"])
except:
	pass
try:
	page=int(params["page"])
except:
	pass
try:
	plot=urllib.unquote_plus(params["plot"])
except:
	pass
try:
	thumb = urllib.unquote_plus(params["thumb"])
except:
	pass
try:
	type = urllib.unquote_plus(params["type"])
except:
	pass

try:
	if mode == None:
		build_main_directory()
	elif mode == 1:
		build_sub_directory(url, thumb)
	elif mode == 2:
		build_video_directory(url, name, type)
	elif mode == 3:
		play_video(url, name, thumb, plot)
	elif mode == 4:
		build_history_directory()
	elif mode == 5:
		remove_menu(name, url)
	elif mode == 6:
		edit_menu(name, url)
except Exception:
	buggalo.onExceptionRaised()
	