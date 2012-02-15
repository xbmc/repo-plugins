
import xbmc, xbmcgui, xbmcplugin, urllib2, urllib, re, string, sys, os, traceback, xbmcaddon, xbmcvfs

plugin = "ESPN Video"
__author__ = 'stacked <stacked.xbmc@gmail.com>'
__url__ = 'http://code.google.com/p/plugin/'
__date__ = '02-14-2012'
__version__ = '1.0.0'
settings = xbmcaddon.Addon(id='plugin.video.espn.video')
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

def build_main_directory():
	main=[
		( settings.getLocalizedString( 30000 ), tvshows_thumb, 'menu2949050', '1' ),
		( settings.getLocalizedString( 30001 ), original_thumb, 'menu3385449', '1' ),
		( settings.getLocalizedString( 30002 ), categories_thumb, 'menu2949049', '1' ),
		( settings.getLocalizedString( 30005 ), search_thumb, 'search', '2' )
		]
	for name, thumbnailImage, url, mode in main:
		listitem = xbmcgui.ListItem( label = '[ ' + name + ' ]', iconImage = "DefaultVideo.png", thumbnailImage = thumbnailImage )
		u = sys.argv[0] + "?mode=" + mode + "&thumb=" + urllib.quote_plus( thumbnailImage ) + "&url=" + urllib.quote_plus( url ) + "&name=" + urllib.quote_plus( name )
		ok = xbmcplugin.addDirectoryItem( handle = int( sys.argv[1] ), url = u, listitem = listitem, isFolder = True )
	if settings.getSetting('presets_search') != '' and settings.getSetting('history') == 'true':
		listitem = xbmcgui.ListItem( label = '[ ' + settings.getLocalizedString( 30006 ) + ' ]', iconImage = "DefaultVideo.png", thumbnailImage = history_thumb )
		u = sys.argv[0] + "?mode=4"
		ok = xbmcplugin.addDirectoryItem( handle = int( sys.argv[1] ), url = u, listitem = listitem, isFolder = True )		
	build_video_directory('http://espn.go.com/video/format/libraryPlaylist?categoryid=2378529', 'The Latest', 'null')

def build_sub_directory(url, thumb):
	saveurl = url
	html = common.fetchPage({"link": "http://espn.go.com/video/"})["content"]
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
			listitem = xbmcgui.ListItem( label = name, iconImage = "DefaultFolder.png", thumbnailImage = tvshows_thumb )
			u = sys.argv[0] + "?mode=2" + "&name=" + urllib.quote_plus( settings.getLocalizedString( 30005 ) ) + "&url=" + urllib.quote_plus( url ) + "&type=" + urllib.quote_plus( 'history' )
			ok = xbmcplugin.addDirectoryItem( handle = int( sys.argv[1] ), url = u, listitem = listitem, isFolder = True )
	for name in title:
		name = name.rsplit('(')[0]
		url = 'http://espn.go.com/video/format/libraryPlaylist?categoryid=' + id[item_count].replace('channel','')
		listitem = xbmcgui.ListItem( label = name, iconImage = "DefaultFolder.png", thumbnailImage = thumb )
		u = sys.argv[0] + "?mode=2" + "&name=" + urllib.quote_plus( name ) + "&url=" + urllib.quote_plus( url ) + "&type=" + urllib.quote_plus( 'null' )
		ok = xbmcplugin.addDirectoryItem( handle = int( sys.argv[1] ), url = u, listitem = listitem, isFolder = True )
		item_count += 1	
	xbmcplugin.addSortMethod( handle = int(sys.argv[1]), sortMethod = xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( int( sys.argv[1] ) )

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
				save_str = presets + ' | ' + newStr
			settings.setSetting("presets_search", save_str)
		else:
			newStr = common.getParameters(url)["searchString"]
		url = 'http://search.espn.go.com/results?searchString=' + newStr + '&start=' + str(int(page) * 16) + '&dims=6'
		nexturl = url
		html = common.fetchPage({"link": url})["content"]
		results = common.parseDOM(html, "li", attrs = { "class": "result video-result" })
		title = common.parseDOM(results, "a", attrs = { "class": "launchVideoOverlay" })
		img = common.parseDOM(results, "a", attrs = { "class": "list-thumb launchVideoOverlay" })
		desc = common.parseDOM(results, "p")
		thumb = common.parseDOM(img, "img", ret = "src" )
		pagenum = common.parseDOM(html, "div", attrs = { "class": "page-numbers" })[0]
		maxlength = common.parseDOM(pagenum, "span")[1].replace('of ','')
		value = common.parseDOM(pagenum, "input", attrs = { "id": "page-number" }, ret = "value" )[0]
		pagecount = [ value, maxlength ]
		if len(title) == 0:
			dialog = xbmcgui.Dialog()
			ok = dialog.ok( plugin , settings.getLocalizedString( 30013 ) + '\n' + settings.getLocalizedString( 30014 ) )
			remove_menu(newStr,'search')
			return
	else:
		nexturl = url
		html = common.fetchPage({"link": url + "&pageNum=" + str(int(page)) + "&sortBy=&assetURL=http://assets.espn.go.com&module=LibraryPlaylist&pagename=vhub_index"})["content"]
		videocell = common.parseDOM(html, "div", attrs = { "class": "video-cell" })
		title = common.parseDOM(videocell, "h5")
		thumb = common.parseDOM(videocell, "img", ret = "src")
		desc = common.parseDOM(common.parseDOM(videocell, "p", attrs = { "class": "watch-now" }), "a", ret = "href")
		pagecount = common.parseDOM(html, "div", attrs = { "class": "page-numbers" })[0].rsplit(' of ')
	item_count = 0
	for name in title:
		plot = desc[item_count]
		data = thumb[item_count].replace('_thumdnail_wbig.jpg','').replace('.jpg','').rsplit('/')[-3:]
		url = data[0] + '/' + data[1] + '/' + data[2]
		thumbnailImage = thumb[item_count].replace('_thumdnail_wbig','')
		listitem = xbmcgui.ListItem( label = name, iconImage = "DefaultFolder.png", thumbnailImage = thumbnailImage )
		u = sys.argv[0] + "?mode=3" + "&name=" + urllib.quote_plus( name ) + "&url=" + urllib.quote_plus( url ) + "&thumb=" + urllib.quote_plus( thumbnailImage ) + "&plot=" + urllib.quote_plus( plot )
		ok = xbmcplugin.addDirectoryItem( handle = int( sys.argv[1] ), url = u, listitem = listitem, isFolder = False )
		item_count += 1
	if pagecount[0] != pagecount[1]:
		listitem = xbmcgui.ListItem(label = settings.getLocalizedString( 30003 ), iconImage = "DefaultVideo.png", thumbnailImage = next_thumb)
		u = sys.argv[0] + "?mode=2&name=" + urllib.quote_plus(nextname) + "&url=" + urllib.quote_plus(nexturl) + "&page=" + str(int(page) + 1) + "&type=" + urllib.quote_plus( 'null' )
		ok = xbmcplugin.addDirectoryItem( handle = int( sys.argv[1] ), url = u, listitem = listitem, isFolder = True )	
	xbmcplugin.addSortMethod( handle = int(sys.argv[1]), sortMethod = xbmcplugin.SORT_METHOD_NONE )
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
		listitem.addContextMenuItems( cm, replaceItems = False )
		u = sys.argv[0] + "?mode=2" + "&name=" + urllib.quote_plus( settings.getLocalizedString( 30005 ) ) + "&url=" + urllib.quote_plus( url ) + "&type=" + urllib.quote_plus( 'history' )
		ok = xbmcplugin.addDirectoryItem( handle = int( sys.argv[1] ), url = u, listitem = listitem, isFolder = True )	
	xbmcplugin.addSortMethod( handle = int(sys.argv[1]), sortMethod = xbmcplugin.SORT_METHOD_NONE )
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
	result = common.fetchPage({"link": "http://vod.espn.go.com/motion/" + url + ".smil?FLVPlaybackVersion=2.1"})
	if result["status"] != 200:
		dialog = xbmcgui.Dialog()
		ok = dialog.ok( plugin , settings.getLocalizedString( 30004 ) + ' (' + str(result["status"]) + ')' )
		return
	if plot.find('http://') != -1:
		html = common.fetchPage({"link": plot})["content"]
		plot = common.parseDOM(html, "meta", attrs = { "name": "description" }, ret = "content")[0].replace('ESPN Video: ', '')
	listitem = xbmcgui.ListItem(label = name , iconImage = thumb, thumbnailImage = thumb)
	listitem.setInfo( type = "Video", infoLabels={ "Title": name, "Studio": plugin, "Plot": plot } )
	playpath = "mp4:" + url + "_720p30_2896k.mp4"
	listitem.setProperty("PlayPath", playpath)
	xbmc.Player(xbmc.PLAYER_CORE_DVDPLAYER).play('rtmp://svod.espn.go.com/motion/', listitem)

params = common.getParameters(sys.argv[2])
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
	