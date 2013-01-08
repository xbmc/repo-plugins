
import xbmc, xbmcaddon, xbmcvfs, xbmcgui, xbmcplugin, urllib2, urllib, re, string, sys, os, traceback, time, buggalo, datetime, _strptime
import simplejson as json

plugin = 'NBA Video'
__author__ = 'stacked <stacked.xbmc@gmail.com>'
__url__ = 'http://code.google.com/p/plugin/'
__date__ = '01-06-2013'
__version__ = '2.0.3'
settings = xbmcaddon.Addon( id = 'plugin.video.nba.video' )
buggalo.SUBMIT_URL = 'http://www.xbmc.byethost17.com/submit.php'
dbg = False
dbglevel = 3
highlights_thumb = os.path.join( settings.getAddonInfo( 'path' ), 'resources', 'media', 'highlights.png' )
topplays_thumb = os.path.join( settings.getAddonInfo( 'path' ), 'resources', 'media', 'topplays.png' )
teams_thumb = os.path.join( settings.getAddonInfo( 'path' ), 'resources', 'media', 'teams.png' )
search_thumb = os.path.join( settings.getAddonInfo( 'path' ), 'resources', 'media', 'search.png' )
next_thumb = os.path.join( settings.getAddonInfo( 'path' ), 'resources', 'media', 'next.png' )
fanart = os.path.join( settings.getAddonInfo( 'path' ), 'fanart.jpg' )

import CommonFunctions
common = CommonFunctions
common.plugin = plugin + ' ' + __version__

from addonfunc import addListItem, playListItem, getUrl, getPage, setViewMode, getParameters, retry

@retry(IndexError)	
def build_main_directory():
	main=[
		( settings.getLocalizedString( 30000 ), highlights_thumb, 'games%2F*%7Cchannels%2Fplayoffs', '0', 'highlights' ),
		( settings.getLocalizedString( 30001 ), topplays_thumb, 'channels%2Ftop_plays', '0', 'top_plays' ),
		( settings.getLocalizedString( 30002 ), teams_thumb, 'null', '1', 'null' ),
		( settings.getLocalizedString( 30003 ), search_thumb, 'search', '0', 'null' )
		]
	for name, thumbnailImage, url, mode, section in main:
		u = { 'mode': mode, 'url': url, 'section': section }
		infoLabels = { "Title": name, "Plot": name }
		addListItem(label = '[ ' + name + ' ]', image = thumbnailImage, url = u, isFolder = True, infoLabels = infoLabels, fanart = fanart)
	build_video_directory('channels%2F*%7Cgames%2F*%7Cflip_video_diaries%7Cfiba', 1, 'all_videos')
	setViewMode("503")
	xbmcplugin.endOfDirectory( int( sys.argv[1] ) )

@retry(IndexError)
def build_video_directory( url, page, section ):
	if url == 'search':
		search = True
		text = common.getUserInput(settings.getLocalizedString( 30003 ), "")
		if text == None:
			return
		url = 'channels%2F*%7Cgames%2F*%7Cflip_video_diaries%7Cfiba&text=' + urllib.quote( text )
	else:
		search =  False
	save_url = url
	if page == 1 and search != True:
		base = 'http://www.nba.com/.element/ssi/auto/2.0/aps/video/playlists/' + section + '.html?section='
	else:
		base = 'http://searchapp2.nba.com/nba-search/query.jsp?section='
	url = base + url + '&season=1213&sort=recent&hide=true&type=advvideo&npp=15&start=' + str(1+(15*(page-1)))
	html = getUrl(url)
	textarea = common.parseDOM(html, "textarea", attrs = { "id": "jsCode" })[0]
	content = textarea.replace("\\'","\\\\'").replace('\\\\"','\\\\\\"').replace('\\n','').replace('\\t','').replace('\\x','')
	query = json.loads(content)
	data = query['results'][0]
	count = query['metaResults']['advvideo']
	if len(data) == 0:
		dialog = xbmcgui.Dialog()
		ok = dialog.ok( plugin , settings.getLocalizedString( 30004 ) + '\n' + settings.getLocalizedString( 30005 ) )
		return
	for results in data:
		mediaDateUts = time.ctime(float(results['mediaDateUts']))
		date = datetime.datetime.fromtimestamp(time.mktime(time.strptime(mediaDateUts, '%a %b %d %H:%M:%S %Y'))).strftime('%d.%m.%Y')
		title = results['title'].replace('\\','')
		thumb = results['metadata']['media']['thumbnail']['url'].replace('136x96','576x324')
		length = results['metadata']['video']['length'].split(':')
		duration = int(length[0]) * 60 + int(length[1])
		plot = results['metadata']['media']['excerpt'].replace('\\','')
		url = results['id'].replace('/video/', '').replace('/index.html','')
		infoLabels={ "Title": title, "Plot": plot, "Aired": date }
		u = { 'mode': '3', 'name': title, 'url': url, 'thumb': thumb, 'plot': plot }
		addListItem(label = title, image = thumb, url = u, isFolder = False, infoLabels = infoLabels, fanart = fanart, duration = duration)
	if int(page) * 15 < int(count):
		u = { 'mode': '0', 'page': str( int( page ) + 1 ), 'url': save_url, 'section': section }
		addListItem(label = '[Next Page (' + str( int( page ) + 1 ) + ')]', image = next_thumb, url = u, isFolder = True, infoLabels = False, fanart = fanart)
	xbmcplugin.addSortMethod( handle = int(sys.argv[1]), sortMethod = xbmcplugin.SORT_METHOD_NONE )
	setViewMode("503")
	xbmcplugin.endOfDirectory( int( sys.argv[1] ) )

@retry(IndexError)
def build_teams_directory():
	html = getUrl( 'http://www.nba.com/video/' )
	team_names = common.parseDOM(html, "a", attrs = { "id": "nbaVidSelectLk" })
	team_nicks = common.parseDOM(html, "a", attrs = { "id": "nbaVidSelectLk" }, ret="onclick")
	item_count = 0
	for title in team_names:
		nick = re.compile("\(\'teams/(.+?)\'").findall(team_nicks[item_count])[0]
		url = 'teams%2F' + nick + '%7Cgames%2F*%7Cchannels%2F*&team=' + title.replace(' ','%20') + '&site=nba%2C' + nick
		u = { 'mode': '0', 'url': url, 'section': nick + '_all' }
		addListItem(label = title, image = teams_thumb, url = u, isFolder = True, infoLabels = False, fanart = fanart)
		item_count += 1	
	xbmcplugin.addSortMethod( handle = int(sys.argv[1]), sortMethod = xbmcplugin.SORT_METHOD_LABEL )
	setViewMode("515")
	xbmcplugin.endOfDirectory( int( sys.argv[1] ) )		

@retry(IndexError)	
def play_video( name, url, thumb, plot ):
	url = 'http://www.nba.com/video/' + url + '.xml'
	html = getPage( url )
	if html['error'] == 'HTTP Error 404: Not Found':
		dialog = xbmcgui.Dialog()
		ok = dialog.ok( plugin , settings.getLocalizedString( 30006 ) )
		return
	url = 'http://nba.cdn.turner.com/nba/big' + common.parseDOM(html['content'], "file", attrs = { "type": "large" })[0]
	infoLabels = { "Title": name , "Studio": plugin, "Plot": plot }
	playListItem(label = name, image = thumb, path = url, infoLabels = infoLabels, PlayPath = False)

params = getParameters(sys.argv[2])
mode = None
name = None
url = None
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
		plot = urllib.unquote_plus(params["plot"])
except:
        pass
try:
		thumb = urllib.unquote_plus(params["thumb"])
except:
        pass
try:
		section = urllib.unquote_plus(params["section"])
except:
        pass
try:
        page = int(params["page"])
except:
        pass

try:
	if mode == None:
		build_main_directory()
	elif mode == 0:
		build_video_directory( url, page, section )
	elif mode == 1:
		build_teams_directory()
	elif mode == 3:
		play_video( name, url, thumb, plot )
except Exception:
	buggalo.onExceptionRaised()
	