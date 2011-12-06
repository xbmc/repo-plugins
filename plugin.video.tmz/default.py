
import xbmc, xbmcaddon, xbmcgui, xbmcplugin, urllib2, urllib, re, string, sys, os, traceback, time, datetime

__plugin__ = 'TMZ'
__author__ = 'stacked <stacked.xbmc@gmail.com>'
__url__ = 'http://code.google.com/p/plugin/'
__date__ = '12-05-2011'
__version__ = '2.0.0'
__settings__ = xbmcaddon.Addon( id = 'plugin.video.tmz' )

def open_url( url ):
	req = urllib2.Request( url )
	content = urllib2.urlopen( req )
	data = content.read()
	content.close()
	return data

def clean( name ):
	remove = [ ('&amp;','&'), ('&quot;','"'), ('&#39;','\''), ('u2013','-'), ('u201c','\"'), ('u201d','\"'), ('u2019','\''), ('u2026','...') ]
	for trash, crap in remove:
		name = name.replace( trash, crap )
	return name
	
def build_main_directory():
	main=[
		( __settings__.getLocalizedString( 30000 ), 'raw_thumb', 'raw_and_uncut' ),
		( __settings__.getLocalizedString( 30001 ), 'tv_thumb', 'tmz_tv' ),
		( __settings__.getLocalizedString( 30002 ), 'live_thumb', 'tmz_live' ),
		( __settings__.getLocalizedString( 30003 ), 'full_thumb', 'tmz_tv_full_episodes' )
		]
	for name, thumbnailImage, url in main:
		listitem = xbmcgui.ListItem( label = name, iconImage = "DefaultVideo.png", thumbnailImage = thumbnailImage )
		u = sys.argv[0] + "?mode=0&name=" + urllib.quote_plus( name ) + "&url=" + urllib.quote_plus( url )
		ok = xbmcplugin.addDirectoryItem( handle = int( sys.argv[1] ), url = u, listitem = listitem, isFolder = True )
	xbmcplugin.addSortMethod( handle = int(sys.argv[1]), sortMethod = xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( int( sys.argv[1] ) )

def build_video_directory( name, url ):
	data = open_url( 'http://www.tmz.com/videos/' )
	content = re.compile('playlistsData\.most_recent\.' + url + ' = \[(.+?)\];', re.DOTALL).findall( data )
	match = re.compile('\n{\n  (.+?)\n}', re.DOTALL).findall( content[0] )
	for videos in match:
		epsdata = re.compile('title: "(.+?)",\n  duration: parseInt\("(.+?)", 10\),\n  url: "(.+?)",\n  videoUrl: "(.+?)",\n  manualThumbnailUrl: "(.+?)",\n  thumbnailUrl: "(.+?)",\n  kalturaId: "(.+?)"', re.DOTALL).findall(videos)
		title = clean(epsdata[0][0].replace("\\", ""))
		duration = epsdata[0][1].replace("\\", "")
		url = epsdata[0][3].replace("\\", "")
		thumb = epsdata[0][5].replace("\\", "")
		if url.find('http://cdnbakmi.kaltura.com') == -1:
			listitem = xbmcgui.ListItem( label = title, iconImage = thumb, thumbnailImage = thumb )
			listitem.setInfo( type="Video", infoLabels={ "Title": title, "Director": "TMZ", "Studio": name, "Duration": str(datetime.timedelta(seconds=int(duration))) } )
			u = sys.argv[0] + "?mode=1&name=" + urllib.quote_plus( title ) + "&url=" + urllib.quote_plus( url ) + "&thumb=" + urllib.quote_plus( thumb ) + "&studio=" + urllib.quote_plus( name )
			ok = xbmcplugin.addDirectoryItem( handle = int( sys.argv[1] ), url = u, listitem = listitem, isFolder = False )
	xbmcplugin.addSortMethod( handle = int(sys.argv[1]), sortMethod = xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( int( sys.argv[1] ) )
		
def play_video( name, url, thumb, studio ):
	item = xbmcgui.ListItem( label = name, iconImage = "DefaultVideo.png", thumbnailImage = thumb )
	item.setInfo( type="Video", infoLabels={ "Title": name , "Director": "TMZ", "Studio": studio } )
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
studio = None
thumb = None

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
		studio = urllib.unquote_plus(params["studio"])
except:
        pass
try:
		thumb = urllib.unquote_plus(params["thumb"])
except:
        pass

if mode == None:
	build_main_directory()
elif mode == 0:
	build_video_directory( name, url )
elif mode == 1:
	play_video( name, url, thumb, studio )
	