
import xbmc, xbmcgui, xbmcplugin, xbmcaddon, urllib, re, string, sys, os, buggalo, time, datetime, _strptime

plugin = 'G4TV'
__author__ = 'stacked <stacked.xbmc@gmail.com>'
__url__ = 'http://code.google.com/p/plugin/'
__date__ = '06-09-2013'
__version__ = '3.0.2'
settings = xbmcaddon.Addon(id='plugin.video.g4tv')
buggalo.SUBMIT_URL = 'http://www.xbmc.byethost17.com/submit.php'
dbg = False
dbglevel = 3
next_thumb = os.path.join( settings.getAddonInfo( 'path' ), 'resources', 'media', 'next.png' )
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

from addonfunc import addListItem, playListItem, getUrl, getPage, setViewMode, getParameters, retry

def build_main_directory():
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
		u = { 'mode': mode, 'name': name, 'type': type, 'url': url }
		infoLabels = { "Title": name, "Plot": name }
		addListItem(label = name, image = thumbnailImage , url = u, isFolder = True, infoLabels = infoLabels)
	xbmcplugin.addSortMethod( handle = int(sys.argv[1]), sortMethod = xbmcplugin.SORT_METHOD_NONE )
	setViewMode("503")
	xbmcplugin.endOfDirectory( int( sys.argv[1] ) )

def build_sub_directory(name, type):
	html = getUrl('http://g4tv.com/videos/index.html')
	content = common.parseDOM(html, "div", attrs = { "id": "search_" + type })
	filter = common.parseDOM(content, "a", attrs = { "href": "#" })
	count = common.parseDOM(content, "span", attrs = { "class": "count" })
	for item_count in range(len(filter) - 1):
		name = filter[item_count]
		url = 'http://g4tv.com/videos/?sort=mostrecent&q=null&ajax=true&' + type + '=' + name.replace(' ', '+')
		u = { 'mode': '2', 'name': name, 'url': url }
		infoLabels = { "Title": name, "Plot": name }
		addListItem(label = name + ' ' + count[item_count + 1], image = eval(type), url = u, isFolder = True, infoLabels = infoLabels)
	xbmcplugin.addSortMethod( handle = int(sys.argv[ 1 ]), sortMethod = xbmcplugin.SORT_METHOD_UNSORTED )
	setViewMode("503")
	xbmcplugin.endOfDirectory( int( sys.argv[1] ) )

def build_video_directory(name, url):
	if name == settings.getLocalizedString( 30012 ):
		searchr = common.getUserInput(settings.getLocalizedString( 30001 ), "")
		if searchr == None:
			build_main_directory()
			return
		url = 'http://g4tv.com/videos/?sort=mostrecent&q='+ searchr.replace(' ','%20') +'&ajax=true'
	nexturl = url
	html = getUrl(url + '&page=' + str(page))
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
		build_main_directory()
		return
	for item_count in range(len(img)):
		if common.stripTags(info[item_count]).find('Views') == -1:
			length = common.stripTags(info[item_count]).rsplit('|')[1].replace(' ','').split(':')
		else:
			length = common.stripTags(info[item_count]).rsplit('|')[2].replace(' ','').split(':')
		duration = int(length[0]) * 60 + int(length[1])
		thumb = img[item_count].replace('138x78','256x256')
		plot = common.stripTags(clean(desc[item_count]))
		name = common.stripTags(clean(title[item_count]))
		try:
			posted = common.stripTags(info[item_count]).rsplit('|')[0].rsplit(':')[1].strip()
			if 'ago' in posted:
				days = int(posted.rsplit(' ')[0])
				aired = (datetime.date.today() - datetime.timedelta(days=days)).strftime('%d.%m.%Y')
			else:
				aired = datetime.datetime.fromtimestamp(time.mktime(time.strptime(posted, "%b %d, %Y"))).strftime('%d.%m.%Y')
			infoLabels = { "Title": name, "Plot": plot, "Aired": aired }
		except:
			infoLabels = { "Title": name, "Plot": plot }
		url = href[item_count]
		u = { 'mode': '3', 'name': name, 'url': url, 'plot': plot, 'thumb': thumb }
		addListItem(label = name, image = thumb, url = u, isFolder = False, infoLabels = infoLabels, fanart = False, duration = duration)
	if len(img) >= 15:
		u = { 'mode': '2', 'name': name, 'url': nexturl, 'page': str(int(page) + 1) }
		infoLabels = { "Title": settings.getLocalizedString( 30019 ), "Plot": settings.getLocalizedString( 30019 ) }
		addListItem(label = settings.getLocalizedString( 30019 ), image = next_thumb, url = u, isFolder = True, infoLabels = infoLabels)
	xbmcplugin.addSortMethod( handle = int(sys.argv[ 1 ]), sortMethod = xbmcplugin.SORT_METHOD_UNSORTED )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_VIDEO_RUNTIME )
	setViewMode("503")
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
	data = getUrl(url)
	url = clean(re.compile('&amp;r=(.+?)</FilePath>').findall(data)[0])
	infoLabels = { "Title": name, "Studio": plugin, "Plot": plot }
	playListItem(label = name, image = thumb, path = url, infoLabels = infoLabels)

params = getParameters(sys.argv[2])
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

try:
	if mode == None:
		build_main_directory()
	elif mode == 1:
		build_sub_directory(name, type)
	elif mode == 2:
		build_video_directory(name, url)
	elif mode == 3:
		play_video(name, url, plot, thumb)	
except Exception:
	buggalo.onExceptionRaised()