'''
Addon Functions
date: 12-29-2012
version: 0.0.2
'''

import xbmc, xbmcgui, xbmcaddon, xbmcplugin, urllib2, sys, time, datetime, buggalo
settings = sys.modules["__main__"].settings
plugin = sys.modules["__main__"].plugin
useragent = 'Mozilla/5.0 (Windows NT 6.2; WOW64; rv:17.0) Gecko/20100101 Firefox/17.0'

def addListItem(label, image, url, isFolder, infoLabels = False, fanart = False, duration = False):
	listitem = xbmcgui.ListItem(label = label, iconImage = image, thumbnailImage = image)
	if not isFolder: listitem.setProperty('IsPlayable', 'true')
	if fanart: listitem.setProperty('fanart_image', fanart)
	if infoLabels:
		listitem.setInfo(type = 'video', infoLabels = infoLabels)
		if duration:
			if hasattr(listitem, 'addStreamInfo'):
				listitem.addStreamInfo('video', { 'duration': int(duration) })
			else:
				listitem.setInfo(type = 'video', infoLabels = { 'duration': str(datetime.timedelta(milliseconds=int(duration)*1000)) } )
	u = sys.argv[0] + '?'
	for key, value in url.items():
		u += key + '=' + value + '&'
	ok = xbmcplugin.addDirectoryItem(handle = int(sys.argv[1]), url = u, listitem = listitem, isFolder = isFolder)
	return ok

def playListItem(label, image, path, infoLabels, PlayPath = False):
	listitem = xbmcgui.ListItem(label = label, iconImage = image, thumbnailImage = image, path = path)
	listitem.setInfo(type = 'video', infoLabels = infoLabels)
	if PlayPath: listitem.setProperty('PlayPath', PlayPath)
	xbmcplugin.setResolvedUrl(handle = int(sys.argv[1]), succeeded = True, listitem = listitem)	

def getUrl(url, gzip = False):
	retries = 0
	while retries <= 10:
		data = {'content': None, 'error': None}
		try:
			if retries != 0:
				time.sleep(3)
			data = getPage(url, gzip)
			if data['content'] != None and data['error'] == None:
				return data['content']
			if data['error'].find('404:') != -1:
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
	
def getPage(url, gzip = False):
	data = {'content': None, 'error': None}
	try:
		req = urllib2.Request(url)
		req.add_header('User-Agent', useragent)
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
		
def setViewMode(id):
	if xbmc.getSkinDir() == 'skin.confluence':
		xbmcplugin.setContent(int( sys.argv[1] ), 'episodes')
		xbmc.executebuiltin('Container.SetViewMode(' + id + ')')

#From CommonFunctions.py in parsedom 
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

#Original from http://www.saltycrane.com/blog/2009/11/trying-out-retry-decorator-python/	
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
							print msg
						time.sleep(mdelay)
						mdelay *= backoff
					mtries -= 1
            if try_one_last_time:
                return f(*args, **kwargs)
            return
        return f_retry 
    return deco_retry
	