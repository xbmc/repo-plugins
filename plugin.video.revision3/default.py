
import xbmc, xbmcgui, xbmcplugin, xbmcaddon, urllib, re, string, sys, os, time, buggalo, urllib2

plugin =  'Revision3'
__author__ = 'stacked <stacked.xbmc@gmail.com>'
__url__ = 'http://code.google.com/p/plugin/'
__date__ = '09-30-2012'
__version__ = '2.0.10'
settings = xbmcaddon.Addon(id='plugin.video.revision3')
buggalo.SUBMIT_URL = 'http://www.xbmc.byethost17.com/submit.php'
dbg = False
dbglevel = 3
next_thumb = os.path.join( settings.getAddonInfo( 'path' ), 'resources', 'media', 'next.png' )
more_thumb = os.path.join( settings.getAddonInfo( 'path' ), 'resources', 'media', 'more.png' )
downloads_thumb = os.path.join( settings.getAddonInfo( 'path' ), 'resources', 'media', 'downloads.png' )
old_thumb = os.path.join( settings.getAddonInfo( 'path' ), 'resources', 'media', 'old.png' )
current_thumb = os.path.join( settings.getAddonInfo( 'path' ), 'resources', 'media', 'current.png' )
search_thumb = os.path.join( settings.getAddonInfo( 'path' ), 'resources', 'media', 'search.png' )
fanart_bg = os.path.join( settings.getAddonInfo( 'path' ), 'fanart.jpg' )

import CommonFunctions
common = CommonFunctions
common.plugin = plugin + ' ' + __version__

import SimpleDownloader as downloader
downloader = downloader.SimpleDownloader()

def retry(ExceptionToCheck, tries=4, delay=3, backoff=2, logger=None):
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
            while mtries > 1:
                try:
                    return f(*args, **kwargs)
                    try_one_last_time = False
                    break
                except ExceptionToCheck, e:
                    msg = "%s, Retrying in %d seconds..." % (str(e), mdelay)
                    if logger:
                        logger.warning(msg)
                    else:
                        print msg
                    time.sleep(mdelay)
                    mtries -= 1
                    mdelay *= backoff
            if try_one_last_time:
                return f(*args, **kwargs)
            return
        return f_retry  # true decorator
    return deco_retry

@retry(IndexError, tries=4)
def build_main_directory(url):
	path = url
	html = open_url(url)
	shows = common.parseDOM(html, "ul", attrs = { "id": "shows" })[0]
	url_name = re.compile('<h3><a href="(.+?)">(.+?)</a></h3>').findall(shows)
	image = re.compile('class="thumbnail"><img src="(.+?)" /></a>').findall(shows)
	plot = common.parseDOM(shows, "p", attrs = { "class": "description" })
	if settings.getSetting('folder') == 'true' and settings.getSetting( 'downloadPath' ) and path == 'http://revision3.com/shows/':
		infoLabels = { "Title": settings.getLocalizedString( 30012 ), "Plot": settings.getLocalizedString( 30022 ) }
		ListItem('[ ' + settings.getLocalizedString( 30012 ) + ' ]', downloads_thumb, settings.getSetting("downloadPath"), None, True, infoLabels, fanart_bg)
	if path == 'http://revision3.com/shows/':
		infoLabels = { "Title": settings.getLocalizedString( 30013 ), "Plot": settings.getLocalizedString( 30018 ) }
		ListItem('[ ' + settings.getLocalizedString( 30013 ) + ' ]', current_thumb, 'http://revision3.com/episodes/page?&hideArrows=1&type=recent&page=1', '1', True, infoLabels, fanart_bg)
		infoLabels = { "Title": settings.getLocalizedString( 30014 ), "Plot": settings.getLocalizedString( 30019 ) }
		ListItem('[ ' + settings.getLocalizedString( 30014 ) + ' ]', old_thumb, 'http://revision3.com/shows/archive', '3', True, infoLabels, fanart_bg)
		infoLabels = { "Title": settings.getLocalizedString( 30015 ), "Plot": settings.getLocalizedString( 30020 ) }
		ListItem('[ ' + settings.getLocalizedString( 30015 ) + ' ]', search_thumb, 'search', '4', True, infoLabels, fanart_bg)
	count = 0
	for url, name in url_name:
		fanart = url.replace('/','')
		if not settings.getSetting(fanart):
			fanart = fanart_bg
		else:
			fanart = settings.getSetting(fanart)
		url = 'http://revision3.com' + url + '/episodes'
		infoLabels = { "Title": name, "Plot": clean(plot[count]) }
		ListItem(name, image[count].replace('160x160','200x200'), url, '1', True, infoLabels, fanart)
		count += 1
	xbmcplugin.addSortMethod( handle = int(sys.argv[ 1 ]), sortMethod = xbmcplugin.SORT_METHOD_UNSORTED )
	xbmcplugin.setContent(int( sys.argv[1] ), 'episodes')
	setViewMode("515")
	xbmcplugin.endOfDirectory(int(sys.argv[1]))

@retry(IndexError, tries=4)
def build_sub_directory(url, name):
	saveurl = url
	studio = name
	savestudio = name
	html = open_url(url)
	ret = common.parseDOM(html, "div", attrs = { "id": "main-episodes" })
	pageLoad = common.parseDOM(ret, "a", ret = "onclick")
	if len(ret) == 0:
		ret = common.parseDOM(html, "div", attrs = { "id": "all-episodes" })
		pageLoad = common.parseDOM(ret, "a", ret = "onclick")
	if len(ret) == 0:
		ret = common.parseDOM(html, "ul", attrs = { "class": "episode-grid" })
		pageLoad = common.parseDOM(html, "a", ret = "onclick")
	current = common.parseDOM(html, "span", attrs = { "class": "active" })
	episodes = common.parseDOM(ret, "li", attrs = { "class": "episode item" })
	img = common.parseDOM(episodes[0], "img", ret = "src")[0]
	if not '[ ' + settings.getLocalizedString( 30013 ) + ' ]' == name:
		try:
			downloads = 'http://revision3.com/' + img.rsplit('/')[6] + '/' + img.rsplit('/')[6] + '_downloads'
			fresult = get_page(downloads)
			if fresult == 'error':
				raise Exception("build_sub_directory ERROR")
			data = re.compile( '<a href="(.+?)" target="_blank">1920x1200</a>' ).findall(fresult)
			if len(data) > 1:
				fanart = data[1]
			else:
				fanart = data[0]
			settings.setSetting(img.rsplit('/')[6], fanart)
		except:
			fanart = 'http://statics.revision3.com/_/images/shows/' + img.rsplit('/')[6] + '/show_background.jpg'
			if get_page(fanart) == 'error':
				settings.setSetting(img.rsplit('/')[6], fanart_bg)
			else:
				settings.setSetting(img.rsplit('/')[6], fanart)		
	try:
		child = common.parseDOM(html, "div", attrs = { "id": "child-episodes" })
		label = common.parseDOM(html, "a", attrs = { "href": "#child-episodes" })[0]
		childshow = common.parseDOM(child, "a", attrs = { "class": "thumbnail" }, ret = "href" )[0].rsplit('/')[1]
		csaveurl = 'http://revision3.com/' + childshow + '/episodePage?type=recent&limit=15&hideShow=1&hideArrows=1&page=1'
		infoLabels = { "Title": label, "Plot": label }
		ListItem('[ ' + label + ' ]', more_thumb, csaveurl, '1', True, infoLabels, fanart, studio)
	except:
		pass
	try:
		strs = 'http://revision3.com' + pageLoad[-1:][0].rsplit('\'')[1]
		params = common.getParameters(strs)
		saveurl = strs.rstrip('&page=' + params['page']) + '&page=' + str( int(current[0]) + 1 )
		if int(params['page']) > int(current[0]):
			next = True
		else:
			next = False
	except:
		next = False
	for data in episodes:
		thumb = common.parseDOM(data, "img", ret = "src")[0].replace('small.thumb','medium.thumb')
		show_id = thumb.split('/')[6]
		if not settings.getSetting(show_id):
			fanart = fanart_bg
		else:
			fanart = settings.getSetting(show_id)
		plot = clean(common.parseDOM(data, "img", ret = "alt")[0])
		name = clean(common.stripTags(common.parseDOM(data, "a")[1]))
		cut = common.parseDOM(data, "a")[1]
		try:
			studio = clean(common.parseDOM(cut, "strong")[0])
		except:
			pass
		name = name.replace(studio + '   ','')
		url = 'http://revision3.com' + common.parseDOM(data, "a", attrs = { "class": "thumbnail" }, ret = "href")[0]
		try:
			episode = name.rsplit(' ')[1]
			date = name.rsplit(' ')[3].rsplit('/')[2] + '-'  + name.rsplit(' ')[3].rsplit('/')[0] + '-' + name.rsplit(' ')[3].rsplit('/')[1]
		except:
			episode = '0'
			date = '0000-00-00'
		duration = name[-6:].rstrip(')').replace('(','')
		infoLabels = { "Title": plot, "Studio": studio, "Plot": plot, "Episode": int(episode), "Aired": date, "Duration": duration }
		ListItem(plot, thumb, url, '2', False, infoLabels, fanart)
	if next == True:
		infoLabels = { "Title": settings.getLocalizedString( 30016 ), "Plot": settings.getLocalizedString( 30016 ) }
		ListItem(settings.getLocalizedString( 30016 ) + ' (' + str( int(current[0]) + 1 ) + ')', next_thumb, saveurl, '1', True, infoLabels, fanart_bg, savestudio)
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_UNSORTED )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_EPISODE )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_STUDIO )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_VIDEO_RUNTIME )
	xbmcplugin.setContent(int( sys.argv[1] ), 'episodes')
	setViewMode("503")
	xbmcplugin.endOfDirectory(int(sys.argv[1]))
	
@retry(IndexError, tries=4)
def get_video(url, name, plot, studio, episode, thumb, date):
	result = open_url(url)
	video_id = re.compile('player\.loadRevision3Item\(\'video_id\',(.+?)\);').findall(result)[0].replace(' ','')
	api = open_url('http://revision3.com/api/flash?video_id=' + video_id)
	videos_api = common.parseDOM(api, "media", ret = "type")
	videos_api[:] = (value for value in videos_api if value != 'thumbnail')
	durl = {}
	for type_api in videos_api:
		content_api = clean(common.parseDOM(api, "media", attrs = { "type": type_api })[0])
		durl[type_api] = content_api
	list = ['MP4','Quicktime','Xvid','WMV','Unknown File Type']
	for type in list:
		content = common.parseDOM(result, "div", attrs = { "id": "action-panels-download-" + type })
		videos = common.parseDOM(content, "a", attrs = { "class": "sizename" })
		links = common.parseDOM(content, "a", attrs = { "class": "sizename" }, ret="href")
		count = 0
		for add in videos:
			if type == 'Unknown File Type':
				code = type
			else:
				code = type + ':' + add
			durl[code] = links[count]
			count += 1
	dictList = [] 
	for key, value in durl.iteritems():
		dictList.append(key)
	quality = settings.getSetting('type')
	try:
		try:
			purl = durl[quality]
		except:
			if quality == 'MP4:HD':
				if 'Quicktime:HD' in durl:
					quality_api = 'Quicktime:HD'
				else:
					quality_api = 'hd'
			if quality == 'MP4:Large':
				if 'Quicktime:Large' in durl:
					quality_api = 'Quicktime:Large'
				else:
					quality_api = 'high'
			if quality == 'MP4:Phone':
				quality_api = 'low'
			purl = durl[quality_api]
		ret = None
	except:
		dialog = xbmcgui.Dialog()
		ret = dialog.select(settings.getLocalizedString( 30017 ), dictList)
		purl = durl[dictList[ret]]
	if ret != -1:
		if settings.getSetting('download') == 'true':
			while not settings.getSetting('downloadPath'):
				if settings.getSetting('download') == 'false':
					xbmc.executebuiltin("Container.Refresh")
					return
				dialog = xbmcgui.Dialog()
				ok = dialog.ok(plugin, settings.getLocalizedString( 30011 ))
				settings.openSettings()
			params = { "url": purl, "download_path": settings.getSetting('downloadPath'), "Title": name }
			downloader.download(clean_file(name) + '.' + purl.split('/')[-1].split('.')[-1], params)
		else:
			listitem = xbmcgui.ListItem(label = name , iconImage = 'DefaultVideo.png', thumbnailImage = thumb, path = purl)
			listitem.setInfo( type = "Video", infoLabels={ "Title": name, "Studio": studio, "Plot": plot, "Episode": int(episode), "Aired": date  } )
			xbmcplugin.setResolvedUrl( handle = int( sys.argv[1] ), succeeded = True, listitem = listitem )

@retry(IndexError, tries=4)
def build_search_directory(url):
	if url == 'search':
		try:
			search = common.getUserInput("Enter search term", "").replace(' ','+')
			url = 'http://revision3.com/search/page?type=video&q=' + search + '&limit=10&page=1'
		except:
			return
	html = open_url(url)
	current = common.parseDOM(html, "span", attrs = { "class": "active" })
	pageLoad = common.parseDOM(html, "a", ret = "onclick")
	try:
		strs = 'http://revision3.com' + pageLoad[-1:][0].rsplit('\'')[1]
		params = common.getParameters(strs)
		saveurl = strs.rstrip('&page=' + params['page']) + '&page=' + str( int(current[0]) + 1 )
		if int(params['page']) > int(current[0]):
			next = True
		else:
			next = False
	except:
		next = False
	episodes = common.parseDOM(html, "li", attrs = { "class": "video" })
	if len(episodes) == 0:
		dialog = xbmcgui.Dialog()
		ok = dialog.ok( plugin , settings.getLocalizedString( 30009 ) + '\n' + settings.getLocalizedString( 30010 ) )
		return
	for data in episodes:
		thumb = common.parseDOM(data, "img", ret = "src")[0]
		url = common.parseDOM(data, "a", attrs = { "class": "thumbnail" }, ret = "href" )[0]
		url = clean(url.replace('http://www.videosurf.com/webui/inc/go.php?redirect=','')).replace('&client_id=revision3','')
		title = clean(common.parseDOM(data, "a", attrs = { "class": "title" })[0])
		plot = clean(common.stripTags(common.parseDOM(data, "div", attrs = { "class": "description" })[0]))
		try:
			studio = title.rsplit(' - ')[1]
		except:
			studio = plugin
		infoLabels = { "Title": title, "Studio": studio, "Plot": plot, "Episode": 0, "Aired": "0000-00-00" }
		ListItem(title, thumb, url, '2', False, infoLabels, fanart_bg)
	if next == True:
		infoLabels = { "Title": settings.getLocalizedString( 30016 ), "Plot": settings.getLocalizedString( 30016 ) }
		ListItem(settings.getLocalizedString( 30016 ) + ' (' + str( int(current[0]) + 1 ) + ')', next_thumb, saveurl, '4', True, infoLabels, fanart_bg, studio)
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_UNSORTED )
	xbmcplugin.setContent(int( sys.argv[1] ), 'episodes')
	setViewMode("503")
	xbmcplugin.endOfDirectory(int(sys.argv[1]))
	
def ListItem(label, image, url, mode, isFolder, infoLabels = False, fanart = False, name = False):
	listitem = xbmcgui.ListItem(label = label, iconImage = image, thumbnailImage = image)
	if fanart:
		listitem.setProperty('fanart_image', fanart)
	if infoLabels:
		listitem.setInfo( type = "Video", infoLabels = infoLabels )
	if not isFolder:
		if settings.getSetting('download') == 'false':
			listitem.setProperty('IsPlayable', 'true')
	if mode:
		if name:
			label = name
		if mode == '2':
			u = sys.argv[0] + "?mode=2&name=" + urllib.quote_plus(label) + "&url=" + urllib.quote_plus(url) + "&plot=" + urllib.quote_plus(infoLabels['Plot'].encode('ascii', 'ignore')) + "&studio=" + urllib.quote_plus(infoLabels['Studio']) + "&episode=" + urllib.quote_plus(str(infoLabels['Episode'])) + "&thumb=" + urllib.quote_plus(image) + "&date=" + urllib.quote_plus(infoLabels['Aired'])
		else:
			u = sys.argv[0] + "?mode=" + mode + "&name=" + urllib.quote_plus(label) + "&url=" + urllib.quote_plus(url) + "&thumb=" + urllib.quote_plus(image)
	else:
		u = url
	ok = xbmcplugin.addDirectoryItem(handle = int(sys.argv[1]), url = u, listitem = listitem, isFolder = isFolder)
	return ok
	
def open_url(url):
	retries = 0
	while retries < 4:
		try:
			time.sleep(5*retries)
			data = get_page(url)
			if len(data) > 0 and data != 'error':
				return data
			else:
				retries += 1
		except:
			retries += 1
	buggalo.addExtraData('url', url)
	dialog = xbmcgui.Dialog()
	ok = dialog.ok(plugin, settings.getLocalizedString( 30023 ) + '\n' + settings.getLocalizedString( 30024 ))
	raise Exception("open_url ERROR")
	
def get_page(url):
	try:
		req = urllib2.Request(url)
		req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:15.0) Gecko/20100101 Firefox/15.0.1')
		content = urllib2.urlopen(req)
		data = content.read()
		content.close()
		try:
			return data.decode("utf-8")
		except:
			return data
	except Exception, e:
		buggalo.addExtraData('error', str(e))
		return 'error'
	
def setViewMode(id):
	if xbmc.getSkinDir() == "skin.confluence" and settings.getSetting('view') == 'true':
		xbmc.executebuiltin("Container.SetViewMode(" + id + ")")

def clean(name):
	remove = [('&amp;','&'), ('&quot;','"'), ('&#039;','\''), ('\r\n',' '), ('\n',' '), ('&apos;','\''), ('&#150;','-'), ('%3A',':'), ('%2F','/'), ('<link>',''), ('</link>','')]
	for trash, crap in remove:
		name = name.replace(trash,crap)
	return name
	
def clean_file(name):
    remove=[('\"',''),('\\',''),('/',''),(':',' - '),('|',''),('>',''),('<',''),('?',''),('*','')]
    for old, new in remove:
        name=name.replace(old,new)
    return name

params = common.getParameters(sys.argv[2])
url = None
name = None
mode = None
plot = None
studio = None
episode = None
thumb = None
date = None

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
	plot = urllib.unquote_plus(params["plot"])
except:
	pass
try:
	studio = urllib.unquote_plus(params["studio"])
except:
	pass
try:
	episode = int(params["episode"])
except:
	pass
try:
	thumb = urllib.unquote_plus(params["thumb"])
except:
	pass
try:
	date = urllib.unquote_plus(params["date"])
except:
	pass

try:
	if mode == None:
		url = 'http://revision3.com/shows/'
		build_main_directory(url)
	elif mode == 1:
		build_sub_directory(url, name)
	elif mode == 2:
		get_video(url, name, plot, studio, episode, thumb, date)
	elif mode == 3:
		build_main_directory(url)
	elif mode == 4:
		build_search_directory(url)
except Exception:
	buggalo.onExceptionRaised()
