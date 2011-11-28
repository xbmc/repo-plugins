
import xbmc, xbmcgui, xbmcplugin, urllib2, urllib, re, base64, string, sys, os, traceback, time, xbmcaddon, datetime, coveapi
from urllib2 import Request, urlopen, URLError, HTTPError 

__plugin__ = "PBS"
__author__ = 'stacked <stacked.xbmc@gmail.com>'
__url__ = 'http://code.google.com/p/plugin/'
__date__ = '11-28-2011'
__version__ = '2.0.0'
__settings__ = xbmcaddon.Addon( id = 'plugin.video.pbs' )

programs_thumb = os.path.join( __settings__.getAddonInfo( 'path' ), 'resources', 'media', 'programs.png' )
topics_thumb = os.path.join( __settings__.getAddonInfo( 'path' ), 'resources', 'media', 'topics.png' )
search_thumb = os.path.join( __settings__.getAddonInfo( 'path' ), 'resources', 'media', 'search.png' )
next_thumb = os.path.join( __settings__.getAddonInfo( 'path' ), 'resources', 'media', 'next.png' )
cove = coveapi.connect(base64.b64decode(__settings__.getLocalizedString( 30010 )), 
                       base64.b64decode(__settings__.getLocalizedString( 30011 )))
				
def open_url( url ):
	print 'PBS - URL: ' + url
	retries = 0
	while retries < 4:
		try:
			req = urllib2.Request( url )
			content = urllib2.urlopen( req )
			data = content.read()
			content.close()
			return data
		except HTTPError,e:
			print 'PBS - Error code: ', e.code
			if e.code == 404:
				dialog = xbmcgui.Dialog()
				ok = dialog.ok( __plugin__ , __settings__.getLocalizedString( 30006 ) + '\n' + __settings__.getLocalizedString( 30007 ) )
				build_main_directory()
				return "404"
			retries += 1
			print 'PBS - Retries: ' + str( retries )
			continue
		else:
			break
	else:
		print 'PBS - Fetch of ' + url + ' failed after ' + str( retries ) + ' tries.'
		build_main_directory()
		return "data"

def clean( string ):
	list = [( '&amp;', '&' ), ( '&quot;', '"' ), ( '&#39;', '\'' ), ( '\n','' ), ( '\r', ''), ( '\t', ''), ( '</p>', '' ), ( '<br />', ' ' ), ( '<b>', '' ), ( '</b>', '' ), ( '<p>', '' ), ( '<div>', '' ), ( '</div>', '' )]
	for search, replace in list:
		string = string.replace( search, replace )
	return string

def build_main_directory():
	main=[
		( __settings__.getLocalizedString( 30000 ), programs_thumb, '1' ),
		( __settings__.getLocalizedString( 30001 ), topics_thumb, '2' ),
		( __settings__.getLocalizedString( 30003 ), search_thumb, '4' )
		]
	for name, thumbnailImage, mode in main:
		listitem = xbmcgui.ListItem( label = name, iconImage = "DefaultVideo.png", thumbnailImage = thumbnailImage )
		u = sys.argv[0] + "?mode=" + mode
		ok = xbmcplugin.addDirectoryItem( handle = int( sys.argv[1] ), url = u, listitem = listitem, isFolder = True )
	xbmcplugin.addSortMethod( handle = int(sys.argv[1]), sortMethod = xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( int( sys.argv[1] ) )

def build_programs_directory():
	data = cove.programs.filter(fields='associated_images,mediafiles,categories',filter_categories__namespace__name='COVE Taxonomy',order_by='title')['results']
	for results in data:
		if len(results['associated_images']) >= 2:
			thumb = results['associated_images'][1]['url']
		else:
			thumb = programs_thumb
		program_id = re.compile( '/cove/v1/programs/(.*?)/' ).findall( results['resource_uri'] )[0]
		listitem = xbmcgui.ListItem( label = results['title'], iconImage = thumb, thumbnailImage = thumb )
		listitem.setInfo( type="Video", infoLabels={ "Title": results['title'], "Plot": results['long_description'] } )
		u = sys.argv[0] + '?mode=0&name=' + urllib.quote_plus( results['title'] ) + '&program_id=' + urllib.quote_plus( program_id )
		ok = xbmcplugin.addDirectoryItem( handle = int( sys.argv[1] ), url = u, listitem = listitem, isFolder = True )
	xbmcplugin.addSortMethod( handle = int(sys.argv[1]), sortMethod = xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( int( sys.argv[1] ) )
		
def build_topics_directory():
	data = cove.categories.filter(order_by='name',filter_namespace__name='COVE Taxonomy')['results']
	item = None
	for results in data:
		if item != results['name']:
			listitem = xbmcgui.ListItem( label = results['name'], iconImage = topics_thumb, thumbnailImage = topics_thumb )
			u = sys.argv[0] + "?mode=0&name=" + urllib.quote_plus( results['name'] ) + "&topic=" + urllib.quote_plus( 'True' )
			ok = xbmcplugin.addDirectoryItem( handle = int( sys.argv[1] ), url = u, listitem = listitem, isFolder = True )
			item = results['name']
	xbmcplugin.addSortMethod( handle = int(sys.argv[1]), sortMethod = xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( int( sys.argv[1] ) )

def build_search_keyboard():
	keyboard = xbmc.Keyboard( '', __settings__.getLocalizedString( 30003 ) )
	keyboard.doModal()
	if ( keyboard.isConfirmed() == False ):
		return
	search_string = keyboard.getText().replace( ' ', '%20' )
	if len( search_string ) == 0:
		return
	build_search_directory( search_string, page )

def build_search_directory( url, page ):
	save_url = url
	url = 'http://www.pbs.org/search/?q=' + url + '&mediatype=Video&start=' + str( page * 10 )
	data = open_url( url )
	title_id_thumb = re.compile('<a title="(.*?)" target="" rel="nofollow" onclick="EZDATA\.trackGaEvent\(\'search\', \'navigation\', \'external\'\);" href="(.*?)"><img src="(.*?)" class="ez-primaryThumb"').findall(data)
	program = re.compile('<p class="ez-metaextra1 ez-icon">(.*?)</p>').findall(data)
	plot = re.compile('<p class="ez-desc">(.*?)<div class="(ez-snippets|ez-itemUrl)">', re.DOTALL).findall(data)
	video_count = re.compile('<b class="ez-total">(.*?)</b>').findall(data)
	if len(title_id_thumb) == 0:
		dialog = xbmcgui.Dialog()
		ok = dialog.ok( __plugin__ , __settings__.getLocalizedString( 30004 ) + '\n' + __settings__.getLocalizedString( 30005 ) )
		return
	item_count = 0
	for title, id, thumb in title_id_thumb:
		listitem = xbmcgui.ListItem( label = clean ( title ), iconImage = thumb, thumbnailImage = thumb )
		listitem.setInfo( type="Video", infoLabels={ "Title": clean( title ) , "Director": "PBS", "Studio": clean( program[item_count] ), "Plot": clean( plot[item_count][0] ) } )
		u = sys.argv[0] + '?mode=0&name=' + urllib.quote_plus( clean( program[item_count] ) ) + '&program_id=' + urllib.quote_plus( id.rsplit('/')[4] ) + "&topic=" + urllib.quote_plus( 'False' )
		ok = xbmcplugin.addDirectoryItem( handle = int( sys.argv[1] ), url = u, listitem = listitem, isFolder = False )
		item_count += 1	
	if ( int( video_count[0] ) - ( 10 * int( page ) ) ) > 10:
		listitem = xbmcgui.ListItem( label = '[Next Page (' + str( int( page ) + 2 ) + ')]' , iconImage = next_thumb, thumbnailImage = next_thumb )
		u = sys.argv[0] + "?mode=6" + "&page=" + str( int( page ) + 1 ) + "&url=" + urllib.quote_plus( save_url )
		ok = xbmcplugin.addDirectoryItem( handle = int( sys.argv[1] ), url = u, listitem = listitem, isFolder = True )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_STUDIO )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_LABEL )
	xbmcplugin.endOfDirectory( int( sys.argv[1] ) )

def find_videos( name, program_id, topic, page ):
	start = str( 200 * page )
	if topic == 'True':
		program_id = 'program_id'
		data = cove.videos.filter(fields='associated_images,mediafiles,categories',filter_categories__name=name,filter_categories__namespace__name='COVE Taxonomy',order_by='-airdate',filter_type='Episode',filter_producer__name='PBS',filter_availability_status='Available',limit_start=start)['results']
	elif topic == 'False':
		data = cove.videos.filter(fields='associated_images,mediafiles',filter_tp_media_object_id=program_id,limit_start=start)['results']
		print "PBS - Video ID: " + program_id
		if len(data) == 0:
			dialog = xbmcgui.Dialog()
			ok = dialog.ok( __plugin__ , __settings__.getLocalizedString( 30009 ) + '\n' + 'http://video.pbs.org/video/' + program_id )
			return			
	else:
		topic = 'topic'
		data = cove.videos.filter(fields='associated_images,mediafiles',filter_program=program_id,order_by='-airdate',filter_availability_status='Available',limit_start=start,filter_type='Episode')['results']
	for results in data:
		if results['associated_images'] != None and len(results['associated_images']) > 0:
			thumb = results['associated_images'][0]['url']
		else:
			thumb = 'None'
		if results['mediafiles'][0]['video_data_url'] != None:
			url = results['mediafiles'][0]['video_data_url']
			mode = '5'
			if results['mediafiles'][0]['video_download_url'] != None:
				backup_url = results['mediafiles'][0]['video_download_url']
			else:
				backup_url = 'None'	
		else:
			url = results['mediafiles'][0]['video_download_url']
			mode = '7'
		if topic == 'False':
			play_video( results['title'], url, thumb, results['long_description'].encode('utf-8'), name, None, backup_url )
			return
		if results['mediafiles'][0]['length_mseconds'] != 0:
			listitem = xbmcgui.ListItem( label = results['title'].encode('utf-8'), iconImage = thumb, thumbnailImage = thumb )
			listitem.setInfo( type="Video", infoLabels={ "Title": results['title'].encode('utf-8'), "Director": "PBS", "Studio": name, "Plot": results['long_description'].encode('utf-8'), "Duration": str(datetime.timedelta(milliseconds=int(results['mediafiles'][0]['length_mseconds']))), "Aired": results['airdate'].rsplit(' ')[0] } )
			u = sys.argv[0] + "?mode=" + mode + "&name=" + urllib.quote_plus( results['title'].encode('utf-8') ) + "&url=" + urllib.quote_plus( url ) + "&thumb=" + urllib.quote_plus( thumb ) + "&plot=" + urllib.quote_plus( results['long_description'].encode('utf-8') ) + "&studio=" + urllib.quote_plus( name ) + "&backup_url=" + urllib.quote_plus( backup_url )
			ok = xbmcplugin.addDirectoryItem( handle = int( sys.argv[1] ), url = u, listitem = listitem, isFolder = False )
	if ( len(data) ) == 200:
		listitem = xbmcgui.ListItem( label = '[Next Page (' + str( int( page ) + 2 ) + ')]' , iconImage = next_thumb, thumbnailImage = next_thumb )
		u = sys.argv[0] + '?mode=0&name=' + urllib.quote_plus( name ) + '&program_id=' + urllib.quote_plus( program_id ) + "&topic=" + urllib.quote_plus( topic ) + "&page=" + str( int( page ) + 1 )
		ok = xbmcplugin.addDirectoryItem( handle = int( sys.argv[1] ), url = u, listitem = listitem, isFolder = True )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_UNSORTED )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_VIDEO_RUNTIME )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_LABEL )
	xbmcplugin.endOfDirectory( int( sys.argv[1] ) )

def play_video( name, url, thumb, plot, studio, starttime, backup_url ):
	data = open_url( url + '&format=SMIL' )
	print 'PBS - ' + studio + ' - ' + name
	try:
		print data
	except:
		pass
	try:
		base = re.compile( '<meta base="(.+?)" />' ).findall( data )[0]
	except:
		print 'PBS - Using backup_url'
		if backup_url != 'None':
			play_mp4( name, backup_url, thumb, plot, studio, starttime )
			return
		else:
			dialog = xbmcgui.Dialog()
			ok = dialog.ok( __plugin__ , __settings__.getLocalizedString( 30008 ) )
			return
	src = re.compile( '<ref src="(.+?)" title="(.+?)" author' ).findall( data )[0][0]
	playpath = None
	if base == 'http://ad.doubleclick.net/adx/':
		src_data = src.split( "&lt;break&gt;" )
		rtmp_url = src_data[0] + "mp4:" + src_data[1].replace('mp4:','')
	elif base == 'http://www-tc.pbs.org/cove-media/':
		play_mp4( name, base+src.replace('mp4:',''), thumb, plot, studio, starttime )
		return
	else:
		rtmp_url = base
		playpath = "mp4:" + src.replace('mp4:','')
	item = xbmcgui.ListItem( label = name, iconImage = "DefaultVideo.png", thumbnailImage = thumb )
	item.setInfo( type="Video", infoLabels={ "Title": name , "Director": "PBS", "Studio": "PBS: " + studio, "Plot": plot } )
	if playpath != None:
		item.setProperty("PlayPath", playpath)
	xbmc.Player( xbmc.PLAYER_CORE_DVDPLAYER ).play( clean( rtmp_url ), item )
	if starttime != None:
		while( 1 ):
			if xbmc.Player().isPlayingVideo():
				xbmc.sleep( 50 )
				xbmc.Player( xbmc.PLAYER_CORE_DVDPLAYER ).seekTime( int( starttime ) / 1000 )
				break

def play_mp4( name, url, thumb, plot, studio, starttime ):
	item = xbmcgui.ListItem( label = name, iconImage = "DefaultVideo.png", thumbnailImage = thumb )
	item.setInfo( type="Video", infoLabels={ "Title": name , "Director": "PBS", "Studio": "PBS: " + studio, "Plot": plot } )
	xbmc.Player( xbmc.PLAYER_CORE_DVDPLAYER ).play( clean( url ), item )
	if starttime != None:
		while( 1 ):
			if xbmc.Player().isPlayingVideo():
				xbmc.sleep( 50 )
				xbmc.Player( xbmc.PLAYER_CORE_DVDPLAYER ).seekTime( int( starttime ) / 1000 )
				break

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
starttime = None
mode = None
name = None
url = None
thumb = None
plot = None
studio = None
program_id = None
backup_url = None
topic = None
page = 0

try:
	topic = urllib.unquote_plus( params["topic"] )
except:
	pass
try:
	backup_url = urllib.unquote_plus( params["backup_url"] )
except:
	pass
try:
	program_id = urllib.unquote_plus( params["program_id"] )
except:
	pass
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
try:
	starttime = int( params["starttime"] )
except:
	pass

if mode == None:
	print __plugin__ + ' ' + __version__ + ' ' + __date__
	build_main_directory()
elif mode == 0:
	find_videos( name, program_id, topic, page )
elif mode == 1:
	build_programs_directory()
elif mode == 2:
	build_topics_directory()
elif mode == 4:	
	build_search_keyboard()
elif mode == 5:
	play_video( name, url, thumb, plot, studio, starttime, backup_url )
elif mode == 6:
	build_search_directory( url, page )
elif mode == 7:
	play_mp4( name, url, thumb, plot, studio, starttime )
