
import xbmc, xbmcgui, xbmcplugin, urllib2, urllib, re, string, sys, os, traceback, xbmcaddon, xbmcvfs

plugin = 'G4TV'
__author__ = 'stacked <stacked.xbmc@gmail.com>'
__url__ = 'http://code.google.com/p/plugin/'
__date__ = '01-30-2012'
__version__ = '2.0.0'
settings = xbmcaddon.Addon(id='plugin.video.g4tv')
dbg = False
dbglevel = 3
next_thumb = os.path.join( settings.getAddonInfo( 'path' ), 'resources', 'media', 'next.png' )
downloads_thumb = os.path.join( settings.getAddonInfo( 'path' ), 'resources', 'media', 'downloads.png' )
search = os.path.join( settings.getAddonInfo( 'path' ), 'resources', 'media', 'search.png' )
showName = os.path.join( settings.getAddonInfo( 'path' ), 'resources', 'media', 'shows.png' )
recent = os.path.join( settings.getAddonInfo( 'path' ), 'resources', 'media', 'recent.png' )
subType = os.path.join( settings.getAddonInfo( 'path' ), 'resources', 'media', 'content.png' )
platform = os.path.join( settings.getAddonInfo( 'path' ), 'resources', 'media', 'platform.png' )
genre = os.path.join( settings.getAddonInfo( 'path' ), 'resources', 'media', 'genre.png' )
eventName = os.path.join( settings.getAddonInfo( 'path' ), 'resources', 'media', 'events.png' )

import CommonFunctions
common = CommonFunctions
common.plugin = plugin + ' ' + __version__

#import SimpleDownloader as downloader
#downloader = downloader.SimpleDownloader()

def open_url(url):
	print url
	retries = 0
	while retries < 3:
		try:
			req = urllib2.Request(url)
			req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-GB; rv:1.9.2.8) Gecko/20100722 Firefox/3.6.8')
			content=urllib2.urlopen(req)
			data=content.read()
			content.close()
			return data
		except:
			retries += 1
			print 'G4TV - Retries: ' + str(retries)
			continue
	else:
		print 'G4TV - Fetch of ' + url + ' failed after ' + str(retries) + 'tries.'
		return 'none'

def build_main_directory():
	if settings.getSetting('folder') == 'true' and settings.getSetting( 'downloadPath' ):
		url = settings.getSetting("downloadPath")
		listitem = xbmcgui.ListItem( label = settings.getLocalizedString( 30018 ), iconImage = downloads_thumb, thumbnailImage = downloads_thumb )
		ok = xbmcplugin.addDirectoryItem(handle = int(sys.argv[1]), url = url, listitem = listitem, isFolder = True)
	main=[
		( settings.getLocalizedString( 30011 ), recent, '2', 'recent' ),
		( settings.getLocalizedString( 30012 ), search, '2', 'search' ),
		( settings.getLocalizedString( 30013 ), showName, '1', 'showName' ),
		( settings.getLocalizedString( 30014 ), subType, '1', 'subType' ),
		( settings.getLocalizedString( 30015 ), eventName, '1', 'eventName' ),
		( settings.getLocalizedString( 30016 ), platform, '1', 'platform' ),
		( settings.getLocalizedString( 30017 ), genre, '1', 'genre' )
		]
	for name, thumbnailImage, mode, type in main:
		url = 'http://g4tv.com/videos/?sort=mostrecent&q=null&ajax=true'
		listitem = xbmcgui.ListItem( label = name, iconImage = "DefaultVideo.png", thumbnailImage = thumbnailImage )
		u = sys.argv[0] + "?mode=" + mode + "&name=" + urllib.quote_plus( name ) + "&type=" + urllib.quote_plus( type ) + "&url=" + urllib.quote_plus( url )
		ok = xbmcplugin.addDirectoryItem( handle = int( sys.argv[1] ), url = u, listitem = listitem, isFolder = True )
	xbmcplugin.addSortMethod( handle = int(sys.argv[1]), sortMethod = xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( int( sys.argv[1] ) )

def build_sub_directory(name, type):
	html = open_url('http://g4tv.com/videos/index.html')
	content = common.parseDOM(html, "div", attrs = { "id": "search_" + type })
	filter = common.parseDOM(content, "a", attrs = { "href": "#" })
	count = common.parseDOM(content, "span", attrs = { "class": "count" })
	for item_count in range(len(filter) - 1):
		name = filter[item_count]
		url = 'http://g4tv.com/videos/?sort=mostrecent&q=null&ajax=true&' + type + '=' + name.replace(' ', '+')
		listitem = xbmcgui.ListItem( label = name + ' ' + count[item_count + 1], iconImage = "DefaultFolder.png", thumbnailImage = eval(type) )
		u = sys.argv[0] + "?mode=2&name=" + urllib.quote_plus(name) + "&url=" + urllib.quote_plus(url)
		ok = xbmcplugin.addDirectoryItem( handle = int( sys.argv[1] ), url = u, listitem = listitem, isFolder = True )
	xbmcplugin.addSortMethod( handle = int(sys.argv[ 1 ]), sortMethod = xbmcplugin.SORT_METHOD_UNSORTED )
	xbmcplugin.endOfDirectory( int( sys.argv[1] ) )

def build_video_directory(name, url):
	if name == settings.getLocalizedString( 30012 ):
		searchr = common.getUserInput(settings.getLocalizedString( 30001 ), "").replace(' ','%20')
		url = 'http://g4tv.com/videos/?sort=mostrecent&q='+ searchr +'&ajax=true'
	nexturl = url
	html = open_url(url + '&page=' + str(page))
	wrap1 = common.parseDOM(html, "div", attrs = { "class": "li-wrap-1" })
	wrap2 = common.parseDOM(html, "div", attrs = { "class": "li-wrap-2" })
	desc = common.parseDOM(wrap1, "p", attrs = { "class": "desc" })
	info = common.parseDOM(wrap1, "p", attrs = { "class": "meta-info" })
	h4 = common.parseDOM(wrap1, "h4")
	title = common.parseDOM(h4, "a")
	href = common.parseDOM(h4, "a", ret = "href")
	img = common.parseDOM(wrap2, "img", ret = "src")
	if len(img) == 0:
		dialog = xbmcgui.Dialog()
		ok = dialog.ok( plugin , settings.getLocalizedString( 30002 ) + '\n' + settings.getLocalizedString( 30003 ) )
		return
	for item_count in range(len(img)):
		if common.stripTags(info[item_count]).find('Views') == -1:
			duration = common.stripTags(info[item_count]).rsplit('|')[1].replace(' ','')
		else:
			duration = common.stripTags(info[item_count]).rsplit('|')[2].replace(' ','')
		thumb = img[item_count].replace('138x78','256x256')
		plot = common.stripTags(clean(desc[item_count])) + '\n\n' + common.stripTags(info[item_count]).rsplit('|')[0]
		name = common.stripTags(clean(title[item_count]))
		url = href[item_count]
		listitem = xbmcgui.ListItem(label = name, iconImage = thumb, thumbnailImage = thumb)
		listitem.setInfo( type = "Video", infoLabels = { "Title": name, "Plot": plot, "Duration": duration } )
		u = sys.argv[0] + "?mode=3&name=" + urllib.quote_plus(name) + "&url=" + urllib.quote_plus(url) + "&plot=" + urllib.quote_plus(plot) + "&thumb=" + urllib.quote_plus(thumb)
		ok = xbmcplugin.addDirectoryItem(handle = int(sys.argv[1]), url = u, listitem = listitem, isFolder = False)
	if len(img) >= 15:
		listitem = xbmcgui.ListItem(label = settings.getLocalizedString( 30019 ), iconImage = "DefaultVideo.png", thumbnailImage = next_thumb)
		u = sys.argv[0] + "?mode=2&name=" + urllib.quote_plus(name) + "&url=" + urllib.quote_plus(nexturl) + "&page=" + str(int(page) + 1)
		ok = xbmcplugin.addDirectoryItem( handle = int( sys.argv[1] ), url = u, listitem = listitem, isFolder = True )
	xbmcplugin.addSortMethod( handle = int(sys.argv[ 1 ]), sortMethod = xbmcplugin.SORT_METHOD_UNSORTED )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_VIDEO_RUNTIME )
	xbmcplugin.endOfDirectory( int( sys.argv[1] ) )

def clean(name):
	remove = [('&amp;','&'), ('&quot;','"'), ('&#039;','\''), ('\r',''), ('&apos;','\''), ('&#150;','-'), ('%3a',':'), ('%2f','/'), ('\n','')]
	for trash, crap in remove:
		name = name.replace(trash,crap)
	return name
	
def clean_file(name):
    remove=[('\"',''),('\\',''),('/',''),(':',' - '),('|',''),('>',''),('<',''),('?',''),('*','')]
    for old, new in remove:
        name=name.replace(old,new)
    return name

def play_video(name, url, plot, thumb):
	videokey = re.compile('videos/(.+?)/(.+?)/').findall(url)
	url = 'http://g4tv.com/xml/broadbandplayerservice.asmx/GetEmbeddedHdVideo?videoKey='+videokey[0][0]+'&playLargeVideo=true&excludedVideoKeys=&playlistType=normal&maxPlaylistSize=0'
	data = open_url(url)
	url = clean(re.compile('&amp;r=(.+?)</FilePath>').findall(data)[0])
	if settings.getSetting('download') == 'true':
		while not settings.getSetting('downloadPath'):
			dialog = xbmcgui.Dialog()
			ok = dialog.ok(plugin, settings.getLocalizedString( 30020 ))
			settings.openSettings()
		params = { "url": url, "download_path": settings.getSetting('downloadPath'), "Title": name }
		downloader.download(clean_file(name) + '.' + url.split('/')[-1].split('.')[-1], params)
	else:
		listitem = xbmcgui.ListItem(label = name , iconImage = 'DefaultVideo.png', thumbnailImage = thumb)
		listitem.setInfo( type = "Video", infoLabels={ "Title": name, "Studio": plugin, "Plot": plot } )
		xbmc.Player(xbmc.PLAYER_CORE_DVDPLAYER).play(url, listitem)

params = common.getParameters(sys.argv[2])
mode = None
name = None
url = None
type = None
plot = None
thumb = None
page = 1

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
	page = int(params["page"])
except:
	pass
try:
	type = urllib.unquote_plus(params["type"])
except:
	pass
try:
	plot = urllib.unquote_plus(params["plot"])
except:
	pass
try:
	thumb = urllib.unquote_plus(params["thumb"])
except:
	pass

if mode == None:
	build_main_directory()
elif mode == 1:
	build_sub_directory(name, type)
elif mode == 2:
	build_video_directory(name, url)
elif mode == 3:
	play_video(name, url, plot, thumb)	
