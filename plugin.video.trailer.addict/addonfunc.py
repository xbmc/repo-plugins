'''
Addon Functions
__author__ = 'stacked <stacked.xbmc@gmail.com>'
__url__ = 'http://code.google.com/p/plugin/'
__date__ = '06-01-2013'
__version__ = '0.0.10'
'''

import xbmc, xbmcgui, xbmcaddon, xbmcplugin, urllib, urllib2, sys, time, datetime, buggalo
from urlparse import urlparse
from os.path import splitext, basename
import random
settings = sys.modules["__main__"].settings
plugin = sys.modules["__main__"].plugin
agents = ['Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.111 Safari/537.36',
             'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:43.0) Gecko/20100101 Firefox/43.0',
             'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko']
useragent = random.choice(agents)             
accept = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
import SimpleDownloader as downloader
downloader = downloader.SimpleDownloader()

def addListItem(label, image, url, isFolder, totalItems, infoLabels = False, fanart = False, duration = False, cm = False):
	listitem = xbmcgui.ListItem(label = label, iconImage = image, thumbnailImage = image)
	if url['mode']:
		u = sys.argv[0] + '?' + urllib.urlencode(url)
	else:
		u = url['url']
	if not isFolder:
		if settings.getSetting('download') == '' or settings.getSetting('download') == 'false':
			if label != '* ' + settings.getLocalizedString( 30030 ) + ' *':
				listitem.setProperty('IsPlayable', 'true')
				if settings.getSetting('playall') == 'true':
					playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
					playlist.add(url = u, listitem = listitem)
	if fanart:
		listitem.setProperty('fanart_image', fanart)
	if cm:
		listitem.addContextMenuItems( cm )
	if infoLabels:
		listitem.setInfo(type = 'video', infoLabels = infoLabels)
		if duration:
			if hasattr(listitem, 'addStreamInfo'):
				listitem.addStreamInfo('video', { 'duration': int(duration) })
			else:
				listitem.setInfo(type = 'video', infoLabels = { 'duration': str(datetime.timedelta(milliseconds=int(duration)*1000)) } )
	ok = xbmcplugin.addDirectoryItem(handle = int(sys.argv[1]), url = u, listitem = listitem, isFolder = isFolder, totalItems = int(totalItems))
	return ok

def playListItem(label, image, path, infoLabels, PlayPath = False):
	listitem = xbmcgui.ListItem(label = label, iconImage = image, thumbnailImage = image, path = path)
	listitem.setInfo(type = 'video', infoLabels = infoLabels)
	if PlayPath: listitem.setProperty('PlayPath', PlayPath)
	xbmcplugin.setResolvedUrl(handle = int(sys.argv[1]), succeeded = True, listitem = listitem)	

def getUrl(url, gzip = False, form_data={}):
	retries = 0
	while retries <= 10:
		data = {'content': None, 'error': None}
		try:
			if retries != 0:
				time.sleep(3)
			data = getPage(url, gzip, form_data)
			if data['content'] != None and data['error'] == None:
				return data['content']
			if data['error'].find('404:') != -1 or data['error'].find('400:') != -1:
				break
		except Exception, e:
			data['error'] = str(e)
		retries += 1
	dialog = xbmcgui.Dialog()
	ret = dialog.yesno(plugin, settings.getLocalizedString( 30050 ), data['error'], '', settings.getLocalizedString( 30052 ), settings.getLocalizedString( 30053 ))
	if ret == False:
		getUrl(url)
	else:
		ok = dialog.ok(plugin, settings.getLocalizedString( 30051 ))
		buggalo.addExtraData('url', url)
		buggalo.addExtraData('error', data['error'])
		raise Exception('getUrl Error')
	
def getPage(url, gzip = False, form_data={}):
	data = {'content': None, 'error': None}
	try:
		req = urllib2.Request(url)
		if form_data:
			form_data = urllib.urlencode(form_data)
			req = urllib2.Request(url, form_data)        
		req.add_header('User-Agent', useragent)
		req.add_header('Accept', accept)
		content = urllib2.urlopen(req)
		if gzip:
			try:
				if content.info()['Content-Encoding'] == 'gzip':
					import gzip, StringIO
					gzip_filehandle = gzip.GzipFile(fileobj=StringIO.StringIO(content.read()))
					html = gzip_filehandle.read()
				else:
					html = content.read()
			except:
				html = content.read()
		else:
			html = content.read()
		content.close()
		try:
			data['content'] = html.decode('utf-8')
			return data
		except:
			data['content'] = html
			return data
	except Exception, e:
		data['error'] = str(e)
		return data
		
def setViewMode(id, type = False):
	if type == False: type = 'episodes'
	if xbmc.getSkinDir() == 'skin.confluence':
		xbmcplugin.setContent(int( sys.argv[1] ), type)
		if settings.getSetting('view') == 'true':
			xbmc.executebuiltin('Container.SetViewMode(' + id + ')')
			
def start_download(name, path):
	try:
		ext = splitext(basename(urlparse(path).path))[1]
	except:
		ext = '.mp4'
	dialog = xbmcgui.Dialog()
	#dir = dialog.browse(0, settings.getLocalizedString( 30059 ), 'files', '', False, False, settings.getSetting('downloadPath'))
	if settings.getSetting('downloadPrompt') == 'true':
		dir = dialog.browse(0, settings.getLocalizedString( 30059 ), 'files')
	else:
		while not settings.getSetting('downloadPath'):
			ok = dialog.ok(plugin, settings.getLocalizedString( 30058 ))
			settings.openSettings()
			if settings.getSetting('downloadPrompt') == 'true':
				dir = dialog.browse(0, 'XBMC', 'files')
				settings.setSetting('downloadPath', dir)
		dir = settings.getSetting('downloadPath')
	if len(dir) == 0:
		return
	params = { "url": path, "download_path": dir, "Title": name }
	downloader.download(clean_file(name) + ext, params)

def clean_file(name):
    remove=[('\"',''),('\\',''),('/',''),(':',' - '),('|',''),('>',''),('<',''),('?',''),('*','')]
    for old, new in remove:
        name=name.replace(old,new)
    return name

#From http://wiki.xbmc.org/index.php?title=Add-on:Parsedom_for_xbmc_plugins 
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

#From http://www.saltycrane.com/blog/2009/11/trying-out-retry-decorator-python/	
def retry(ExceptionToCheck, tries = 10, delay = 3, backoff = 1, logger = None):
    def deco_retry(f):
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            try_one_last_time = True
            while mtries >= -1:
				if mtries == -1:
					dialog = xbmcgui.Dialog()
					ret = dialog.yesno(plugin, settings.getLocalizedString( 30054 ), '', '', settings.getLocalizedString( 30052 ), settings.getLocalizedString( 30053 ))
					if ret == False:
						mtries, mdelay = tries, delay
					else:
						ok = dialog.ok(plugin, settings.getLocalizedString( 30051 ))
						buggalo.addExtraData('error', str(e))
						raise Exception("retry Error")
				try:
					return f(*args, **kwargs)
					try_one_last_time = False
					break
				except ExceptionToCheck, e:
					if mtries >= 1:
						msg = "%s, Retrying in %d seconds..." % (str(e), mdelay)
						if logger:
							logger.warning(msg)
						else:
							xbmc.log(msg, xbmc.LOGERROR)
						time.sleep(mdelay)
						mdelay *= backoff
					mtries -= 1
            if try_one_last_time:
                return f(*args, **kwargs)
            return
        return f_retry 
    return deco_retry
	