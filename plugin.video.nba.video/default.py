
import xbmc, xbmcaddon, xbmcvfs, xbmcgui, xbmcplugin, urllib2, urllib, re, string, sys, os, traceback, time, buggalo
from datetime import datetime
import simplejson as json

plugin = 'NBA Video'
__author__ = 'stacked <stacked.xbmc@gmail.com>'
__url__ = 'http://code.google.com/p/plugin/'
__date__ = '12-02-2012'
__version__ = '1.0.1'
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

def build_main_directory():
	main=[
		( settings.getLocalizedString( 30000 ), highlights_thumb, 'games%2F*%7Cchannels%2Fplayoffs', '0' ),
		( settings.getLocalizedString( 30001 ), topplays_thumb, 'channels%2Ftop_plays', '0' ),
		( settings.getLocalizedString( 30002 ), teams_thumb, 'null', '1' ),
		( settings.getLocalizedString( 30003 ), search_thumb, 'search', '0' )
		]
	for name, thumbnailImage, url, mode in main:
		u = { 'mode': mode, 'url': urllib.quote_plus( url ) }
		infoLabels = { "Title": name, "Plot": name }
		ListItem(label = '[ ' + name + ' ]', image = thumbnailImage, url = u, isFolder = True, infoLabels = infoLabels)
	build_video_directory('channels%2F*%7Cgames%2F*%7Cflip_video_diaries%7Cfiba', 1)
	xbmcplugin.setContent(int( sys.argv[1] ), 'episodes')
	setViewMode("503")
	xbmcplugin.endOfDirectory( int( sys.argv[1] ) )

def build_video_directory( url, page ):
	if url == 'search':
		text = common.getUserInput(settings.getLocalizedString( 30003 ), "")
		url = 'channels%2F*%7Cgames%2F*%7Cflip_video_diaries%7Cfiba&text=' + urllib.quote( text )
	save_url = url
	url = 'http://searchapp2.nba.com/nba-search/query.jsp?section=' + url + '&season=1213&sort=recent&hide=true&type=advvideo&npp=15&start=' + str(1+(15*(page-1)))
	html = open_url( url )
	textarea = common.parseDOM(html, "textarea", attrs = { "id": "jsCode" })[0]
	data = json.loads(textarea.decode('latin1').encode('utf8'))['results'][0]
	if len(data) == 0:
		dialog = xbmcgui.Dialog()
		ok = dialog.ok( plugin , settings.getLocalizedString( 30004 ) + '\n' + settings.getLocalizedString( 30005 ) )
		return
	for results in data:
		mediaDateUts = time.ctime(float(results['mediaDateUts']))
		date = datetime.fromtimestamp(time.mktime(time.strptime(mediaDateUts, '%a %b %d %H:%M:%S %Y'))).strftime('%d.%m.%Y')
		title = results['title'].replace('\\','').encode('utf-8')
		thumb = results['metadata']['media']['thumbnail']['url'].replace('136x96','576x324')
		duration = results['metadata']['video']['length']
		plot = results['metadata']['media']['excerpt'].replace('\\','').encode('utf-8')
		url = results['id'].replace('/video/', '').replace('/index.html','')
		infoLabels={ "Title": title, "Plot": plot, "Duration": duration, "Aired": date }
		u = { 'mode': '3', 'name': urllib.quote_plus( title ), 'url': urllib.quote_plus( url ), 'thumb': urllib.quote_plus( thumb ), 'plot': urllib.quote_plus( plot ) }
		ListItem(label = title, image = thumb, url = u, isFolder = False, infoLabels = infoLabels)
	u = { 'mode': '0', 'page': str( int( page ) + 1 ), 'url': urllib.quote_plus( save_url ) }
	ListItem(label = '[Next Page (' + str( int( page ) + 1 ) + ')]', image = next_thumb, url = u, isFolder = True, infoLabels = False)
	xbmcplugin.addSortMethod( handle = int(sys.argv[1]), sortMethod = xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.setContent(int( sys.argv[1] ), 'episodes')
	setViewMode("503")
	xbmcplugin.endOfDirectory( int( sys.argv[1] ) )

def build_teams_directory():
	html = open_url( 'http://www.nba.com/video/' )
	team_names = common.parseDOM(html, "a", attrs = { "id": "nbaVidSelectLk" })
	team_nicks = common.parseDOM(html, "a", attrs = { "id": "nbaVidSelectLk" }, ret="onclick")
	item_count = 0
	for title in team_names:
		nick = re.compile("\(\'teams/(.+?)\'").findall(team_nicks[item_count])[0]
		url = 'teams%2F' + nick + '%7Cgames%2F*%7Cchannels%2F*&team=' + title.replace(' ','%20') + '&site=nba%2C' + nick
		u = { 'mode': '0', 'url': urllib.quote_plus( url ) }
		ListItem(label = title, image = teams_thumb, url = u, isFolder = True, infoLabels = False)
		item_count += 1	
	xbmcplugin.addSortMethod( handle = int(sys.argv[1]), sortMethod = xbmcplugin.SORT_METHOD_LABEL )
	xbmcplugin.setContent(int( sys.argv[1] ), 'episodes')
	setViewMode("515")
	xbmcplugin.endOfDirectory( int( sys.argv[1] ) )		
	
def play_video( name, url, thumb, plot ):
	url = 'http://www.nba.com/video/' + url + '.xml'
	html = open_url( url )
	url = 'http://nba.cdn.turner.com/nba/big' + common.parseDOM(html, "file", attrs = { "type": "large" })[0]
	listitem = xbmcgui.ListItem( label = name, iconImage = "DefaultVideo.png", thumbnailImage = thumb, path = url )
	listitem.setInfo( type="Video", infoLabels={ "Title": name , "Studio": plugin, "Plot": plot } )
	xbmcplugin.setResolvedUrl( handle = int( sys.argv[1] ), succeeded = True, listitem = listitem )

def open_url( url ):
	retries = 0
	while retries < 11:
		data = {'content': None, 'error': None}
		try:
			if retries != 0:
				time.sleep(3)
			data = get_page(url)
			if data['content'] != None and data['error'] == None:
				return data['content']
			if data['error'] == 'HTTP Error 404: Not Found':
				break
		except Exception, e:
			data['error'] = str(e)
		retries += 1
	dialog = xbmcgui.Dialog()
	ret = dialog.yesno(plugin, settings.getLocalizedString( 30050 ), data['error'], '', settings.getLocalizedString( 30052 ), settings.getLocalizedString( 30053 ))
	if ret == False:
		open_url(url)
	else:
		ok = dialog.ok(plugin, settings.getLocalizedString( 30051 ))
		buggalo.addExtraData('url', url)
		buggalo.addExtraData('error', data['error'])
		raise Exception("open_url ERROR")
	
def get_page(url):
	data = {'content': None, 'error': None}
	try:
		req = urllib2.Request(url)
		req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:15.0) Gecko/20100101 Firefox/15.0.1')
		content = urllib2.urlopen(req)
		html = content.read()
		content.close()
		try:
			data['content'] = html.decode("utf-8")
			return data
		except:
			data['content'] = html
			return data
	except Exception, e:
		data['error'] = str(e)
		return data
		
def ListItem(label, image, url, isFolder, infoLabels = False):
	listitem = xbmcgui.ListItem(label = label, iconImage = image, thumbnailImage = image)
	listitem.setProperty('fanart_image', fanart)
	if infoLabels:
		listitem.setInfo( type = "Video", infoLabels = infoLabels )
	if not isFolder:
		listitem.setProperty('IsPlayable', 'true')
	u = sys.argv[0] + '?'
	for key, value in url.items():
		u = u + key + '=' + value + '&'
	ok = xbmcplugin.addDirectoryItem(handle = int(sys.argv[1]), url = u, listitem = listitem, isFolder = isFolder)
	return ok
	
def setViewMode(id):
	if xbmc.getSkinDir() == "skin.confluence":
		xbmc.executebuiltin("Container.SetViewMode(" + id + ")")

def getParameters(parameterString):
    commands = {}
    splitCommands = parameterString[parameterString.find('?') + 1:].split('&')
    for command in splitCommands:
        if (len(command) > 0):
            splitCommand = command.split('=')
            key = splitCommand[0]
            value = splitCommand[1]
            commands[key] = value
    return commands

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
        page = int(params["page"])
except:
        pass

try:
	if mode == None:
		build_main_directory()
	elif mode == 0:
		build_video_directory( url, page )
	elif mode == 1:
		build_teams_directory()
	elif mode == 3:
		play_video( name, url, thumb, plot )
except Exception:
	buggalo.onExceptionRaised()
	