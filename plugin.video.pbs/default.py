
import xbmc, xbmcgui, xbmcplugin, urllib2, urllib, re, string, sys, os, traceback, time, xbmcaddon
from urllib2 import Request, urlopen, URLError, HTTPError

__plugin__ = "PBS"
__author__ = 'stacked <stacked.xbmc@gmail.com>'
__url__ = 'http://code.google.com/p/plugin/'
__date__ = '01-11-2011'
__version__ = '1.0.2'
__settings__ = xbmcaddon.Addon( id = 'plugin.video.pbs' )

programs_thumb = os.path.join( __settings__.getAddonInfo( 'path' ), 'resources', 'media', 'programs.png' )
topics_thumb = os.path.join( __settings__.getAddonInfo( 'path' ), 'resources', 'media', 'topics.png' )
collections_thumb = os.path.join( __settings__.getAddonInfo( 'path' ), 'resources', 'media', 'collections.png' )
search_thumb = os.path.join( __settings__.getAddonInfo( 'path' ), 'resources', 'media', 'search.png' )
next_thumb = os.path.join( __settings__.getAddonInfo( 'path' ), 'resources', 'media', 'next.png' )

def open_url( url ):
	retries = 0
	while retries < 3:
		try:
			req = urllib2.Request( url )
			content = urllib2.urlopen( req )
			data = content.read()
			content.close()
			return data
		except HTTPError,e:
			print 'PBS - Error code: ', e.code
			if e.code == 503:
				dialog = xbmcgui.Dialog()
				ok = dialog.ok( __plugin__ , 'HTTP Error 503. Please try again.' )
				return "data"
			if e.code == 404:
				dialog = xbmcgui.Dialog()
				ok = dialog.ok( __plugin__ , 'HTTP Error 404. Page not found.' )
				build_main_directory()
				return "data"
			retries += 1
			print 'PBS - Retries: ' + str( retries )
			continue
		else:
			break
	else:
		print 'PBS - Fetch of ' + url + ' failed after ' + str( retries ) + 'tries.'

def clean( string ):
	list = [( '&amp;', '&' ), ( '&quot;', '"' ), ( '&#39;', '\'' ), ( '\n',' ' ), ( '\r', ' '), ( '\t', ' '), ( '</p>', '' )]
	for search, replace in list:
		string = string.replace( search, replace )
	return string

def build_main_directory():
	main=[
		( __settings__.getLocalizedString( 30000 ), programs_thumb, '1' ),
		( __settings__.getLocalizedString( 30001 ), topics_thumb, '2' ),
		( __settings__.getLocalizedString( 30002 ), collections_thumb, '3' ),
		( __settings__.getLocalizedString( 30003 ), search_thumb, '4' )
		]
	for name, thumbnailImage, mode in main:
		listitem = xbmcgui.ListItem( label = name, iconImage = "DefaultVideo.png", thumbnailImage = thumbnailImage )
		u = sys.argv[0] + "?mode=" + mode
		ok = xbmcplugin.addDirectoryItem( handle = int( sys.argv[1] ), url = u, listitem = listitem, isFolder = True )
	xbmcplugin.addSortMethod( handle = int(sys.argv[1]), sortMethod = xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( int( sys.argv[1] ) )

def build_programs_directory():
	url = 'http://video.pbs.org/morevideos.html'
	data = open_url( url )
	content = re.compile( '<ul id="showslist">(.+?)<div id="more-pbs-footer"', re.DOTALL ).findall( data )[0]
	id_title = re.compile( '"http://video.pbs.org/program/(.+?)/" title="(.+?)" target="_self">(.+?)</a><br/>' ).findall( content )
	thumb = re.compile( '<img src="(.+?)" alt' ).findall( content )
	item_count = 0
	for id, title, trash in id_title:
		url = 'http://video.pbs.org/program/' + id + '/rss/'
		listitem = xbmcgui.ListItem( label = clean( title ), iconImage = thumb[item_count], thumbnailImage = thumb[item_count] )
		u = sys.argv[0] + "?mode=0&url=" + urllib.quote_plus( url )
		ok = xbmcplugin.addDirectoryItem( handle = int( sys.argv[1] ), url = u, listitem = listitem, isFolder = True )
		item_count += 1
	xbmcplugin.addSortMethod( handle = int(sys.argv[1]), sortMethod = xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( int( sys.argv[1] ) )
		
def build_topics_directory():
	url = 'http://video.pbs.org/'
	data = open_url( url )
	content = re.compile( '<li class="topics-nav">(.+?)<li class="collections-nav">', re.DOTALL ).findall( data )[0]
	id_title = re.compile( '<li><a href="http://video.pbs.org/subject/(.+?)/" title="(.+?)">' ).findall( content )
	item_count = 0
	for id, title in id_title:
		url = 'http://video.pbs.org/subject/' + id + '/rss/'
		listitem = xbmcgui.ListItem( label = clean( title ), iconImage = topics_thumb, thumbnailImage = topics_thumb )
		u = sys.argv[0] + "?mode=0&url=" + urllib.quote_plus( url )
		ok = xbmcplugin.addDirectoryItem( handle = int( sys.argv[1] ), url = u, listitem = listitem, isFolder = True )
		item_count += 1
	xbmcplugin.addSortMethod( handle = int(sys.argv[1]), sortMethod = xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( int( sys.argv[1] ) )

def build_collections_directory():
	url = 'http://video.pbs.org/'
	data = open_url( url )
	content = re.compile( '<li class="collections-nav">(.+?)<li class="divider-nav">', re.DOTALL ).findall( data )[0]
	id_title = re.compile( '<li><a href="http://video.pbs.org/feature/(.+?)/" title="(.+?)">' ).findall( content )
	item_count = 0
	for id, title in id_title:
		url = 'http://video.pbs.org/feature/' + id + '/rss/'
		listitem = xbmcgui.ListItem( label = clean( title ), iconImage = collections_thumb, thumbnailImage = collections_thumb )
		u = sys.argv[0] + "?mode=0&url=" + urllib.quote_plus( url )
		ok = xbmcplugin.addDirectoryItem( handle = int( sys.argv[1] ), url = u, listitem = listitem, isFolder = True )
		item_count += 1
	xbmcplugin.addSortMethod( handle = int(sys.argv[1]), sortMethod = xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( int( sys.argv[1] ) )

def build_search_keyboard():
	keyboard = xbmc.Keyboard( '', __settings__.getLocalizedString( 30003 ) )
	keyboard.doModal()
	if ( keyboard.isConfirmed() == False ):
		return
	search_string = keyboard.getText().replace( ' ', '+' )
	if len( search_string ) == 0:
		return
	url_1 = 'http://video.pbs.org/searchForm/?q=' + search_string
	url_2 = 'http://video.pbs.org/searchReleases/' + search_string
	build_search_directory( url_1 + '|' + url_2, page )

def build_search_directory( url, page ):
	save_url = url
	url_1 = url.rsplit( '|' )[0]
	url_2 = url.rsplit( '|' )[1]
	data = open_url( url_1 )
	video_data = open_url( url_2 + '/start/' + str( 1 + (int( page ) * 10) ) + '/end/' + str( ( int( page ) + 1 ) * 10 ) + '/' )
	try:
		content = re.compile( '<h2 class="result_title">Video Results</h2>(.+?)<div id="more-pbs-footer" class="clear clearfix">', re.DOTALL ).findall( data )[0]
	except:
		dialog = xbmcgui.Dialog()
		ok = dialog.ok( __plugin__ , __settings__.getLocalizedString( 30004 ) + '\n' + __settings__.getLocalizedString( 30005 ) )
		build_search_keyboard()
		return
	programs_id_title = re.compile( '<a href="http://(.+?)/program/(.+?)" class="program_title"><span class="program_name">(.+?)</span> <span class="visit_program">Visit Program Page</span></a>' ).findall( data )
	programs_info = re.compile( '<div class="program_description"> <p>(.+?)</div>' ).findall( data )
	video_count = re.compile( '<span class="resultnum">(.+?) Video Results</span>' ).findall( data )[0]
	id_title = re.compile( '<p class="info">(.*?)<a href="http://video.pbs.org/video/(.+?)/(\?starttime=(.*?))?" class="title" title="(.+?)">(.+?)</a>', re.DOTALL ).findall( video_data )
	info = re.compile( '<span class="list">(.*?)</span>', re.DOTALL ).findall( video_data )[0]
	thumb = re.compile('<img src="(.+?)" alt="(.+?)" />').findall( video_data )
	item_count = 0
	if len( programs_id_title ) > 0:
		for url, id, title in programs_id_title:
			url = 'http://' +url + '/program/' + id + '/rss/'
			listitem = xbmcgui.ListItem( label = '[Program] ' + clean( title ), iconImage = programs_thumb, thumbnailImage = programs_thumb )
			listitem.setInfo( type="Video", infoLabels={ "Title": 'Program: ' + clean( title ) , "Director": "PBS", "Studio": clean( title ), "Plot": clean( programs_info[item_count] ) } )
			u = sys.argv[0] + "?mode=0&url=" + urllib.quote_plus( url )
			ok = xbmcplugin.addDirectoryItem( handle = int( sys.argv[1] ), url = u, listitem = listitem, isFolder = True )
			item_count += 1	
	item_count = 0
	for trash1, id, trash2, trash3, trash4, title in id_title:
		url = 'http://video.pbs.org/xbmc/' + id
		studio = clean(title).rsplit(' | ',2)[0]
		name = clean(title).replace(studio+' | ','')
		listitem = xbmcgui.ListItem( label = name, iconImage = thumb[item_count][0], thumbnailImage = thumb[item_count][0] )
		listitem.setInfo( type="Video", infoLabels={ "Title": name , "Director": "PBS", "Studio": studio, "Plot": clean( info ) } )
		u = sys.argv[0] + "?mode=5&name=" + urllib.quote_plus( name ) + "&url=" + urllib.quote_plus( url ) + "&thumb=" + urllib.quote_plus( thumb[item_count][0] ) + "&plot=" + urllib.quote_plus( clean( info ) ) + "&studio=" + urllib.quote_plus( studio )
		ok = xbmcplugin.addDirectoryItem( handle = int( sys.argv[1] ), url = u, listitem = listitem, isFolder = False )
		item_count += 1
	if ( int( video_count ) - ( 10 * int( page ) ) ) > 10:
		listitem = xbmcgui.ListItem( label = '[Next Page (' + str( int( page ) + 2 ) + ')]' , iconImage = next_thumb, thumbnailImage = next_thumb )
		u = sys.argv[0] + "?mode=6" + "&page=" + str( int( page ) + 1 ) + "&url=" + urllib.quote_plus( save_url )
		ok = xbmcplugin.addDirectoryItem( handle = int( sys.argv[1] ), url = u, listitem = listitem, isFolder = True )
	xbmcplugin.addSortMethod( handle = int(sys.argv[1]), sortMethod = xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( int( sys.argv[1] ) )

def find_videos( url ):
	data = open_url( url )
	title_id_info = re.compile( '<item><title>(.+?)</title><link>http://(.+?)/video/(.+?)/</link><description>(.+?)</description>' ).findall( data )
	thumb = re.compile( '<media:thumbnail url="(.+?)" type' ).findall( data )
	item_count = 0
	for title, trash, id, info in title_id_info:
		url = 'http://video.pbs.org/xbmc/' + id
		studio = clean( title ).rsplit( ' | ', 2 )[0]
		name = clean( title ).replace( studio + ' | ', '' )
		listitem = xbmcgui.ListItem( label = name, iconImage = thumb[item_count], thumbnailImage = thumb[item_count] )
		listitem.setInfo( type="Video", infoLabels={ "Title": name, "Director": "PBS", "Studio": studio, "Plot": clean( info ) } )
		u = sys.argv[0] + "?mode=5&name=" + urllib.quote_plus( name ) + "&url=" + urllib.quote_plus( url ) + "&thumb=" + urllib.quote_plus( thumb[item_count] ) + "&plot=" + urllib.quote_plus( clean( info ) ) + "&studio=" + urllib.quote_plus( studio )
		ok = xbmcplugin.addDirectoryItem( handle = int( sys.argv[1] ), url = u, listitem = listitem, isFolder = False )
		item_count += 1
	xbmcplugin.addSortMethod( handle = int(sys.argv[1]), sortMethod = xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( int( sys.argv[1] ) )

def play_video( name, url, thumb, plot, studio ):
	data = open_url( url )
	id = re.compile( 'http%3A//release.theplatform.com/content.select%3Fpid%3D(.+?)%26UserName' ).findall( data )[0]
	url = 'http://release.theplatform.com/content.select?pid=' + id + '&format=SMIL'
	data = open_url( url )
	base = re.compile( '<meta base="(.+?)" />' ).findall( data )[0]
	src = re.compile( '<ref src="(.+?)" title="(.+?)" author' ).findall( data )[0][0]
	if base == 'http://ad.doubleclick.net/adx/':
		src_data = src.split( "&lt;break&gt;" )
		rtmp_url = src_data[0]
		playpath = "mp4:" + src_data[1]
	else:
		rtmp_url = base + src
		playpath = src
	item = xbmcgui.ListItem( label = name, iconImage = "DefaultVideo.png", thumbnailImage = thumb )
	item.setInfo( type="Video", infoLabels={ "Title": name , "Director": "PBS", "Studio": "PBS: " + studio, "Plot": plot } )
	xbmc.Player( xbmc.PLAYER_CORE_DVDPLAYER ).play( rtmp_url, item )

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
thumb = None
plot = None
studio = None
page = 0

try:
	url = urllib.unquote_plus( params["url"] )
except:
	pass
try:
	name = urllib.unquote_plus( params["name"] )
except:
	pass
try:
	mode = int( params["mode"] )
except:
	pass
try:
	page = int( params["page"] )
except:
	pass
try:
	thumb = urllib.unquote_plus( params["thumb"] )
except:
	pass
try:
	plot = urllib.unquote_plus( params["plot"] )
except:
	pass
try:
	studio = urllib.unquote_plus( params["studio"] )
except:
	pass

if mode == None:
	build_main_directory()
elif mode == 0:
	find_videos( url )
elif mode == 1:
	build_programs_directory()
elif mode == 2:
	build_topics_directory()
elif mode == 3:
	build_collections_directory()
elif mode == 4:	
	build_search_keyboard()
elif mode == 5:
	play_video( name, url, thumb, plot, studio )
elif mode == 6:
	build_search_directory( url, page )
