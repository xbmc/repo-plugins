
import xbmc, xbmcaddon, xbmcgui, xbmcplugin, urllib2, urllib, re, string, sys, os, traceback, time, datetime, buggalo

__plugin__ = 'TMZ'
__author__ = 'stacked <stacked.xbmc@gmail.com>'
__url__ = 'http://code.google.com/p/plugin/'
__date__ = '09-11-2012'
__version__ = '2.0.4'
__settings__ = xbmcaddon.Addon( id = 'plugin.video.tmz' )
icon = os.path.join( __settings__.getAddonInfo( 'path' ), 'icon.png' )
buggalo.SUBMIT_URL = 'http://www.xbmc.byethost17.com/submit.php'

def open_url(url):
	req = urllib2.Request(url)
	req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:12.0) Gecko/20100101 Firefox/12.0')
	content = urllib2.urlopen(req)
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
		( __settings__.getLocalizedString( 30000 ) ),
		( __settings__.getLocalizedString( 30001 ) ),
		( __settings__.getLocalizedString( 30002 ) ),
		( __settings__.getLocalizedString( 30003 ) )
		]
	for name in main:
		listitem = xbmcgui.ListItem( label = name, iconImage = icon, thumbnailImage = icon )
		u = sys.argv[0] + "?mode=0&name=" + urllib.quote_plus( name )
		ok = xbmcplugin.addDirectoryItem( handle = int( sys.argv[1] ), url = u, listitem = listitem, isFolder = True )
	xbmcplugin.addSortMethod( handle = int(sys.argv[1]), sortMethod = xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( int( sys.argv[1] ) )

def build_video_directory( name ):
	data = open_url( 'http://www.tmz.com/videos/' )
	content = re.compile('{ name: \'' + name.upper() + '\',( )?\n         allInitialJson: \[(.+?)\],\n', re.DOTALL).findall( data )
	match = re.compile('\n{\n  (.+?)\n}', re.DOTALL).findall( content[0][1] )
	for videos in match:
		epsdata = re.compile('title": "(.+?)",\n  "duration": "(.+?)",\n  "url": "(.+?)",\n  "videoUrl": "(.+?)",\n  "manualThumbnailUrl": "(.+?)",\n  "thumbnailUrl": "(.+?)",\n  "kalturaId": "(.+?)"', re.DOTALL).findall(videos)
		title = clean(epsdata[0][0].replace("\\", ""))
		duration = epsdata[0][1].replace("\\", "")
		videoUrl = epsdata[0][3].replace("\\", "")
		thumb = epsdata[0][5].replace("\\", "") + '/width/490/height/266/type/3'
		if videoUrl.find('http://cdnbakmi.kaltura.com') == -1:
			if __settings__.getSetting("quality") == __settings__.getLocalizedString( 30005 ):
				url = 'http://cdnapi.kaltura.com/p/' + thumb.split('/')[4] + '/sp/' + thumb.split('/')[6] + '/playManifest/entryId/0_' + videoUrl.split('_')[1]
			else:
				url = 'http://cdnapi.kaltura.com/p/' + thumb.split('/')[4] + '/sp/' + thumb.split('/')[6] + '/playManifest/entryId/0_' + videoUrl.split('_')[1] + '/flavorId/0_' + videoUrl.split('_')[3]
			listitem = xbmcgui.ListItem( label = title, iconImage = thumb, thumbnailImage = thumb )
			listitem.setInfo( type="Video", infoLabels={ "Title": title, "Director": "TMZ", "Studio": name, "Duration": str(datetime.timedelta(seconds=int(duration))) } )
			listitem.setProperty('IsPlayable', 'true')
			u = sys.argv[0] + "?mode=1&name=" + urllib.quote_plus( title ) + "&url=" + urllib.quote_plus( url ) + "&thumb=" + urllib.quote_plus( thumb ) + "&studio=" + urllib.quote_plus( name )
			ok = xbmcplugin.addDirectoryItem( handle = int( sys.argv[1] ), url = u, listitem = listitem, isFolder = False )
	xbmcplugin.addSortMethod( handle = int(sys.argv[1]), sortMethod = xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( int( sys.argv[1] ) )
		
def play_video( name, url, thumb, studio ):
	data = open_url( url )
	url = re.compile('<media url=\"(.+?)\"').findall(data)[0]
	listitem = xbmcgui.ListItem( label = name, iconImage = "DefaultVideo.png", thumbnailImage = thumb, path = url )
	listitem.setInfo( type="Video", infoLabels={ "Title": name , "Director": "TMZ", "Studio": studio } )
	xbmcplugin.setResolvedUrl( handle = int( sys.argv[1] ), succeeded = True, listitem = listitem )

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

try:
	if mode == None:
		build_main_directory()
	elif mode == 0:
		build_video_directory( name )
	elif mode == 1:
		play_video( name, url, thumb, studio )
except Exception:
	buggalo.onExceptionRaised()
	