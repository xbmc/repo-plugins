
import xbmc, xbmcaddon, xbmcgui, xbmcplugin, urllib2, urllib, re, string, sys, os, traceback, time, datetime, buggalo

plugin = 'TMZ'
__author__ = 'stacked <stacked.xbmc@gmail.com>'
__url__ = 'http://code.google.com/p/plugin/'
__date__ = '10-07-2012'
__version__ = '2.0.5'
settings = xbmcaddon.Addon( id = 'plugin.video.tmz' )
icon = os.path.join( settings.getAddonInfo( 'path' ), 'icon.png' )
buggalo.SUBMIT_URL = 'http://www.xbmc.byethost17.com/submit.php'

def retry(ExceptionToCheck, tries=4, delay=5, backoff=2, logger=None):
    """Retry calling the decorated function using an exponential backoff.

    http://www.saltycrane.com/blog/2009/11/trying-out-retry-decorator-python/
    original from: http://wiki.python.org/moin/PythonDecoratorLibrary#Retry

    :param ExceptionToCheck: the exception to check. may be a tuple of
        excpetions to check
    :type ExceptionToCheck: Exception or tuple
    :param tries: number of times to try (not retry) before giving up
    :type tries: int
    :param delay: initial delay between retries in seconds
    :type delay: int
    :param backoff: backoff multiplier e.g. value of 2 will double the delay
        each retry
    :type backoff: int
    :param logger: logger to use. If None, print
    :type logger: logging.Logger instance
    """
    def deco_retry(f):
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            try_one_last_time = True
            while mtries >= 0:
				if mtries == 0:
					dialog = xbmcgui.Dialog()
					ret = dialog.yesno(plugin, settings.getLocalizedString( 30054 ), nolabel = settings.getLocalizedString( 30052 ), yeslabel = settings.getLocalizedString( 30053 ))
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
        return f_retry  # true decorator
    return deco_retry

def clean( name ):
	remove = [ ('&amp;','&'), ('&quot;','"'), ('&#39;','\''), ('u2013','-'), ('u201c','\"'), ('u201d','\"'), ('u2019','\''), ('u2026','...') ]
	for trash, crap in remove:
		name = name.replace( trash, crap )
	return name

@retry(IndexError)	
def build_main_directory():
	main=[
		( settings.getLocalizedString( 30000 ) ),
		( settings.getLocalizedString( 30001 ) ),
		( settings.getLocalizedString( 30002 ) ),
		( settings.getLocalizedString( 30003 ) )
		]
	for name in main:
		listitem = xbmcgui.ListItem( label = name, iconImage = icon, thumbnailImage = icon )
		u = sys.argv[0] + "?mode=0&name=" + urllib.quote_plus( name )
		ok = xbmcplugin.addDirectoryItem( handle = int( sys.argv[1] ), url = u, listitem = listitem, isFolder = True )
	xbmcplugin.addSortMethod( handle = int(sys.argv[1]), sortMethod = xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( int( sys.argv[1] ) )

@retry(IndexError)
def build_video_directory( name ):
	data = open_url( 'http://www.tmz.com/videos/' )['content']
	content = re.compile('{ name: \'' + name.upper() + '\',( )?\n         allInitialJson: \[(.+?)\],\n', re.DOTALL).findall( data )
	match = re.compile('\n{\n  (.+?)\n}', re.DOTALL).findall( content[0][1] )
	for videos in match:
		epsdata = re.compile('title": "(.+?)",\n  "duration": "(.+?)",\n  "url": "(.+?)",\n  "videoUrl": "(.+?)",\n  "manualThumbnailUrl": "(.+?)",\n  "thumbnailUrl": "(.+?)",\n  "kalturaId": "(.+?)"', re.DOTALL).findall(videos)
		title = clean(epsdata[0][0].replace("\\", ""))
		duration = epsdata[0][1].replace("\\", "")
		videoUrl = epsdata[0][3].replace("\\", "")
		thumb = epsdata[0][5].replace("\\", "") + '/width/490/height/266/type/3'
		if videoUrl.find('http://cdnbakmi.kaltura.com') == -1:
			if settings.getSetting("quality") == settings.getLocalizedString( 30005 ):
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

@retry(IndexError)	
def play_video( name, url, thumb, studio ):
	data = open_url( url )['content']
	url = re.compile('<media url=\"(.+?)\"').findall(data)[0]
	listitem = xbmcgui.ListItem( label = name, iconImage = "DefaultVideo.png", thumbnailImage = thumb, path = url )
	listitem.setInfo( type="Video", infoLabels={ "Title": name , "Director": "TMZ", "Studio": studio } )
	xbmcplugin.setResolvedUrl( handle = int( sys.argv[1] ), succeeded = True, listitem = listitem )
	
def open_url(url):
	retries = 0
	while retries < 4:
		try:
			time.sleep(5*retries)
			data = get_page(url)
			if data['content'] != None and data['error'] == None:
				return data
			else:
				retries += 1
		except:
			retries += 1
	dialog = xbmcgui.Dialog()
	ret = dialog.yesno(plugin, settings.getLocalizedString( 30050 ), data['error'], nolabel = settings.getLocalizedString( 30052 ), yeslabel = settings.getLocalizedString( 30053 ))
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
	