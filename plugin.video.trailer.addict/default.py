
import xbmc, xbmcgui, xbmcplugin, urllib2, urllib, re, string, sys, os, traceback, xbmcaddon

__plugin__ = 'Trailer Addict'
__author__ = 'stacked <stacked.xbmc@gmail.com>'
__url__ = 'http://code.google.com/p/plugin/'
__date__ = '01-04-2011'
__version__ = '1.0.4'
__settings__ = xbmcaddon.Addon( id = 'plugin.video.trailer.addict' )

next_thumb = os.path.join( __settings__.getAddonInfo( 'path' ), 'resources', 'media', 'next.png' )
search_thumb = os.path.join( __settings__.getAddonInfo( 'path' ), 'resources', 'media', 'search_icon.png' )
clapperboard_thumb = os.path.join( __settings__.getAddonInfo( 'path' ), 'resources', 'media', 'clapperboard.png' )
film_reel_thumb = os.path.join( __settings__.getAddonInfo( 'path' ), 'resources', 'media', 'film_reel.png' )
oscar_thumb = os.path.join( __settings__.getAddonInfo( 'path' ), 'resources', 'media', 'oscar.png' )
popcorn_thumb = os.path.join( __settings__.getAddonInfo( 'path' ), 'resources', 'media', 'popcorn.png' )

def open_url( url ):
	req = urllib2.Request( url )
	content = urllib2.urlopen( req )
	data = content.read()
	content.close()
	return data

def clean( name ):
	list = [ ( '&amp;', '&' ), ( '&quot;', '"' ), ( '<em>', '' ), ( '</em>', '' ), ( '&#39;', '\'' ) ]
	for search, replace in list:
		name = name.replace( search, replace )
	return name

def find_trailers( url, name ):
	save_name = name
	data = open_url( url )
	link_thumb = re.compile( '<a href="(.+?)"><img src="(.+?)" name="thumb' ).findall( data )
	thumbs = re.compile( 'img src="/psize\.php\?dir=(.+?)" style' ).findall( data )
	if len( thumbs ) == 0:
		thumb = "DefaultVideo.png"
	else:
		thumb = 'http://www.traileraddict.com/' + thumbs[0]
	title = re.compile( '<div class="abstract"><h2><a href="(.+?)">(.+?)</a></h2><br />', re.DOTALL ).findall( data )
	trailers = re.compile( '<dl class="dropdown">(.+?)</dl>', re.DOTALL ).findall( data )
	item_count = 0
	if len( trailers ) > 0:
		check1 = re.compile( '<a href="(.+?)"><img src="\/images\/usr\/arrow\.png" border="0" style="float:right;" \/>(.+?)</a>' ).findall( trailers[0] )
		check2 = re.compile( '<a href="(.+?)"( style="(.*?)")?>(.+?)<br />' ).findall( trailers[0] )
		if len( check1 ) > 0:
			url_title = check1
			for url, title in url_title:
				url = 'http://www.traileraddict.com' + url
				listitem = xbmcgui.ListItem( label = clean( title ), iconImage = thumb, thumbnailImage = thumb )
				u = sys.argv[0] + "?mode=5&name=" + urllib.quote_plus( save_name + ' (' + clean( title ) + ')' ) + "&url=" + urllib.quote_plus( url )
				ok = xbmcplugin.addDirectoryItem( handle = int( sys.argv[1] ), url = u, listitem = listitem, isFolder = False )
			xbmcplugin.addSortMethod( handle = int(sys.argv[1]), sortMethod = xbmcplugin.SORT_METHOD_NONE )
			xbmcplugin.endOfDirectory( int( sys.argv[1] ) )
		elif len( check2 ) > 0:
			url_title = check2
			for url, trash1, trash2, title in url_title:
				url = 'http://www.traileraddict.com' + url
				listitem = xbmcgui.ListItem( label = clean( title ), iconImage = thumb, thumbnailImage = thumb )
				u = sys.argv[0] + "?mode=5&name=" + urllib.quote_plus( save_name + ' (' + clean( title ) + ')' ) + "&url=" + urllib.quote_plus( url )
				ok = xbmcplugin.addDirectoryItem( handle = int( sys.argv[1] ), url = u, listitem = listitem, isFolder = False )
			xbmcplugin.addSortMethod( handle = int(sys.argv[1]), sortMethod = xbmcplugin.SORT_METHOD_NONE )
			xbmcplugin.endOfDirectory( int( sys.argv[1] ) )
		else:
			dia = xbmcgui.Dialog()
			ok = dia.ok( __settings__.getLocalizedString(30005), __settings__.getLocalizedString(30006) )
	else:
		for url, thumb2 in link_thumb:
			if clean( title[item_count][1] ).find( 'Trailer' ) > 0: 
				url = 'http://www.traileraddict.com' + url
				listitem = xbmcgui.ListItem( label = clean( title[item_count][1] ), iconImage = thumb, thumbnailImage = thumb )
				u = sys.argv[0] + "?mode=5&name=" + urllib.quote_plus( save_name + ' (' + clean( title[item_count][1] ) + ')' ) + "&url=" + urllib.quote_plus( url )
				ok = xbmcplugin.addDirectoryItem( handle = int( sys.argv[1] ),url = u, listitem = item, isFolder = False )
			item_count = item_count + 1
		xbmcplugin.addSortMethod( handle = int( sys.argv[1] ), sortMethod = xbmcplugin.SORT_METHOD_NONE )
		xbmcplugin.endOfDirectory( int( sys.argv[1] ) )

def build_main_directory():
	main=[
		( __settings__.getLocalizedString(30000), search_thumb, '0' ),
		( __settings__.getLocalizedString(30001), film_reel_thumb, '1' ),
		( __settings__.getLocalizedString(30002), clapperboard_thumb, '2' ),
		( __settings__.getLocalizedString(30003), oscar_thumb, '3' ),
		( __settings__.getLocalizedString(30004), popcorn_thumb, '6' )
		]
	for name, thumbnailImage, mode in main:
		listitem = xbmcgui.ListItem( label = name, iconImage = "DefaultVideo.png", thumbnailImage = thumbnailImage )
		u = sys.argv[0] + "?mode=" + mode + "&name="+urllib.quote_plus( name )
		ok = xbmcplugin.addDirectoryItem( handle = int( sys.argv[1] ), url = u, listitem = listitem, isFolder = True )
	data = open_url( 'http://www.traileraddict.com/' )
	url_thumb_x_title = re.compile( '<a href="/trailer/(.+?)"><img src="(.+?)" border="0" alt="(.+?)" title="(.+?)" style="margin:2px 10px 8px 10px;">' ).findall( data )
	for url, thumb, x, title in url_thumb_x_title:
		title = title.rsplit( ' - ' )
		name1 = clean( title[0] )
		if len( title ) > 1:
			name2 = clean( title[0] ) + ' (' + clean( title[1] ) + ')'
		else:
			name2 = clean( title[0] )
		url = 'http://www.traileraddict.com/trailer/' + url
		thumb = 'http://www.traileraddict.com' + thumb
		listitem = xbmcgui.ListItem( label = name1, iconImage = thumb, thumbnailImage = thumb )
		u = sys.argv[0] + "?mode=5&name=" + urllib.quote_plus( name2 ) + "&url=" + urllib.quote_plus( url )
		ok = xbmcplugin.addDirectoryItem( handle = int( sys.argv[1] ), url = u, listitem = listitem, isFolder = False )
	xbmcplugin.addSortMethod( handle = int(sys.argv[1]), sortMethod = xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( int( sys.argv[1] ) )
	
def build_search_directory():
	keyboard = xbmc.Keyboard( '', __settings__.getLocalizedString(30007) )
	keyboard.doModal()
	if ( keyboard.isConfirmed() == False ):
		return
	search_string = keyboard.getText().replace( ' ', '+' )
	if len( search_string ) == 0:
		return
	data = open_url( 'http://www.traileraddict.com/search.php?q=' + search_string )
	image = re.compile( '<center>\r\n<div style="background:url\((.*?)\);" class="searchthumb">', re.DOTALL ).findall( data )
	link_title = re.compile( '</div><a href="/tags/(.*?)">(.*?)</a><br />' ).findall( data )
	if len( link_title ) == 0:
		dialog = xbmcgui.Dialog()
		ok = dialog.ok( __plugin__ , __settings__.getLocalizedString(30009) + search_string + '.\n' + __settings__.getLocalizedString(30010) )
		build_main_directory()
		return
	item_count=0
	for url, title in link_title:
		url = 'http://www.traileraddict.com/tags/' + url
		thumb = 'http://www.traileraddict.com' + image[item_count].replace( '/pthumb.php?dir=', '' ).replace( '\r\n', '' )
		listitem = xbmcgui.ListItem( label = clean( title ), iconImage = thumb, thumbnailImage = thumb )
		u = sys.argv[0] + "?mode=4&name=" + urllib.quote_plus( clean( title ) ) + "&url=" + urllib.quote_plus( url )
		ok = xbmcplugin.addDirectoryItem( handle = int( sys.argv[1] ), url = u, listitem = listitem, isFolder = True )
		item_count = item_count + 1
	xbmcplugin.addSortMethod( handle = int( sys.argv[1] ), sortMethod = xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( int( sys.argv[1] ) )

def build_film_database_directory():
	keyboard = xbmc.Keyboard( '', __settings__.getLocalizedString(30011) )
	keyboard.doModal()
	if ( keyboard.isConfirmed() == False ):
		return
	search_string = keyboard.getText().replace( ' ', '+' )
	if len( search_string ) == 0:
		return
	data = open_url( 'http://www.traileraddict.com/thefilms/' + search_string )
	link_title = re.compile( '<img src="/images/arrow2.png" class="arrow"> <a href="(.+?)">(.+?)</a>' ).findall( data )
	item_count=0
	for url, title in link_title:
		url = 'http://www.traileraddict.com/' + url
		listitem = xbmcgui.ListItem( label = clean( title ), iconImage = "DefaultFolder.png", thumbnailImage = "DefaultFolder.png" )
		u = sys.argv[0] + "?mode=4&name=" + urllib.quote_plus( clean( title ) ) + "&url=" + urllib.quote_plus( url )
		ok = xbmcplugin.addDirectoryItem( handle = int( sys.argv[1] ), url = u, listitem = listitem, isFolder = True )
		item_count = item_count + 1
	xbmcplugin.addSortMethod( handle = int( sys.argv[1] ), sortMethod = xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( int( sys.argv[1] ) )

def build_coming_soon_directory():
	data = open_url( 'http://www.traileraddict.com/comingsoon' )
	margin_right = re.compile( '<div style=\"float:right(.*?)<div style="float:left; width:300px;', re.DOTALL ).findall( data )[0]
	margin_left = re.compile( '<div style=\"float:left; width:300px;(.*?)<div style="clear:both;">', re.DOTALL ).findall( data )[0]
	link_title = re.compile( '<img src="/images/arrow2.png" class="arrow"> <a href="(.+?)">(.+?)</a>' ).findall( margin_left )
	item_count = 0
	for url, title in link_title:
		url = 'http://www.traileraddict.com/' + url
		listitem = xbmcgui.ListItem( label = clean( title ), iconImage = "DefaultFolder.png", thumbnailImage = "DefaultFolder.png" )
		u = sys.argv[0] + "?mode=4&name=" + urllib.quote_plus( clean( title ) ) + "&url=" + urllib.quote_plus( url )
		ok = xbmcplugin.addDirectoryItem( handle = int( sys.argv[1] ), url = u, listitem = listitem, isFolder = True )
		item_count = item_count + 1
	link_title = re.compile( '<img src="/images/arrow2.png" class="arrow"> <a href="(.+?)">(.+?)</a>' ).findall( margin_right )
	item_count = 0
	for url, title in link_title:
		url = 'http://www.traileraddict.com/' + url
		listitem = xbmcgui.ListItem( label = clean( title ), iconImage = "DefaultFolder.png", thumbnailImage = "DefaultFolder.png" )
		u = sys.argv[0] + "?mode=4&name=" + urllib.quote_plus( clean( title ) ) + "&url=" + urllib.quote_plus( url )
		ok = xbmcplugin.addDirectoryItem( handle = int( sys.argv[1] ), url = u, listitem = listitem, isFolder = True )
		item_count = item_count + 1
	xbmcplugin.addSortMethod( handle = int( sys.argv[1] ), sortMethod = xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( int( sys.argv[1] ) )

def build_top_150_directory():
	data = open_url( 'http://www.traileraddict.com/top150' )
	link_title_views = re.compile( '<img src="/images/arrow2.png" class="arrow"> <a href="(.+?)">(.+?)</a> <span style="font-size:7pt;">(.+?)</span>' ).findall( data )
	item_count = 75
	for list in range( 0, 150 ):
		if item_count == 150:
			item_count = 0
		title = link_title_views[item_count][1] + ' ' + link_title_views[item_count][2]
		url = 'http://www.traileraddict.com/' + link_title_views[item_count][0]
		listitem = xbmcgui.ListItem( label = clean( title ), iconImage = "DefaultFolder.png", thumbnailImage = "DefaultFolder.png" )
		u = sys.argv[0] + "?mode=4&name=" + urllib.quote_plus( clean( title ) ) + "&url=" + urllib.quote_plus( url )
		ok = xbmcplugin.addDirectoryItem( handle = int( sys.argv[1] ), url = u, listitem = listitem, isFolder = True )
		item_count = item_count + 1
	xbmcplugin.addSortMethod( handle = int( sys.argv[1] ), sortMethod = xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( int( sys.argv[1] ) )

def build_featured_directory( page ):
	save_page = page
	data = open_url( 'http://www.traileraddict.com/attraction/' + str( int( page ) + 1) )
	url_thumb_x_title = re.compile( '<a href="/trailer/(.+?)"><img src="(.+?)" border="0" alt="(.+?)" title="(.+?)" style="margin:8px 5px 2px 5px;"></a>' ).findall( data )
	for url, thumb, x, title in url_thumb_x_title:
		title = title.rsplit( ' - ' )
		name1 = clean( title[0] )
		if len( title ) > 1:
			name2 = clean( title[0] ) + ' (' + clean( title[1] ) + ')'
		else:
			name2 = clean( title[0] )
		url = 'http://www.traileraddict.com/trailer/' + url
		thumb = 'http://www.traileraddict.com' + thumb
		listitem = xbmcgui.ListItem( label = name1, iconImage = thumb, thumbnailImage = thumb )
		u = sys.argv[0] + "?mode=5&name=" + urllib.quote_plus( name2 ) + "&url=" + urllib.quote_plus( url )
		ok = xbmcplugin.addDirectoryItem( handle = int( sys.argv[1] ), url = u, listitem = listitem, isFolder = False )
	listitem = xbmcgui.ListItem( label = '[ Next Page (' + str( int( save_page ) + 2 ) + ') ]' , iconImage = next_thumb, thumbnailImage = next_thumb )
	u = sys.argv[0] + "?mode=6" + "&page=" + str( int( save_page ) + 1 )
	ok = xbmcplugin.addDirectoryItem( handle = int( sys.argv[1] ), url = u, listitem = listitem, isFolder = True )
	xbmcplugin.addSortMethod( handle = int(sys.argv[1]), sortMethod = xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( int( sys.argv[1] ) )
	
def play_video( url, name ):
	data = open_url( url )
	url = re.compile( '<param name="movie" value="http://www.traileraddict.com/emb/(.+?)">' ).findall( data )[0]
	if data.find( 'black-tab-hd.png' ) > 0:
		url = 'http://www.traileraddict.com/fvarhd.php?tid=' + url
	else:
		url = 'http://www.traileraddict.com/fvar.php?tid=' + url
	data = open_url( url )
	url = re.compile( 'fileurl=(.+?)&vidwidth' ).findall( data )[0]
	thumb = re.compile( '&image=(.+?)' ).findall( data )[0]
	url = url.replace( '%3A', ':').replace( '%2F', '/' ).replace( '%3F', '?' ).replace( '%3D', '=' ).replace( '%26', '&' ).replace( '%2F', '//' )
	req = urllib2.Request( url )
	content = urllib2.urlopen( req )
	url = content.geturl()
	content.close()
	listitem = xbmcgui.ListItem( label = name, iconImage = "DefaultVideo.png", thumbnailImage = xbmc.getInfoImage( "ListItem.Thumb" ) )
	xbmc.Player( xbmc.PLAYER_CORE_DVDPLAYER ).play( str(url), listitem)

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
url = None
name = None
mode = None
page = 0

try:
	url = urllib.unquote_plus( params['url'] )
except:
	pass
try:
	name = urllib.unquote_plus( params['name'] )
except:
	pass
try:
	mode = int( params['mode'] )
except:
	pass
try:
        page = int( params['page'] )
except:
        pass

if mode == None:
	build_main_directory()
elif mode == 0:
	build_search_directory()
elif mode == 1:
	build_film_database_directory()
elif mode == 2:
	build_coming_soon_directory()
elif mode == 3:
	build_top_150_directory()
elif mode == 4:
	find_trailers( url, name )
elif mode == 5:
	play_video( url, name )
elif mode == 6:
	build_featured_directory( page )
