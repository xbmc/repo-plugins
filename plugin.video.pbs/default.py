
import xbmc, xbmcgui, xbmcplugin, urllib2, urllib, re, base64, string, sys, os, traceback, time, xbmcaddon, datetime, coveapi, buggalo
from urllib2 import Request, urlopen, URLError, HTTPError

plugin = "PBS"
__author__ = 'stacked <stacked.xbmc@gmail.com>'
__url__ = 'http://code.google.com/p/plugin/'
__date__ = '12-29-2012'
__version__ = '2.0.8'
settings = xbmcaddon.Addon( id = 'plugin.video.pbs' )
buggalo.SUBMIT_URL = 'http://www.xbmc.byethost17.com/submit.php'
dbg = False
dbglevel = 3
programs_thumb = os.path.join( settings.getAddonInfo( 'path' ), 'resources', 'media', 'programs.png' )
topics_thumb = os.path.join( settings.getAddonInfo( 'path' ), 'resources', 'media', 'topics.png' )
search_thumb = os.path.join( settings.getAddonInfo( 'path' ), 'resources', 'media', 'search.png' )
next_thumb = os.path.join( settings.getAddonInfo( 'path' ), 'resources', 'media', 'next.png' )
pbskids_thumb = os.path.join( settings.getAddonInfo( 'path' ), 'resources', 'media', 'pbskids.png' )
fanart = os.path.join( settings.getAddonInfo( 'path' ), 'fanart.jpg' )
cove = coveapi.connect(base64.b64decode(settings.getLocalizedString( 30010 )), 
                       base64.b64decode(settings.getLocalizedString( 30011 )))
					 
import CommonFunctions
common = CommonFunctions
common.plugin = plugin + ' ' + __version__

from addonfunc import addListItem, playListItem, getUrl, setViewMode, getParameters, retry

def clean( string ):
	list = [( '&amp;', '&' ), ( '&quot;', '"' ), ( '&#39;', '\'' ), ( '\n','' ), ( '\r', ''), ( '\t', ''), ( '</p>', '' ), ( '<br />', ' ' ), 
			( '<br/>', ' ' ), ( '<b>', '' ), ( '</b>', '' ), ( '<p>', '' ), ( '<div>', '' ), ( '</div>', '' ), ( '<strong>', ' ' ), 
			( '<\/strong>', ' ' ), ( '</strong>', ' ' ), ( '&hellip;', '...' ), ( '&ntilde;', 'n' ), ('&ldquo;', '\"'), ('&rdquo;', '\"'),
			('<a href=\"', ''), ('</a>', ''), ('\">', ' ')]
	for search, replace in list:
		string = string.replace( search, replace )
	return string

def build_main_directory():
	main=[
		( settings.getLocalizedString( 30000 ), programs_thumb, '1' ),
		( settings.getLocalizedString( 30001 ), topics_thumb, '2' ),
		( settings.getLocalizedString( 30003 ), search_thumb, '4' ),
		( settings.getLocalizedString( 30014 ), pbskids_thumb, '1' )
		]
	for name, thumbnailImage, mode in main:
		u = { 'mode': mode, 'name': name }
		addListItem(label = name, image = thumbnailImage, url = u, isFolder = True, infoLabels = False, fanart = fanart)
	try:
		build_most_watched_directory()
	except:
		pass
	xbmcplugin.addSortMethod( handle = int(sys.argv[1]), sortMethod = xbmcplugin.SORT_METHOD_NONE )
	setViewMode("501")
	xbmcplugin.endOfDirectory( int( sys.argv[1] ) )
	
def build_most_watched_directory():
	url = 'http://video.pbs.org/'
	data = getUrl( url )
	list = common.parseDOM(data, "ul", attrs = { "class": "video-list clear clearfix" })
	videos = common.parseDOM(list, "span", attrs = { "class": "title clear clearfix" })
	img = common.parseDOM(list, "img", ret = "src")
	count = 0
	for video in videos:
		program_id = common.parseDOM(video, "a", ret = "href")[0].rsplit('/')[4]
		title = common.parseDOM(video, "a")[0]
		label = clean(title)
		thumb = img[count]
		infoLabels = { "Title": label, "Director": "PBS", "Studio": clean(title.rsplit(' | ')[0]) }
		u = { 'mode': '0', 'name': label, 'program_id': program_id, 'topic': 'False', 'page': '0' }
		addListItem(label = label, image = thumb, url = u, isFolder = False, infoLabels = infoLabels, fanart = fanart)
		count += 1

@retry(TypeError)
def build_programs_directory( name, page ):
	checking = True
	while checking:
		start = str( 200 * page )
		#data = cove.programs.filter(fields='associated_images,mediafiles,categories',filter_categories__namespace__name='COVE Taxonomy',order_by='title',limit_start=start)
		if name != settings.getLocalizedString( 30014 ) and name != settings.getLocalizedString( 30000 ):
			data = cove.programs.filter(fields='associated_images',order_by='title',limit_start=start,filter_title=name)
		else:
			data = cove.programs.filter(fields='associated_images',order_by='title',limit_start=start)
		if ( len(data) ) == 200:
			page = page + 1
		else:
			checking = False
		for results in data:
			if len(results['nola_root'].strip()) != 0:
				if name == settings.getLocalizedString( 30014 ):
					if results['tp_account'] == 'PBS DP KidsGo':
						process_list = True
					else:
						process_list = False
				else:
					if results['tp_account'] == 'PBS DP KidsGo':
						process_list = False
					else:
						process_list = True
				if process_list:
					if len(results['associated_images']) >= 2:
						thumb = results['associated_images'][1]['url']
					else:
						thumb = programs_thumb
					program_id = re.compile( '/cove/v1/programs/(.*?)/' ).findall( results['resource_uri'] )[0]
					infoLabels = { "Title": results['title'].encode('utf-8'), "Plot": clean(results['long_description']) }
					u = { 'mode': '0', 'name': urllib.quote_plus( results['title'].encode('utf-8') ), 'program_id': urllib.quote_plus( program_id ) }
					addListItem(label = results['title'], image = thumb, url = u, isFolder = True, infoLabels = infoLabels, fanart = fanart)
	# if ( len(data) ) == 200:
		# u = { 'mode': '1', 'page': str( int( page ) + 1 ) }
		# addListItem(label = '[Next Page (' + str( int( page ) + 2 ) + ')]', image = next_thumb, url = u, isFolder = True, infoLabels = False)
	xbmcplugin.addSortMethod( handle = int(sys.argv[1]), sortMethod = xbmcplugin.SORT_METHOD_NONE )
	if name == settings.getLocalizedString( 30014 ):
		setViewMode("500")
	else:
		setViewMode("503")
	xbmcplugin.endOfDirectory( int( sys.argv[1] ) )
		
def build_topics_directory():
	data = cove.categories.filter(order_by='name',filter_namespace__name='COVE Taxonomy')
	item = None
	for results in data:
		if item != results['name']:
			u = { 'mode': '0', 'name': urllib.quote_plus( results['name'] ), 'topic': urllib.quote_plus( 'True' ) }
			addListItem(label = results['name'], image = topics_thumb, url = u, isFolder = True, infoLabels = False, fanart = fanart)
			item = results['name']
	xbmcplugin.addSortMethod( handle = int(sys.argv[1]), sortMethod = xbmcplugin.SORT_METHOD_NONE )
	setViewMode("515")
	xbmcplugin.endOfDirectory( int( sys.argv[1] ) )

def build_search_keyboard():
	keyboard = xbmc.Keyboard( '', settings.getLocalizedString( 30003 ) + ' ' + settings.getLocalizedString( 30013 ) )
	keyboard.doModal()
	if ( keyboard.isConfirmed() == False ):
		return
	search_string = keyboard.getText()
	if len( search_string ) == 0:
		return
	#build_search_directory( search_string, page )
	find_videos( search_string, 'program_id', 'search', 0 )

def build_search_directory( url, page ):
	save_url = url.replace( ' ', '%20' )
	url = 'http://www.pbs.org/search/?q=' + url.replace( ' ', '%20' ) + '&ss=pbs&mediatype=Video&start=' + str( page * 10 )
	data = getUrl( url )
	title_id_thumb = re.compile('<a title="(.*?)" target="" rel="nofollow" onclick="EZDATA\.trackGaEvent\(\'search\', \'navigation\', \'external\'\);" href="(.*?)"><img src="(.*?)" class="ez-primaryThumb"').findall(data)
	program = re.compile('<p class="ez-metaextra1 ez-icon">(.*?)</p>').findall(data)
	plot = re.compile('<p class="ez-desc">(.*?)<div class="(ez-snippets|ez-itemUrl)">', re.DOTALL).findall(data)
	video_count = re.compile('<b class="ez-total">(.*?)</b>').findall(data)
	if len(title_id_thumb) == 0:
		dialog = xbmcgui.Dialog()
		ok = dialog.ok( plugin , settings.getLocalizedString( 30004 ) + '\n' + settings.getLocalizedString( 30005 ) )
		return
	item_count = 0
	for title, id, thumb in title_id_thumb:
		infoLabels = { "Title": clean( title ) , "Director": "PBS", "Studio": clean( program[item_count] ), "Plot": clean( plot[item_count][0] ) }
		u = { 'mode': '0', 'name': urllib.quote_plus( clean( program[item_count] ) ), 'program_id': urllib.quote_plus( id.rsplit('/')[4] ), 'topic': urllib.quote_plus( 'False' ) }
		addListItem(label = clean( title ), image = thumb, url = u, isFolder = False, infoLabels = infoLabels, fanart = fanart)
		item_count += 1	
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_STUDIO )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_LABEL )
	if page == 0:
		build_programs_directory( save_url.replace( '%20', ' ' ), 0 )
	if ( int( video_count[0] ) - ( 10 * int( page ) ) ) > 10:
		u = { 'mode': '6', 'page': str( int( page ) + 1 ), 'url': urllib.quote_plus( save_url ) }
		addListItem(label = '[Next Page (' + str( int( page ) + 2 ) + ')]', image = next_thumb, url = u, isFolder = True, infoLabels = False, fanart = fanart)
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_STUDIO )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_LABEL )
	setViewMode("503")
	xbmcplugin.endOfDirectory( int( sys.argv[1] ) )

@retry(TypeError)
def find_videos( name, program_id, topic, page ):
	start = str( 200 * page )
	url = 'None'
	backup_url = None
	if topic == 'True':
		program_id = 'program_id'
		data = cove.videos.filter(fields='associated_images,mediafiles,categories',filter_categories__name=name,order_by='-airdate',filter_availability_status='Available',limit_start=start,exclude_type__in='Chapter,Promotion')
	elif topic == 'False':
		data = cove.videos.filter(fields='associated_images,mediafiles',filter_tp_media_object_id=program_id,limit_start=start)
		print "PBS - Video ID: " + program_id
		if len(data) == 0:
			dialog = xbmcgui.Dialog()
			ok = dialog.ok( plugin , settings.getLocalizedString( 30009 ) + '\n' + 'http://video.pbs.org/video/' + program_id )
			return
	elif topic == 'search':
		data = cove.videos.filter(fields='associated_images,mediafiles',filter_title__contains=name,order_by='-airdate',filter_availability_status='Available',limit_start=start)
		if len(data) == 0:
			data = cove.videos.filter(fields='associated_images,mediafiles',filter_title__contains=string.capwords(name),order_by='-airdate',filter_availability_status='Available',limit_start=start)
	else:
		topic = 'topic'
		data = cove.videos.filter(fields='associated_images,mediafiles',filter_program=program_id,order_by='-airdate',filter_availability_status='Available',limit_start=start,exclude_type__in='Chapter,Promotion')
		if len(data) <= 1:
			data = cove.videos.filter(fields='associated_images,mediafiles',filter_program=program_id,order_by='-airdate',filter_availability_status='Available',limit_start=start)
	for results in data:
		playable = None
		if results['associated_images'] != None and len(results['associated_images']) > 0:
			thumb = results['associated_images'][0]['url']
		else:
			thumb = 'None'
		count = 0
		for videos in results['mediafiles']:
			if results['mediafiles'][count]['video_encoding']['name'] == 'MPEG-4 500kbps':
				playable = count
			count += 1
		if playable == None:
			playable = count - 1
		if playable != -1:
			if results['mediafiles'][playable]['video_data_url'] != None:
				url = results['mediafiles'][playable]['video_data_url']
				mode = '5'
				if results['mediafiles'][playable]['video_download_url'] != None:
					backup_url = results['mediafiles'][playable]['video_download_url']
				else:
					backup_url = 'None'	
			elif results['mediafiles'][playable]['video_data_url'] == None and results['mediafiles'][playable]['video_download_url'] == None:
				url = 'None'
				mode = '5'
			else:
				url = results['mediafiles'][playable]['video_download_url']
				mode = '7'
			infoLabels = { "Title": results['title'].encode('utf-8'), "Director": "PBS", "Studio": name, "Plot": results['long_description'].encode('utf-8'), "Aired": results['airdate'].rsplit(' ')[0], "Duration": str((int(results['mediafiles'][0]['length_mseconds'])/1000)/60) }
			u = { 'mode': mode, 'name': urllib.quote_plus( results['title'].encode('utf-8') ), 'url': urllib.quote_plus( url ), 'thumb': urllib.quote_plus( thumb ), 'plot': urllib.quote_plus( results['long_description'].encode('utf-8') ), 'studio': urllib.quote_plus( name ), 'backup_url': urllib.quote_plus( backup_url ) }
			addListItem(label = results['title'].encode('utf-8'), image = thumb, url = u, isFolder = False, infoLabels = infoLabels, fanart = fanart, duration = str(int(results['mediafiles'][0]['length_mseconds'])/1000))
	if topic == 'False':
		play_video( results['title'].encode('utf-8'), url, thumb, results['long_description'].encode('utf-8'), name.encode('utf-8'), None, backup_url )
		return
	if len(data) == 0:
		dialog = xbmcgui.Dialog()
		ok = dialog.ok( plugin , settings.getLocalizedString( 30012 ) + ' ' + name + '.' )
		return
	if ( len(data) ) == 200:
		u = { 'mode': '0', 'name': urllib.quote_plus( name ), 'program_id': urllib.quote_plus( program_id ), 'topic': urllib.quote_plus( topic ), 'page': str( int( page ) + 1 ) }
		addListItem(label = '[Next Page (' + str( int( page ) + 2 ) + ')]', image = next_thumb, url = u, isFolder = True, infoLabels = False, fanart = fanart)
	if topic == 'search':
		build_programs_directory( name, 0 )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_UNSORTED )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_VIDEO_RUNTIME )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_LABEL )
	setViewMode("503")
	xbmcplugin.endOfDirectory( int( sys.argv[1] ) )

def play_video( name, url, thumb, plot, studio, starttime, backup_url ):
	if url == 'None':
		dialog = xbmcgui.Dialog()
		ok = dialog.ok( plugin , settings.getLocalizedString( 30008 ) )
		return
	if url.find('http://urs.pbs.org/redirect/') != -1:
		try:
			import requests
			status = 0
			headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.2; WOW64; rv:17.0) Gecko/20100101 Firefox/17.0'}
			while status <= 10:
				if status != 0: time.sleep(3)
				r = requests.head(url , headers=headers, allow_redirects=False)
				new_url = r.headers['location']
				if new_url != None: break
				status += 1
			infoLabels = { "Title": name , "Studio": "PBS: " + studio, "Plot": plot }
			playListItem(label = name, image = thumb, path = clean(new_url), infoLabels = infoLabels, PlayPath = False)
			return
		except  Exception, e:
			print 'PBS - Using backup_url'
			if backup_url != 'None':
				infoLabels = { "Title": name , "Studio": "PBS: " + studio, "Plot": plot }
				playListItem(label = name, image = thumb, path = clean(backup_url), infoLabels = infoLabels, PlayPath = False)
				return
			else:
				dialog = xbmcgui.Dialog()
				ok = dialog.ok( plugin , settings.getLocalizedString( 30008 ) )
				ok = dialog.ok(plugin, settings.getLocalizedString( 30051 ))
				buggalo.addExtraData('url', url)
				buggalo.addExtraData('error', str(e))
				buggalo.addExtraData('info', studio + ' - ' + name)
				raise Exception("redirect_url ERROR")
				return
	data = getUrl( url + '&format=SMIL' )
	print 'PBS - ' + studio + ' - ' + name
	try:
		print data
	except:
		pass
	try:
		msg = common.parseDOM(data, "ref", ret = "title")[0]
		if msg == 'Unauthorized':
			dialog = xbmcgui.Dialog()
			ok = dialog.ok( plugin , settings.getLocalizedString( 30008 ) )
			return
		if msg == 'Unavailable':
			dialog = xbmcgui.Dialog()
			ok = dialog.ok( plugin , settings.getLocalizedString( 30015 ) + '\n' + settings.getLocalizedString( 30016 ) )
			return
	except:
		print 'PBS - Failed to check video status'
		pass
	try:
		base = re.compile( '<meta base="(.+?)" />' ).findall( data )[0]
	except:
		print 'PBS - Using backup_url'
		if backup_url != 'None':
			infoLabels = { "Title": name , "Studio": "PBS: " + studio, "Plot": plot }
			playListItem(label = name, image = thumb, path = clean(backup_url), infoLabels = infoLabels, PlayPath = False)
			return
		else:
			dialog = xbmcgui.Dialog()
			ok = dialog.ok( plugin , settings.getLocalizedString( 30008 ) )
			ok = dialog.ok(plugin, settings.getLocalizedString( 30051 ))
			buggalo.addExtraData('url', url)
			buggalo.addExtraData('info', studio + ' - ' + name)
			raise Exception("backup_url ERROR")
			return
	src = re.compile( '<ref src="(.+?)" title="(.+?)" (author)?' ).findall( data )[0][0]
	# if src.find('m3u8') != -1:
		# dialog = xbmcgui.Dialog()
		# ok = dialog.ok( plugin , settings.getLocalizedString( 30008 ) )
		# return
	playpath = None
	if base == 'http://ad.doubleclick.net/adx/':
		src_data = src.split( "&lt;break&gt;" )
		rtmp_url = src_data[0] + "mp4:" + src_data[1].replace('mp4:','')
	elif base != 'http://ad.doubleclick.net/adx/' and base.find('http://') != -1:
		infoLabels = { "Title": name , "Studio": "PBS: " + studio, "Plot": plot }
		playListItem(label = name, image = thumb, path = clean(base+src.replace('mp4:','')), infoLabels = infoLabels, PlayPath = False)
		return
	elif src.find('.flv') != -1 or src.find('.mp4') != -1:
		rtmp_url = base + src
	else:
		rtmp_url = base
		playpath = "mp4:" + src.replace('mp4:','')
	if playpath != None:
		listitem.setProperty("PlayPath", playpath)
	infoLabels = { "Title": name , "Studio": "PBS: " + studio, "Plot": plot }
	playListItem(label = name, image = thumb, path = clean( rtmp_url ), infoLabels = infoLabels, PlayPath = playpath)

params = getParameters(sys.argv[2])
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

try:
	if mode == None:
		print plugin + ' ' + __version__ + ' ' + __date__
		if sys.argv[2].startswith('?play='):
			find_videos( 'Video', sys.argv[2][6:].strip(), 'False', page )
		else:
			build_main_directory()
	elif mode == 0:
		find_videos( name, program_id, topic, page )
	elif mode == 1:
		build_programs_directory( name, page )
	elif mode == 2:
		build_topics_directory()
	elif mode == 4:	
		build_search_keyboard()
	elif mode == 5:
		play_video( name, url, thumb, plot, studio, starttime, backup_url )
	elif mode == 6:
		build_search_directory( url, page )
	elif mode == 7:
		infoLabels = { "Title": name , "Studio": "PBS: " + studio, "Plot": plot }
		playListItem(label = name, image = thumb, path = clean(url), infoLabels = infoLabels, PlayPath = False)
except Exception:
	buggalo.onExceptionRaised()
