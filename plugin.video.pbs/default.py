
import xbmc, xbmcgui, xbmcplugin, xbmcaddon, urllib, re, base64, string, sys, os, coveapi, buggalo
import simplejson as json

plugin = "PBS"
__author__ = 'stacked <stacked.xbmc@gmail.com>'
__url__ = 'http://code.google.com/p/plugin/'
__date__ = '01-20-2013'
__version__ = '2.0.10'
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

from addonfunc import addListItem, playListItem, getUrl, setViewMode, getParameters, retry, useragent

try:
	if common.getXBMCVersion() >= 12.0:
		HIGH = 'iPad'
	else:
		HIGH = 'MP4 1200k'
except:
	HIGH = 'MP4 1200k'

def clean( string ):
	list = [( '&amp;', '&' ), ( '&quot;', '"' ), ( '&#39;', '\'' ), ( '\n','' ), ( '\r', ''), ( '\t', ''), ( '</p>', '' ), ( '<br />', ' ' ), 
			( '<br/>', ' ' ), ( '<b>', '' ), ( '</b>', '' ), ( '<p>', '' ), ( '<div>', '' ), ( '</div>', '' ), ( '<strong>', ' ' ), 
			( '<\/strong>', ' ' ), ( '</strong>', ' ' ), ( '&hellip;', '...' ), ( '&ntilde;', 'n' ), ('&ldquo;', '\"'), ('&rdquo;', '\"'),
			('<a href=\"', ''), ('</a>', ''), ('\">', ' ')]
	for search, replace in list:
		string = string.replace( search, replace )
	return string
	
def clean_type( string ):
	if string == None: return 'None'
	list = [( '-16x9', '' ), ( '-4x3', '' ), ( ' 16x9', '' ), ( ' 4x3','' )]
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
					u = { 'mode': '0', 'name': results['title'].encode('utf-8'), 'program_id': program_id }
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
			u = { 'mode': '0', 'name': results['name'], 'topic': 'True' }
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
		u = { 'mode': '0', 'name': clean( program[item_count] ), 'program_id': id.rsplit('/')[4], 'topic': 'False' }
		addListItem(label = clean( title ), image = thumb, url = u, isFolder = False, infoLabels = infoLabels, fanart = fanart)
		item_count += 1	
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_STUDIO )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_LABEL )
	if page == 0:
		build_programs_directory( save_url.replace( '%20', ' ' ), 0 )
	if ( int( video_count[0] ) - ( 10 * int( page ) ) ) > 10:
		u = { 'mode': '6', 'page': str( int( page ) + 1 ), 'url': save_url }
		addListItem(label = '[Next Page (' + str( int( page ) + 2 ) + ')]', image = next_thumb, url = u, isFolder = True, infoLabels = False, fanart = fanart)
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_STUDIO )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_LABEL )
	setViewMode("503")
	xbmcplugin.endOfDirectory( int( sys.argv[1] ) )

@retry(TypeError)
def find_videos( name, program_id, topic, page ):
	if settings.getSetting("quality") == '0':
		type = ['MPEG-4 500kbps', 'MP4 800k', HIGH]
	else:
		type = [HIGH, 'MP4 800k', 'MPEG-4 500kbps' ]
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
		if len(results['mediafiles']) != 0:
			encoding = {}
			if results['associated_images'] != None and len(results['associated_images']) > 0:
				thumb = results['associated_images'][0]['url']
			else:
				thumb = 'None'
			for videos in results['mediafiles']:
				encoding[clean_type(videos['video_encoding']['name'])] = { 'url': videos['video_data_url'], 'backup_url': videos['video_download_url'] }
			cycle = 0
			while cycle <= 2:
				if type[cycle] in encoding:
					url = str(encoding[type[cycle]]['url'])
					backup_url = str(encoding[type[cycle]]['backup_url'])
					break
				cycle += 1
			if cycle == 3:
				url = str(encoding.items()[0][1]['url'])
				backup_url = str(encoding.items()[0][1]['backup_url'])
			infoLabels = { "Title": results['title'].encode('utf-8'), "Director": "PBS", "Studio": name, "Plot": results['long_description'].encode('utf-8'), "Aired": results['airdate'].rsplit(' ')[0], "Duration": str((int(results['mediafiles'][0]['length_mseconds'])/1000)/60) }
			u = { 'mode': '5', 'name': results['title'].encode('utf-8'), 'url': url, 'thumb': thumb, 'plot': results['long_description'].encode('utf-8'), 'studio': name, 'backup_url': backup_url }
			addListItem(label = results['title'].encode('utf-8'), image = thumb, url = u, isFolder = False, infoLabels = infoLabels, fanart = fanart, duration = str(int(results['mediafiles'][0]['length_mseconds'])/1000))
	if topic == 'False':
		play_video( results['title'].encode('utf-8'), url, thumb, results['long_description'].encode('utf-8'), name.encode('utf-8'), None, backup_url )
		return
	if len(data) == 0:
		dialog = xbmcgui.Dialog()
		ok = dialog.ok( plugin , settings.getLocalizedString( 30012 ) + ' ' + name + '.' )
		return
	if ( len(data) ) == 200:
		u = { 'mode': '0', 'name': name, 'program_id': program_id, 'topic': topic, 'page': str( int( page ) + 1 ) }
		addListItem(label = '[Next Page (' + str( int( page ) + 2 ) + ')]', image = next_thumb, url = u, isFolder = True, infoLabels = False, fanart = fanart)
	if topic == 'search':
		build_programs_directory( name, 0 )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_UNSORTED )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_VIDEO_RUNTIME )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_LABEL )
	setViewMode("503")
	xbmcplugin.endOfDirectory( int( sys.argv[1] ) )

def play_video( name, url, thumb, plot, studio, starttime, backup_url ):
	print 'PBS - ' + studio + ' - ' + name
	print url
	playpath = False
	
	#Release Urls
	if 'http://release.theplatform.com/' in url:
		data = getUrl( url + '&format=SMIL' )
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
		try:
			base = re.compile( '<meta base="(.+?)" />' ).findall( data )[0]
			src = re.compile( '<ref src="(.+?)" title="(.+?)" (author)?' ).findall( data )[0][0]
		except:
			print 'PBS - Release backup_url'
			if backup_url != 'None':
				url = backup_url
				backup_url = 'None'
			else:
				url = 'None'
				backup_url = 'None'
		if url != 'None' and 'http://urs.pbs.org/redirect/' not in url:
			if base == 'http://ad.doubleclick.net/adx/':
				src_data = src.split( "&lt;break&gt;" )
				url = src_data[0] + "mp4:" + src_data[1].replace('mp4:','')
			elif base != 'http://ad.doubleclick.net/adx/' and 'http://' in base:
				url = clean(base + src.replace('mp4:',''))
			else:
				url = base
				playpath = "mp4:" + src.replace('mp4:','')
	
	#Empty Urls
	if url == 'None':
		print 'PBS - Empty backup_url'
		if backup_url != 'None':
			url = backup_url
			backup_url = 'None'
		else:
			url = 'None'
			backup_url = 'None'
			
	#Redirect Urls
	if 'http://urs.pbs.org/redirect/' in url:
		redirect = True
		while redirect:
			try:
				content = getUrl( url + '?format=json' )
				query = json.loads(content)
				if query['http_code'] != 302 or query['url'] == None:
					if query['http_code'] == 403:
						dialog = xbmcgui.Dialog()
						ok = dialog.ok( plugin , settings.getLocalizedString( 30015 ) + '\n' + settings.getLocalizedString( 30016 ) )
						return
					else:
						raise Exception("redirect Error")
				if 'mp4:' in query['url']:
					url = query['url'].rsplit('mp4:')[0]
					playpath = 'mp4:' + query['url'].rsplit('mp4:')[1]
				else:
					url = query['url']
				redirect = False
			except Exception, e:
				print str(e)
				print 'PBS - Redirect backup_url'
				if backup_url != 'None':
					if 'http://urs.pbs.org/redirect/' in backup_url:
						redirect = True
					else:
						redirect = False
					url = backup_url
					backup_url = 'None'
				else:
					url = 'None'
					backup_url = 'None'
					redirect = False
				
	#Fails
	if url == 'None' and backup_url == 'None':		
		dialog = xbmcgui.Dialog()
		ok = dialog.ok(plugin , settings.getLocalizedString( 30008 ))
		ok = dialog.ok(plugin, settings.getLocalizedString( 30051 ))
		buggalo.addExtraData('url', url)
		buggalo.addExtraData('info', studio + ' - ' + name)
		raise Exception("backup_url ERROR")
		
	infoLabels = { "Title": name , "Studio": "PBS: " + studio, "Plot": plot }
	playListItem(label = name, image = thumb, path = url, infoLabels = infoLabels, PlayPath = playpath)

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
except Exception:
	buggalo.onExceptionRaised()
