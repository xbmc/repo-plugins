
import xbmc, xbmcaddon, xbmcgui, xbmcplugin, urllib2, urllib, re, string, sys, os, traceback, time, datetime
import simplejson as json

__plugin__ = 'National Geographic'
__author__ = 'stacked <stacked.xbmc@gmail.com>'
__url__ = 'http://code.google.com/p/plugin/'
__date__ = '12-13-2011'
__version__ = '1.0.0'
__settings__ = xbmcaddon.Addon( id = 'plugin.video.national.geographic' )

next_thumb = os.path.join( __settings__.getAddonInfo( 'path' ), 'resources', 'media', 'next.png' )
natgeowild_thumb = os.path.join( __settings__.getAddonInfo( 'path' ), 'resources', 'media', 'natgeowild.png' )
natgeo_thumb = os.path.join( __settings__.getAddonInfo( 'path' ), 'resources', 'media', 'natgeo.png' )

def open_url( url ):
	req = urllib2.Request( url )
	req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-GB; rv:1.9.2.8) Gecko/20100722 Firefox/3.6.8')
	content = urllib2.urlopen( req )
	data = content.read()
	content.close()
	return data

def clean( name ):
	remove = [ ('&amp;','&'), ('&quot;','"'), ('&#39;','\''), ('u2013','-'), ('u201c','\"'), ('u201d','\"'), ('u2019','\''), ('<p>',''), ('</p>','') ]
	for trash, crap in remove:
		name = name.replace( trash, crap )
	return name
	
def build_main_directory():
	main=[
		( 'National Geographic Channel', natgeo_thumb, 'national-geographic-channel' ),
		( 'Nat Geo Wild', natgeowild_thumb, 'nat-geo-wild' )
		]
	for label, thumb, id in main:
		listitem = xbmcgui.ListItem( label = label, iconImage = "DefaultVideo.png", thumbnailImage = thumb )
		listitem.setProperty('fanart_image',__settings__.getAddonInfo('fanart'))
		u = sys.argv[0] + "?mode=0&label=" + urllib.quote_plus( label ) + "&id=" + urllib.quote_plus( id )
		ok = xbmcplugin.addDirectoryItem( handle = int( sys.argv[1] ), url = u, listitem = listitem, isFolder = True )
	xbmcplugin.addSortMethod( handle = int(sys.argv[1]), sortMethod = xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( int( sys.argv[1] ) )

def build_category_directory( label, id, hasChild ):
	print 'http://video.nationalgeographic.com/video/player/data/json/category_' + id + '.json'
	data = open_url('http://video.nationalgeographic.com/video/player/data/json/category_' + id + '.json')
	data = json.loads( data )
	for children in data['section']['children']:
		id = children['id'].encode('utf-8')
		label = children['label']
		hasChild = children['hasChild']
		if hasChild == 'true':
			mode = 0
		else:
			mode = 1
		listitem = xbmcgui.ListItem( label = label, iconImage = "DefaultVideo.png", thumbnailImage = "thumbnailImage" )
		u = sys.argv[0] + "?mode=" + str( mode ) + "&label=" + urllib.quote_plus( label ) + "&id=" + urllib.quote_plus( id ) + "&hasChild=" + urllib.quote_plus( hasChild )
		ok = xbmcplugin.addDirectoryItem( handle = int( sys.argv[1] ), url = u, listitem = listitem, isFolder = True )
	xbmcplugin.addSortMethod( handle = int(sys.argv[1]), sortMethod = xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( int( sys.argv[1] ) )

def build_lineup_directory( label, id, page ):
	print 'http://video.nationalgeographic.com/video/player/data/json/lineup_' + id + '_' + str(page) + '.json'
	data = open_url('http://video.nationalgeographic.com/video/player/data/json/lineup_' + id + '_' + str(page) + '.json')
	data = json.loads( data )
	name = label
	saveid = id
	for video in data['lineup']['video']:
		id = video['id'].encode('utf-8')
		title = clean(video['title']).encode('utf-8')
		thumb = video['thumb']
		duration = video['time']
		plot = clean(video['caption'].encode('utf-8'))
		listitem = xbmcgui.ListItem( label = title, iconImage = thumb, thumbnailImage = thumb )
		listitem.setInfo( type="Video", infoLabels={ "Title": title, "Director": "National Geographic", "Studio": name, "Duration": duration, "Plot": plot } )
		u = sys.argv[0] + "?mode=2&name=" + urllib.quote_plus( title ) + "&id=" + urllib.quote_plus( id ) + "&thumb=" + urllib.quote_plus( thumb ) + "&studio=" + urllib.quote_plus( name ) + "&plot=" + urllib.quote_plus( plot )
		ok = xbmcplugin.addDirectoryItem( handle = int( sys.argv[1] ), url = u, listitem = listitem, isFolder = False )
	if ( int(data['lineup']['totalpages']) - 1 ) > page:
		listitem = xbmcgui.ListItem( label = '[Next Page (' + str( int( page ) + 1 ) + ')]' , iconImage = next_thumb, thumbnailImage = next_thumb )
		u = sys.argv[0] + '?mode=1&label=' + urllib.quote_plus( name ) + '&id=' + urllib.quote_plus( saveid ) + "&page=" + str( int( page ) + 1 )
		ok = xbmcplugin.addDirectoryItem( handle = int( sys.argv[1] ), url = u, listitem = listitem, isFolder = True )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_UNSORTED )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_VIDEO_RUNTIME )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_LABEL )
	xbmcplugin.endOfDirectory( int( sys.argv[1] ) )
		
def play_video( name, id, thumb, studio, plot ):
	print 'http://video.nationalgeographic.com/video/player/data/json/video_' + id + '.json'
	data = open_url('http://video.nationalgeographic.com/video/player/data/json/video_' + id + '.json')
	id = re.compile( '"id":"(.+?)"' ).findall( data )[0]
	print id
	if len(id) == 4:
		url = 'http://channel.nationalgeographic.com/channel/videos/feeds/xms/' + id[:2] + '/' + id[2:] + '/video_000' + id + '.xml'
	else:
		id = id[1:]
		url = 'http://channel.nationalgeographic.com/channel/videos/feeds/xms/' + id[:2] + '/' + id[2:] + '/video_001' + id + '.xml'
	print url
	data = open_url( url )
	url = 'rtmp://' + re.compile( 'rtmp://(.+?)</file>').findall( data )[0]
	item = xbmcgui.ListItem( label = name, iconImage = "DefaultVideo.png", thumbnailImage = thumb )
	item.setInfo( type="Video", infoLabels={ "Title": name , "Director": "National Geographic", "Studio": studio } )
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
id = None
label = None
hasChild = None
plot = None
page = 0

try:
	page = int( params["page"] )
except:
	pass
try:
	plot = urllib.unquote_plus(params["plot"])
except:
	pass
try:
	hasChild = urllib.unquote_plus(params["hasChild"])
except:
	pass
try:
	label = urllib.unquote_plus(params["label"])
except:
	pass
try:
	id = urllib.unquote_plus(params["id"])
except:
	pass
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
	build_category_directory( label, id, hasChild )
elif mode == 1:
	build_lineup_directory( label, id, page )
elif mode == 2:
	play_video( name, id, thumb, studio, plot )
	