
import xbmc, xbmcaddon, xbmcvfs, xbmcgui, xbmcplugin, urllib2, urllib, re, string, sys, os, traceback, time
import simplejson as json

plugin = 'NBA Video'
__author__ = 'stacked <stacked.xbmc@gmail.com>'
__url__ = 'http://code.google.com/p/plugin/'
__date__ = '07-26-2012'
__version__ = '1.0.0'
settings = xbmcaddon.Addon( id = 'plugin.video.nba.video' )
dbg = False
dbglevel = 3
highlights_thumb = os.path.join( settings.getAddonInfo( 'path' ), 'resources', 'media', 'highlights.png' )
topplays_thumb = os.path.join( settings.getAddonInfo( 'path' ), 'resources', 'media', 'topplays.png' )
teams_thumb = os.path.join( settings.getAddonInfo( 'path' ), 'resources', 'media', 'teams.png' )
search_thumb = os.path.join( settings.getAddonInfo( 'path' ), 'resources', 'media', 'search.png' )
next_thumb = os.path.join( settings.getAddonInfo( 'path' ), 'resources', 'media', 'next.png' )

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
		listitem = xbmcgui.ListItem( label = '[ ' + name + ' ]', iconImage = thumbnailImage, thumbnailImage = thumbnailImage )
		u = sys.argv[0] + "?mode=" + mode + "&url=" + urllib.quote_plus( url )
		ok = xbmcplugin.addDirectoryItem( handle = int( sys.argv[1] ), url = u, listitem = listitem, isFolder = True )
	build_video_directory('channels%2F*%7Cgames%2F*%7Cflip_video_diaries%7Cfiba', 1)

def build_video_directory( url, page ):
	if url == 'search':
		text = common.getUserInput(settings.getLocalizedString( 30003 ), "")
		url = 'channels%2F*%7Cgames%2F*%7Cflip_video_diaries%7Cfiba&text=' + urllib.quote( text )
		print url
	save_url = url
	url = 'http://searchapp2.nba.com/nba-search/query.jsp?section=' + url + '&season=1112&sort=recent&site=nba&hide=true&type=advvideo&npp=15&start=' + str(1+(15*(page-1)))
	html = common.fetchPage({"link": url})['content']
	textarea = common.parseDOM(html, "textarea", attrs = { "id": "jsCode" })[0]
	data = json.loads(textarea.decode('latin1').encode('utf8'))['results'][0]
	if len(data) == 0:
		dialog = xbmcgui.Dialog()
		ok = dialog.ok( plugin , settings.getLocalizedString( 30004 ) + '\n' + settings.getLocalizedString( 30005 ) )
		return
	for results in data:
		date = results['mediaDateUts']
		title = results['title'].replace('\\','').encode('utf-8')
		thumb = results['metadata']['media']['thumbnail']['url'].replace('136x96','576x324')
		duration = results['metadata']['video']['length']
		plot = results['metadata']['media']['excerpt'].replace('\\','').encode('utf-8') + '\n\n' + time.ctime(float(date))
		url = results['id'].replace('/video/', '').replace('/index.html','')
		listitem = xbmcgui.ListItem( label = title, iconImage = thumb, thumbnailImage = thumb )
		listitem.setInfo( type="Video", infoLabels={ "Title": title, "Plot": plot, "Duration": duration } )
		u = sys.argv[0] + "?mode=3&name=" + urllib.quote_plus( title ) + "&url=" + urllib.quote_plus( url ) + "&thumb=" + urllib.quote_plus( thumb ) + "&plot=" + urllib.quote_plus( plot )
		ok = xbmcplugin.addDirectoryItem( handle = int( sys.argv[1] ), url = u, listitem = listitem, isFolder = False )
	listitem = xbmcgui.ListItem( label = '[Next Page (' + str( int( page ) + 1 ) + ')]' , iconImage = next_thumb, thumbnailImage = next_thumb )
	u = sys.argv[0] + "?mode=0" + "&page=" + str( int( page ) + 1 ) + "&url=" + urllib.quote_plus( save_url )
	ok = xbmcplugin.addDirectoryItem( handle = int( sys.argv[1] ), url = u, listitem = listitem, isFolder = True )
	xbmcplugin.addSortMethod( handle = int(sys.argv[1]), sortMethod = xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( int( sys.argv[1] ) )

def build_teams_directory():
	html = common.fetchPage({"link": "http://www.nba.com/video/"})['content']
	team_names = common.parseDOM(html, "a", attrs = { "id": "nbaVidSelectLk" })
	team_nicks = common.parseDOM(html, "a", attrs = { "id": "nbaVidSelectLk" }, ret="onclick")
	item_count = 0
	for title in team_names:
		nick = re.compile("\(\'teams/(.+?)\'").findall(team_nicks[item_count])[0]
		url = 'teams%2F' + nick + '%7Cgames%2F*%7Cchannels%2F*&team=' + title.replace(' ','%20')
		listitem = xbmcgui.ListItem( label = title, iconImage = teams_thumb, thumbnailImage = teams_thumb )
		u = sys.argv[0] + "?mode=0" + "&url=" + urllib.quote_plus( url )
		ok = xbmcplugin.addDirectoryItem( handle = int( sys.argv[1] ), url = u, listitem = listitem, isFolder = True )
		item_count += 1	
	xbmcplugin.addSortMethod( handle = int(sys.argv[1]), sortMethod = xbmcplugin.SORT_METHOD_LABEL )
	xbmcplugin.endOfDirectory( int( sys.argv[1] ) )		
	
def play_video( name, url, thumb, plot ):
	url = 'http://www.nba.com/video/' + url + '.xml'
	html = common.fetchPage({"link": url})['content']
	url = 'http://nba.cdn.turner.com/nba/big' + common.parseDOM(html, "file", attrs = { "type": "large" })[0]
	item = xbmcgui.ListItem( label = name, iconImage = "DefaultVideo.png", thumbnailImage = thumb )
	item.setInfo( type="Video", infoLabels={ "Title": name , "Studio": plugin, "Plot": plot } )
	xbmc.Player( xbmc.PLAYER_CORE_DVDPLAYER ).play( url, item )

def get_params():
	param = []
	paramstring = sys.argv[2]
	if len( paramstring ) >= 2:
		params = sys.argv[2]
		cleanedparams = params.replace( '?', '' )
		if ( params[len( params ) - 1] == '/' ):
			params = params[0:len( params ) - 2]
		pairsofparams = cleanedparams.split( '&' )
		param = {}
		for i in range( len( pairsofparams ) ):
			splitparams = {}
			splitparams = pairsofparams[i].split( '=' )
			if ( len( splitparams ) ) == 2:
				param[splitparams[0]] = splitparams[1]					
	return param

params = get_params()
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

if mode == None:
	build_main_directory()
elif mode == 0:
	build_video_directory( url, page )
elif mode == 1:
	build_teams_directory()
elif mode == 3:
	play_video( name, url, thumb, plot )
	