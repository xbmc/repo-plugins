	
import xbmc, xbmcgui, xbmcplugin, urllib2, urllib, re, string, sys, os, traceback, xbmcaddon
import xml.dom.minidom
import time
import threading
from BeautifulSoup import BeautifulStoneSoup, BeautifulSoup

__plugin__ = 'Pakee'
__author__ = 'pakeeapp@gmail.com'
__url__ = 'http://code.google.com/p/pakee/'
__date__ = '01-04-2011'
__version__ = '1.0.1'
__settings__ = xbmcaddon.Addon(id='plugin.video.pakee')
__rooturl__ = 'http://pakee.hopto.org/pakee/pakee-betaplus.xml'
__language__ = __settings__.getLocalizedString

pakee_thumb = os.path.join( __settings__.getAddonInfo( 'path' ), 'resources', 'media', 'pakee.png' )



setting_play_all = (xbmcplugin.getSetting(int( sys.argv[1] ), 'play_all') == "true")
	
#setting_play_all = __settings__.getSetting('play_all')
#print ("setting_play_all is: " + str(setting_play_all) + " lang is " + str(__language__) + " __settings__ is " + str(__settings__))
#__settings__.openSettings()
#xbmcplugin.openSettings( sys.argv[1] )

def open_url( url ):
	req = urllib2.Request( url )
	content = urllib2.urlopen( req )
	data = content.read()
	content.close()
	return data

def clean( name ):
	list = [ ( '&amp;', '&' ), ( '&quot;', '"' ), ( '<em>', '' ), ( '</em>', '' ), ( '&#39;', '\'' ), ( '&#039;', '\'' ), ('&amp;#039;', '\'') ]
	for search, replace in list:
		name = name.replace( search, replace )	
	#return unicode(name.encode("utf-8"))
	return unicode(name)



def play_youtube_video(video_id, name):
	print ("Playing video " + name + " id: " + video_id)
	url = 'plugin://plugin.video.youtube/?action=play_video&videoid=%s' % (video_id)
	listitem = xbmcgui.ListItem( label = str(name), iconImage = "DefaultVideo.png", thumbnailImage = xbmc.getInfoImage( "ListItem.Thumb" ), path=url )
	infolabels = { "title": name, "plot": name}
	listitem.setInfo( type="Video", infoLabels=infolabels)
	xbmc.Player( xbmc.PLAYER_CORE_DVDPLAYER ).play( str(url), listitem)
		
	
def play_audio(url, name):
	print "playing audio file. name: " + name + " url: " + url
	listitem = xbmcgui.ListItem( label = str(name), iconImage = "DefaultVideo.png", thumbnailImage = xbmc.getInfoImage( "ListItem.Thumb" ), path=url )
	listitem.setInfo( type="video", infoLabels={ "Title": name, "Plot" : name } )
	xbmc.Player( xbmc.PLAYER_CORE_DVDPLAYER ).play( str(url), listitem)

def play_picture_slideshow(origurl, name):
	print "Starting play_picture_slideshow(): " + str(origurl)

	#user clicked on a picture
	if origurl[-4:]=='.jpg' or origurl[-4:]=='.gif' or origurl[-4:]=='.png':
		print "Single picture mode"		
		origurl = origurl.replace( ' ', '%20' )
		xbmc.log("adding to picture slideshow: " + str(origurl))
		xbmc.executehttpapi("ClearSlideshow")
		xbmc.executehttpapi("AddToSlideshow(%s)" % origurl)
		xbmc.executebuiltin( "SlideShow(,,notrandom)" )
		return
		
	#user clicked on <start slideshow>
	items = getItemsFromUrl(origurl)

	xbmc.executehttpapi("ClearSlideshow")	

	itemCount=0
	for item in items:
		itemCount=itemCount+1
		label, url, description, pubDate, guid, thumb, duration, rating, viewcount = getItemFields(item)
		if url is not None and url != '':
			xbmc.executehttpapi("AddToSlideshow(%s)" % url)

	print "# of pictures added to sideshow " + str(itemCount)
	xbmc.executebuiltin( "SlideShow(,,notrandom)" )

def play_playlist(origurl):
	print "Starting play_playlist(): " + str(origurl)

	items = getItemsFromUrl(origurl)
	if items is None:
		return

	player = xbmc.Player()
	if player.isPlaying():
		player.stop()
    
	playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
	playlist.clear()   
	

	itemCount=0
	for item in items:
		label, url, description, pubDate, guid, thumb, duration, rating, viewcount = getItemFields(item)

		itemCount=itemCount+1

		if guid is not None and guid != '':
			print "Found item: " + label + " guid: " + guid 
			playlisturl = 'plugin://plugin.video.youtube/?action=play_video&videoid=%s' % (guid)

		elif url is not None and url != '':
			print "Found item: " + label + " url: " + url 
			playlisturl = url

		if playlisturl is not None and playlisturl !='':
			listitem = xbmcgui.ListItem( label = label,  thumbnailImage = thumb, path=playlisturl )
			listitem.setInfo( type="video", infoLabels={ "Title": label, "Plot" : description } )
			#print "adding to playlist"
			playlist.add(url=playlisturl, listitem=listitem)

	print "# of files added to playlist " + str(itemCount)
	xbmc.Player().play(playlist)



def build_show_directory(origurl):

	#from threading import Timer
	if origurl:
		xbmc.log('Starting build_show_directory() with url: ' + origurl)
	else:
		xbmc.executehttpapi("sendkey(I)")
		xbmc.log('Starting build_show_directory() with no url. Showing info')

		return


	#items = getItemsFromUrlBS(origurl)
	items = getItemsFromUrl(origurl)

	if items is None:
		return



	itemCount=0
	for item in items:

		#label, url, description, pubDate, guid, thumb, duration, rating, viewcount = getItemFieldsBS(item)
		label, url, description, pubDate, guid, thumb, duration, rating, viewcount = getItemFields(item)

		mode = 10
		isFolder = True

		try:
			xbmc.log('found in show_dir(): ' + clean(str(label)) + ' ' + str(url) + ' ' + str(rating) + ' ' + str(pubDate) + ' ' + str(duration) + ' ' + str(viewcount)) 
		except:
			label = ''
			description = ''
			#url = ''
			xbmc.log('found in show_dir(): ' + str(url) + ' ' + str(rating) + ' ' + str(pubDate) + ' ' + str(duration) + ' ' + str(viewcount))	

		if (url is not None and url != ''):
			if 'youtube.com' in url or '(Playlist: ' in label:
				#For folders with videos, show play all option 			
				if itemCount == 0:
					playAll = xbmcgui.ListItem( label = '<Play all videos below>', iconImage = pakee_thumb, thumbnailImage = pakee_thumb )
					xbmcplugin.addDirectoryItem( handle = int( sys.argv[1] ), url = sys.argv[0] + "?mode=80&name=Playlist&url=" + urllib.quote_plus(origurl), listitem = playAll, isFolder = True )

			if 'youtube.com' in url:
				mode = 20
				isFolder = False
				url = guid



			if url[-4:]=='.jpg' or url[-4:]=='.gif' or url[-4:]=='.png':
				#For folders with videos, show play all option 			
				if itemCount == 0:
					playAll = xbmcgui.ListItem( label = '<Start slideshow>', iconImage = pakee_thumb, thumbnailImage = pakee_thumb )
					xbmcplugin.addDirectoryItem( handle = int( sys.argv[1] ), url = sys.argv[0] + "?mode=90&name=Playlist&url=" + urllib.quote_plus(origurl), listitem = playAll, isFolder = True )

				isFolder = False
				mode = 90
	
			if '.mp3' in url or '.wma' in url or 'http://bit.ly' in url or '/getSharedFile/' in url:
				mode = 70
				isFolder = False
				if itemCount == 0:
					playAll = xbmcgui.ListItem( label = '<Play all>', iconImage = pakee_thumb, thumbnailImage = pakee_thumb )
					xbmcplugin.addDirectoryItem( handle = int( sys.argv[1] ), url = sys.argv[0] + "?mode=80&name=Playlist&url=" + urllib.quote_plus(origurl), listitem = playAll, isFolder = True )



		itemCount=itemCount+1		
		xbmcplugin.setContent( handle=int( sys.argv[ 1 ] ), content='movies' )
		listitem = xbmcgui.ListItem( label = label, iconImage = thumb, thumbnailImage = thumb, path = url)
		infolabels = { "title": label, "plot": description, "plotoutline": description, "date": pubDate, "duration": duration, "rating": rating, "votes": viewcount, "tvshowtitle": label, "originaltitle": label, "count": viewcount}
		listitem.setInfo( type="video", infoLabels=infolabels )

		if url:
			u = sys.argv[0] + "?mode=" + str(mode) + "&name=" + urllib.quote_plus( str(label) ) + "&url=" + urllib.quote_plus( url )
		else:
			u = sys.argv[0] + "?mode=" + str(mode) + "&name=" + urllib.quote_plus( label )
	
		ok = xbmcplugin.addDirectoryItem( handle = int( sys.argv[1] ), url = u, listitem = listitem, isFolder = isFolder )

	#show search options on only the main page
	if origurl == __rooturl__:
		searchPakee = xbmcgui.ListItem( label = 'Search Pakee...', iconImage = thumb, thumbnailImage = thumb )
		xbmcplugin.addDirectoryItem( handle = int( sys.argv[1] ), url = sys.argv[0] + "?mode=30&name=Search Pakee...", listitem = searchPakee, isFolder = True )

		searchYT = xbmcgui.ListItem( label = 'Search YouTube...', iconImage = thumb, thumbnailImage = thumb )
		xbmcplugin.addDirectoryItem( handle = int( sys.argv[1] ), url = sys.argv[0] + "?mode=40&name=Search YouTube...", listitem = searchYT, isFolder = True )

		searchYT = xbmcgui.ListItem( label = 'YouTube user uploads/playlists...', iconImage = thumb, thumbnailImage = thumb )
		xbmcplugin.addDirectoryItem( handle = int( sys.argv[1] ), url = sys.argv[0] + "?mode=50&name=YouTube user uploads and playlists", listitem = searchYT, isFolder = True )

		searchYT = xbmcgui.ListItem( label = 'YouTube user favorites...', iconImage = thumb, thumbnailImage = thumb )
		xbmcplugin.addDirectoryItem( handle = int( sys.argv[1] ), url = sys.argv[0] + "?mode=60&name=YouTube user favorites", listitem = searchYT, isFolder = True )


	sortmethods = ( xbmcplugin.SORT_METHOD_UNSORTED, xbmcplugin.SORT_METHOD_VIDEO_TITLE, xbmcplugin.SORT_METHOD_VIDEO_RUNTIME, xbmcplugin.SORT_METHOD_DATE, xbmcplugin.SORT_METHOD_PROGRAM_COUNT  )
	for sortmethod in sortmethods:	
		xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=sortmethod )	

	xbmc.executebuiltin("Container.SetViewMode(503)")
	xbmcplugin.endOfDirectory( int( sys.argv[1] ) )





def getItemFieldsBS(item):

	label=''
	url = ''
	thumb = ''
	guid = ''
	description = ''
	pubDate = '01.01.1960'
	rating = 0.0
	duration = 0
	viewcount = '0'


	if item.title:
		label = clean(item.title.string)
	if item.link:
		url = item.link.string
	else:
		url = ''

	if item.enclosure:
		url = item('enclosure')[0]['url']

	if item.description:
		description = item.description.string

	if item('boxee:release-date'):
		pubDate = item('boxee:release-date')[0].string
		#xbmc.log('pubdate: x' + str(pubDate) + 'x')
		if pubDate is None or pubDate=='':
			pubDate = '01.01.1960'
		else:
			tpubDate = time.strptime(pubDate, '%Y-%m-%d')
			pubDate = time.strftime("%d.%m.%Y", tpubDate)

	if item.guid:
		guid = item.guid.string

	if item('media:thumbnail'):
        	thumb = item('media:thumbnail')[0]['url']
	if item('media:content'):
        	duration = item('media:content')[0]['duration']

		if duration is None or duration == '':
			duration = 0
		else:	
			duration = string.atoi(duration)
			#duration = int(duration)			
		duration = time.strftime('%H:%M:%S', time.gmtime(duration))

	if item('media:starrating'):
		print item('media:starrating')[0]['average'] + ' '  + item('media:starrating')[0]['viewcount']
		if item('media:starrating')[0]['average']:
			rating = item('media:starrating')[0]['average']
		else:
			rating = '0.0'
		rating = string.atof(rating)

		if item('media:starrating')[0]['viewcount']:
			viewcount = item('media:starrating')[0]['viewcount']
		else:
			viewcount = '0'
		viewcount = string.atoi(viewcount)

	if url:
		url = url.replace( ' ', '%20' )

	#return {'label': label, 'url':url, 'description': description, 'pubDate': pubDate, 'guid': guid, 'thumb': thumb, 'duration': duration, 'rating': rating, 'viewcount': viewcount}
	return label, url, description, pubDate, guid, thumb, duration, rating, viewcount



def getItemsFromUrlBS(url):
	try:
		file = urllib2.urlopen(url)
		t = threading.Timer(100000.0, file.close)
		t.start()
		link = file.read()
		file.close()
	except:
		xbmcgui.Dialog().ok('Pakee','Request timed out. Please try again')
		return

        soup = BeautifulStoneSoup(link, convertEntities=BeautifulStoneSoup.XML_ENTITIES)
        items = soup('item')
	return items

def getItemsFromUrl(url):

	try:

		#file = urllib2.urlopen(url)
		#t = threading.Timer(100000, file.close)
		#t.start()
		#data = file.read()
		#file.close()

		file = urllib2.urlopen(url)
		data = file.read()
		file.close()
	except:
		xbmcgui.Dialog().ok('Pakee','Request timed out. Please try again')
		return

	dom =  xml.dom.minidom.parseString(data)
	items = dom.getElementsByTagName('item')
	return items


def getItemFields(item):

	label=''
	url = ''
	thumb = ''
	guid = ''
	description = ''
	pubDate = '01.01.1960'
	rating = 0.0
	duration = 0
	viewcount = '0'

	if item.getElementsByTagName("title"):
		label = clean(getText(item.getElementsByTagName("title")[0].childNodes))
	else:
		label = 'No title'
	if item.getElementsByTagName("link"):
		url = getText(item.getElementsByTagName("link")[0].childNodes)
	elif item.getElementsByTagName("enclosure"):
		url = item.getElementsByTagName("enclosure")[0].getAttribute('url')
	else:
		url = ''
	if item.getElementsByTagName("description"):
		description = clean(getText(item.getElementsByTagName("description")[0].childNodes))
	else:
		description = ''
	if item.getElementsByTagNameNS("http://search.yahoo.com/mrss/","thumbnail"):
		thumb = item.getElementsByTagNameNS("http://search.yahoo.com/mrss/","thumbnail")[0].getAttribute('url')
	else:
		thumb = pakee_thumb

	if item.getElementsByTagNameNS("http://search.yahoo.com/mrss/","content"):
		duration = item.getElementsByTagNameNS("http://search.yahoo.com/mrss/","content")[0].getAttribute('duration')
	else:
		duration = ''
	if duration == '':
		duration = 0
	else:
		duration = string.atoi(duration)
	duration = time.strftime('%H:%M:%S', time.gmtime(duration))

	
	if item.getElementsByTagNameNS("http://search.yahoo.com/mrss/","starRating"):
		rating = item.getElementsByTagNameNS("http://search.yahoo.com/mrss/","starRating")[0].getAttribute('average')
	else:
		rating = ''
	if rating == '':
		rating = 0.0
	else:
		rating = string.atof(rating)

	if item.getElementsByTagNameNS("http://search.yahoo.com/mrss/","starRating"):
		viewcount = item.getElementsByTagNameNS("http://search.yahoo.com/mrss/","starRating")[0].getAttribute('viewcount')
		if viewcount == '':
			viewcount = '0'
	else:
		viewcount = '0'
	viewcount = string.atoi(viewcount)


	if item.getElementsByTagName("pubDate"):
		pubDate = getText(item.getElementsByTagName("pubDate")[0].childNodes)
		if pubDate == '':
			pubDate = '01.01.1960'
		else:
			tpubDate = time.strptime(pubDate, '%Y-%m-%d')
			pubDate = time.strftime("%d.%m.%Y", tpubDate)
	else:
		pubDate = '01.01.1960'

	if item.getElementsByTagName("guid"):
		guid = getText(item.getElementsByTagName("guid")[0].childNodes)

	return label, url, description, pubDate, guid, thumb, duration, rating, viewcount



def getText(nodelist):
	rc = []
	for node in nodelist:
		if node.nodeType == node.TEXT_NODE:
			rc.append(node.data)
	return ''.join(rc)


	
def build_search_directory(paramName):
	if paramName == 'querydb':
		title = 'Search Pakee'
	else:
		title = 'Search YouTube'

	keyboard = xbmc.Keyboard( '', title )
	keyboard.doModal()
	if ( keyboard.isConfirmed() == False ):
		return
	search_string = keyboard.getText().replace( ' ', '+' )
	if len( search_string ) == 0:
		return

	build_show_directory('http://pakee.hopto.org/pakee/getYoutubePlaylistQuick.php?' + paramName + '=' + search_string)


def build_ytuser_directory():
	keyboard = xbmc.Keyboard( '', 'Enter YouTube userid' )
	keyboard.doModal()
	if ( keyboard.isConfirmed() == False ):
		return
	search_string = keyboard.getText().replace( ' ', '+' )
	if len( search_string ) == 0:
		return

	build_show_directory('http://pakee.hopto.org/pakee/getYoutubePlaylistQuick.php?id=' + search_string)

def build_ytuser_favs_directory():
	keyboard = xbmc.Keyboard( '', 'Enter YouTube userid' )
	keyboard.doModal()
	if ( keyboard.isConfirmed() == False ):
		return
	search_string = keyboard.getText().replace( ' ', '+' )
	if len( search_string ) == 0:
		return

	build_show_directory('http://pakee.hopto.org/pakee/getYoutubePlaylistQuick.php?favorites=1&id=' + search_string)

	

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
description = None
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

print ("pakee started with mode: " + str(mode))

if mode == None:
	build_show_directory(__rooturl__)
elif mode == 10:
	build_show_directory(url)
elif mode == 20:
	play_youtube_video(url, name)
elif mode == 30:
	build_search_directory('querydb')
elif mode == 40:
	build_search_directory('queryyt')
elif mode == 50:
	build_ytuser_directory()
elif mode == 60:
	build_ytuser_favs_directory()
elif mode == 70:
	play_audio(url, name)
elif mode == 80:
	play_playlist(url)
elif mode == 90:
	play_picture_slideshow(url, name)
