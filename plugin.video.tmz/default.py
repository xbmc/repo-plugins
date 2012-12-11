
import xbmc, xbmcaddon, xbmcgui, xbmcplugin, urllib2, urllib, re, string, sys, os, traceback, time, datetime, buggalo, gzip, StringIO
import simplejson as json

plugin = 'TMZ'
__author__ = 'stacked <stacked.xbmc@gmail.com>'
__url__ = 'http://code.google.com/p/plugin/'
__date__ = '12-10-2012'
__version__ = '2.0.9'
settings = xbmcaddon.Addon( id = 'plugin.video.tmz' )
dbg = False
dbglevel = 3
icon = os.path.join( settings.getAddonInfo( 'path' ), 'icon.png' )
fanart_bg = os.path.join( settings.getAddonInfo( 'path' ), 'fanart.jpg' )
buggalo.SUBMIT_URL = 'http://www.xbmc.byethost17.com/submit.php'

import CommonFunctions
common = CommonFunctions
common.plugin = plugin + ' ' + __version__

def retry(ExceptionToCheck, tries=11, delay=3, backoff=1, logger=None):
    def deco_retry(f):
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            try_one_last_time = True
            while mtries >= 0:
				if mtries == 0:
					dialog = xbmcgui.Dialog()
					ret = dialog.yesno(plugin, settings.getLocalizedString( 30054 ), '', '', settings.getLocalizedString( 30052 ), settings.getLocalizedString( 30053 ))
					if ret == False:
						mtries, mdelay = tries, delay
					else:
						ok = dialog.ok(plugin, settings.getLocalizedString( 30051 ))
						raise Exception("retry ERROR")
				try:
					return f(*args, **kwargs)
					try_one_last_time = False
					break
				except ExceptionToCheck, e:
					if mtries > 1:
						msg = "%s, Retrying in %d seconds..." % (str(e), mdelay)
						if logger:
							logger.warning(msg)
						else:
							print msg
						time.sleep(mdelay)
						mdelay *= backoff
					mtries -= 1
            if try_one_last_time:
                return f(*args, **kwargs)
            return
        return f_retry 
    return deco_retry

def clean( name ):
	remove = [ ('&amp;','&'), ('&quot;','"'), ('&#39;','\''), ('u2013','-'), ('u201c','\"'), ('u201d','\"'), ('u2019','\''), ('u2026','...') ]
	for trash, crap in remove:
		name = name.replace( trash, crap )
	return name

@retry(IndexError)	
def build_main_directory():
	main=[
		( settings.getLocalizedString( 30007 ), '2' ),
		( settings.getLocalizedString( 30000 ), '0' ),
		( settings.getLocalizedString( 30001 ), '0' ),
		( settings.getLocalizedString( 30002 ), '0' ),
		( settings.getLocalizedString( 30003 ), '0' )
		]
	for name, mode in main:
		ListItem(name, icon, '', mode, True, False, True)
	xbmcplugin.addSortMethod( handle = int(sys.argv[1]), sortMethod = xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.setContent(int( sys.argv[1] ), 'episodes')
	setViewMode("515")
	xbmcplugin.endOfDirectory( int( sys.argv[1] ) )

@retry(IndexError)
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
			if settings.getSetting("quality") == '0':
				url = 'http://cdnapi.kaltura.com/p/' + thumb.split('/')[4] + '/sp/' + thumb.split('/')[6] + '/playManifest/entryId/' + videoUrl.split('_')[0].split('/')[-1:][0] + '_' + videoUrl.split('_')[1]
			else:
				url = 'http://cdnapi.kaltura.com/p/' + thumb.split('/')[4] + '/sp/' + thumb.split('/')[6] + '/playManifest/entryId/' + videoUrl.split('_')[0].split('/')[-1:][0] + '_' + videoUrl.split('_')[1] + '/flavorId/0_' + videoUrl.split('_')[3]
			infoLabels = { "Title": title, "Director": "TMZ", "Studio": name, "Plot": title, "Duration": str(datetime.timedelta(seconds=int(duration))) }
			ListItem(title, thumb, url, '1', False, infoLabels, True)
	xbmcplugin.addSortMethod( handle = int(sys.argv[1]), sortMethod = xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.setContent(int( sys.argv[1] ), 'episodes')
	setViewMode("503")
	xbmcplugin.endOfDirectory( int( sys.argv[1] ) )

@retry(IndexError)	
def build_search_directory():
	page = 1
	checking = True
	string = common.getUserInput(settings.getLocalizedString( 30007 ), "")
	if not string:
		return
	while checking:
		url = 'http://www.tmz.com/search/json/videos/' + urllib.quote(string) + '/' + str(page) + '.json'
		data = get_page(url)
		if data['error'] == 'HTTP Error 404: Not Found':
			dialog = xbmcgui.Dialog()
			ok = dialog.ok( plugin , settings.getLocalizedString( 30009 ) + '\n' + settings.getLocalizedString( 30010 ) )
			return
		elif data['error'] != None:
			text = open_url( url )
		else:
			text = data['content']
		jdata = json.loads(text)
		total = int(jdata['total'])
		count = int(jdata['count'])
		if ((total - page * 25) > 0):
			page = page + 1
		else:
			checking = False
		for results in jdata['results']:
			title = results['title'].encode('ascii', 'ignore')
			videoUrl = results['URL'].replace("\\", "")
			thumb = results['thumbnailUrl'].replace("\\", "") + '/width/490/height/266/type/3'
			infoLabels = { "Title": title, "Director": "TMZ", "Plot": title }
			ListItem(title, thumb, videoUrl, '3', False, infoLabels, True)
	xbmcplugin.addSortMethod( handle = int(sys.argv[1]), sortMethod = xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.setContent(int( sys.argv[1] ), 'episodes')
	setViewMode("503")
	xbmcplugin.endOfDirectory( int( sys.argv[1] ) )

@retry(IndexError)	
def get_search_url(name, url, thumb):
	if settings.getSetting("quality") == '0' or len(url.split('/')[4]) > 10:
		meta = 'http://cdnapi.kaltura.com/p/' + thumb.split('/')[4] + '/sp/' + thumb.split('/')[6] + '/playManifest/entryId/' + thumb.split('/')[9]
		data = open_url( meta )
		url = re.compile('<media url=\"(.+?)\"').findall(data)[0]
	else:
		data = open_url( url )
		url = common.parseDOM(data, "meta", attrs = { "name": "VideoURL" }, ret = "content")[0]
	play_video( name, url, thumb, 'TMZ' )

@retry(IndexError)	
def play_video( name, url, thumb, studio ):
	if studio != 'TMZ':
		try:
			data = open_url( url )
			url = re.compile('<media url=\"(.+?)\"').findall(data)[0]
		except:
			url = 'http://www.tmz.com/videos/' + url.split('/')[9]
			data = open_url( url )
			url = common.parseDOM(data, "meta", attrs = { "name": "VideoURL" }, ret = "content")[0]
	listitem = xbmcgui.ListItem( label = name, iconImage = "DefaultVideo.png", thumbnailImage = thumb, path = url )
	listitem.setInfo( type="Video", infoLabels={ "Title": name , "Director": "TMZ", "Studio": studio, "Plot": name } )
	xbmcplugin.setResolvedUrl( handle = int( sys.argv[1] ), succeeded = True, listitem = listitem )

def ListItem(label, image, url, mode, isFolder, infoLabels = False, fanart = False):
	listitem = xbmcgui.ListItem(label = label, iconImage = image, thumbnailImage = image)
	if fanart:
		listitem.setProperty('fanart_image', fanart_bg)
	if infoLabels:
		listitem.setInfo( type = "Video", infoLabels = infoLabels )
	if not isFolder:
		listitem.setProperty('IsPlayable', 'true')
	if mode == '1':
		u = sys.argv[0] + "?mode=1&name=" + urllib.quote_plus(label) + "&url=" + urllib.quote_plus(url) + "&studio=" + urllib.quote_plus(infoLabels['Studio']) + "&thumb=" + urllib.quote_plus(image)
	elif mode == '3':
		u = sys.argv[0] + "?mode=3&name=" + urllib.quote_plus(label) + "&url=" + urllib.quote_plus(url) + "&thumb=" + urllib.quote_plus(image)
	else:
		u = sys.argv[0] + "?mode=" + mode + "&name=" + urllib.quote_plus(label)
	ok = xbmcplugin.addDirectoryItem(handle = int(sys.argv[1]), url = u, listitem = listitem, isFolder = isFolder)
	return ok
	
def open_url(url):
	retries = 0
	while retries < 11:
		data = {'content': None, 'error': None}
		try:
			if retries != 0:
				time.sleep(3)
			data = get_page(url)
			if data['content'] != None and data['error'] == None:
				return data['content']
			if data['error'] == 'HTTP Error 404: Not Found':
				break
		except Exception, e:
			data['error'] = str(e)
		retries += 1
	dialog = xbmcgui.Dialog()
	ret = dialog.yesno(plugin, settings.getLocalizedString( 30050 ), data['error'], '', settings.getLocalizedString( 30052 ), settings.getLocalizedString( 30053 ))
	if ret == False:
		open_url(url)
	else:
		ok = dialog.ok(plugin, settings.getLocalizedString( 30051 ))
		buggalo.addExtraData('url', url)
		buggalo.addExtraData('error', data['error'])
		raise Exception("open_url ERROR")
	
def get_page(url):
	data = {'content': None, 'error': None}
	try:
		req = urllib2.Request(url)
		req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:15.0) Gecko/20100101 Firefox/15.0.1')
		content = urllib2.urlopen(req)
		try:
			if content.info()['Content-Encoding'] == 'gzip':
				gzip_filehandle = gzip.GzipFile(fileobj=StringIO.StringIO(content.read()))
				html = gzip_filehandle.read()
			else:
				html = content.read()
		except:
			html = content.read()
		content.close()
		try:
			data['content'] = html.decode("utf-8")
			return data
		except:
			data['content'] = html
			return data
	except Exception, e:
		data['error'] = str(e)
		return data
		
def setViewMode(id):
	if xbmc.getSkinDir() == "skin.confluence" and settings.getSetting('view') == 'true':
		xbmc.executebuiltin("Container.SetViewMode(" + id + ")")

def getParameters(parameterString):
    commands = {}
    splitCommands = parameterString[parameterString.find('?') + 1:].split('&')
    for command in splitCommands:
        if (len(command) > 0):
            splitCommand = command.split('=')
            key = splitCommand[0]
            value = splitCommand[1]
            commands[key] = value
    return commands

params = getParameters(sys.argv[2])
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
	elif mode == 2:
		build_search_directory()
	elif mode == 3:
		get_search_url(name, url, thumb)
except Exception:
	buggalo.onExceptionRaised()
	