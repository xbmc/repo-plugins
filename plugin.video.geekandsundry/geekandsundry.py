import os, sys, urllib, urllib2, urlparse, re, htmlentitydefs, hashlib, time
import xbmc, xbmcgui, xbmcplugin, xbmcaddon
if sys.version < '2.7.3': #If crappy html.parser, use internal version. Using internal version on ATV2 crashes as of XBMC 12.2, so that's why we test version
	import HTMLParser # @UnusedImport
import bs4  # @UnresolvedImport
ADDON = xbmcaddon.Addon(id='plugin.video.geekandsundry')
__version__ = ADDON.getAddonInfo('version')
T = ADDON.getLocalizedString
CACHE_PATH = xbmc.translatePath(os.path.join(ADDON.getAddonInfo('profile'),'cache'))
FANART_PATH = xbmc.translatePath(os.path.join(ADDON.getAddonInfo('profile'),'fanart'))
if not os.path.exists(CACHE_PATH): os.makedirs(CACHE_PATH)
if not os.path.exists(FANART_PATH): os.makedirs(FANART_PATH)
ADDON_PATH = xbmc.translatePath(ADDON.getAddonInfo('path'))
plugin_fanart = os.path.join(ADDON_PATH,'fanart.jpg')

def LOG(msg):
	print 'plugin.video.geekandsundry: %s' % msg 

def ERROR(msg):
	LOG('ERROR: {0}'.format(msg))
	import traceback
	traceback.print_exc()
	
charCodeFilter = re.compile('&#(\d{1,5});',re.I)
charNameFilter = re.compile('&(\w+?);')
		
def cUConvert(m): return unichr(int(m.group(1)))
def cTConvert(m):
	return unichr(htmlentitydefs.name2codepoint.get(m.group(1),32))
	
def convertHTMLCodes(html):
	try:
		html = charCodeFilter.sub(cUConvert,html)
		html = charNameFilter.sub(cTConvert,html)
	except:
		pass
	return html

def addDir(name,url,mode,iconimage,page=1,tot=0,playable=False,desc='',episode='',fanart=None,context=None,info=None):
	name = convertHTMLCodes(name)
	u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&page="+str(page)
	liz=xbmcgui.ListItem(name, 'test',iconImage="DefaultFolder.png", thumbnailImage=iconimage)
	infolabels={"Title": name,"Episode":episode}
	if info: infolabels.update(info)
	liz.setInfo( type="Video", infoLabels=infolabels )
	if playable: liz.setProperty('IsPlayable', 'true')
	liz.setProperty('fanart_image',fanart or plugin_fanart)
	if context: liz.addContextMenuItems(context)
	return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=not playable,totalItems=tot)

def get_params():
	param=[]
	paramstring=sys.argv[2]
	if len(paramstring)>=2:
		params=sys.argv[2]
		cleanedparams=params.replace('?','')
		if (params[len(params)-1]=='/'):
			params=params[0:len(params)-2]
		pairsofparams=cleanedparams.split('&')
		param={}
		for i in range(len(pairsofparams)):
			splitparams={}
			splitparams=pairsofparams[i].split('=')
			if (len(splitparams))==2:
				param[splitparams[0]]=splitparams[1]
	else:
		param={}					
	return param

def showMain():
	addDir(T(32100),'','newest','logo',fanart='')
	url = 'http://www.geekandsundry.com/'
	html = getCachedHTML('main',url)
	if not html:
		try:
			html = urllib2.urlopen(url).read()
			cacheHTML('main', url, html)
		except:
			ERROR('Failed getting main page')
			xbmc.executebuiltin('Notification(%s,%s,%s,%s)' % ('Geek & Sundry',T(32101),3,ADDON.getAddonInfo('icon')))
			xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')
			return
	nhtml = html.split('<div class="new-shows">',1)[-1].split('<div class="clear">',1)[0]
	ohtml = html.split('<div class="old-shows">',1)[-1].split('<div class="clear">',1)[0]
	items = re.finditer("(?is)<a href='(?P<url>[^\"'>]+)'>.+?<li class=\"[^\"]*show-(?P<status>[\w-]+)\">.+?<img src=\"(?P<logo>[^\"'>]+)\" alt=\"(?P<title>[^\"]+)\".+?<p>(?P<desc>[^<]+)</p>.+?</a>",nhtml+ohtml)
	vlogs = False
	for i in items:
		idict = i.groupdict()
		url = urlparse.urljoin('http:',idict.get('url',''))
		fanart = createFanart(None,url)
		status = idict.get('status').replace('-',' ').title()
		statusdisp = status
		if 'Air' in status:
			statusdisp = '[COLOR green]{0}[/COLOR]'.format(status)
		elif 'Hiatus' in status:
			statusdisp = '[COLOR FFAAAA00]{0}[/COLOR]'.format(status)
		plot = '{0}: [B]{1}[/B][CR][CR]{2}'.format(T(32102),statusdisp,idict.get('desc'))
		mode = 'show'
		if 'vlogs' in url:
			mode = 'vlogs'
			vlogs = True
		addDir(idict.get('title',''),url,mode,idict.get('logo',''),fanart=fanart,info={"Plot":plot,'status':status})
	if not vlogs: addDir('Vlogs','','vlogs',os.path.join(ADDON_PATH,'resources','media','vlogs.png'),fanart='')
	addDir(T(32103),'','all','logo',fanart='')
	xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')

def getSoup(html,default_parser="lxml"):
	try:
		soup = bs4.BeautifulSoup(html, default_parser)
		LOG('Using: %s' % default_parser)
	except:
		soup = bs4.BeautifulSoup(html,"html.parser")
		LOG('Using: html.parser')
	return soup

def showAllShows():
	url = 'http://www.geekandsundry.com/shows/'
	html = getCachedHTML('all',url)
	if not html:
		html = urllib2.urlopen(url).read()
		cacheHTML('all', url, html)
	soup = getSoup(html)
	for a in soup.select('#shows')[0].findAll('a'):
		surl = urlparse.urljoin(url,a.get('href') or '')
		img =  a.find('img')
		if not img: continue
		title = img.get('alt') or ''
		logo = img.get('src') or ''
		fanart = createFanart(None,surl)
		mode = "show"
		if 'vlogs' in surl:
			mode = 'vlogs'
		addDir(title,surl,mode,logo,fanart=fanart,info={"Plot":'','status':''})
	xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')
	return True
	
def showVlogs():
	url = 'http://www.geekandsundry.com/'
	html = getCachedHTML('main',url)
	if not html:
		html = urllib2.urlopen(url).read()
		cacheHTML('main', url, html)
	soup = getSoup(html)
	vlogs = soup.select('.subvlogs')
	if not vlogs: return
	for a in vlogs[0].findAll('a'):
		url = a.get('href') or ''
		li = a.li
		if not li: continue
		icon = li.img.get('src') or ''
		fanart = ''
		try:
			fanart = createFanart(urlparse.urljoin(url,icon),url)
		except:
			LOG(str(sys.exc_info()[1]))
		if not li.span: continue
		title = li.span.string or ''
		addDir(title,url,'show',icon,fanart=fanart,info={"Plot":'','status':''})

def getVlogVideos(html):
	try:
		soup = getSoup(html)
		shows = soup.select('.ui-carousel')
		if not shows: return True
		for li in shows[0].findAll('li'):
			url = li.a.get('href','')
			icon = li.img.get('src','')
			fanart = createFanart(icon,url)
			title = li.h2.string
			ep = extractEpisode(title,icon)
			addDir(title,url,'video',icon,playable=True,episode=ep,fanart=fanart)
		xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
		return True
	except:
		ERROR('getVlogVideos()')
		return False

def showSeason(url):
	if not url: return False
	section,url = url.split(':',1)
	html = getCachedHTML('show',url)
	if not html:
		html = urllib2.urlopen(url).read()
		cacheHTML('show', url, html)
	items = re.finditer("(?is)<li class='episode-item-(?P<section>[^']+)'>\s+?<a href='(?P<url>[^']+)'.+?<img src=\"(?P<thumb>[^\"]*)\".+?<h2>(?P<title>[^<]+)</h2>.+?</li>",html)
	try:
		fanart = 'http://www.geekandsundry.com' + re.search('<div id="show-banner"[^>]*url\(\'(?P<url>[^\']*)\'',html).group(1)
		fanart = createFanart(fanart,url)
	except:
		fanart = None
	for i in items:
		idict = i.groupdict()
		currSection = idict.get('section','')
		if currSection == section:
			ep = extractEpisode(idict.get('title',''),idict.get('thumb',''))
			addDir(idict.get('title',''),url + idict.get('url',''),'video',idict.get('thumb',''),playable=True,episode=ep,fanart=fanart)
	xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
	return True

def showShow(url):
	if not url: return False
	html = getCachedHTML('show',url)
	if not html:
		html = urllib2.urlopen(url).read()
		cacheHTML('show', url, html)
	if 'vlogger' in url: return getVlogVideos(html)
	items = re.finditer("(?is)<li class='episode-item-(?P<section>[^']+)'>\s+?<a href='(?P<url>[^']+)'.+?<img src=\"(?P<thumb>[^\"]*)\".+?<h2>(?P<title>[^<]+)</h2>.+?</li>",html)
	try:
		fanart = urlparse.urljoin('http://www.geekandsundry.com',re.search('<div id="show-banner"[^>]*url\(\'(?P<url>[^\']*)\'',html).group(1))
		fanart = createFanart(fanart,url)
	except:
		fanart = None
	sections = {}
	for i in items:
		idict = i.groupdict()
		section = idict.get('section','')
		if not section in sections:
			sections[section] = 1
			if section.startswith('episode-') or section.startswith('extras-'):
				display = section.split('-',1)[-1]
				num = re.search('\d+$',display)
				if num:
					display = re.sub('\d+$','',display) + ' ' + num.group(0)
				if section.startswith('extras-'): display += ' - {0} '.format(T(32104))
			else:
				display = section.replace('-',' ')
			display = display.title()
			addDir(display,section + ':' + url,'season',idict.get('thumb',''),fanart=fanart)
	xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')
	return True

def showNewest():
	url = 'http://www.youtube.com/user/geekandsundry/videos'
	html = getCachedHTML('newest',url)
	if not html:
		html = urllib2.urlopen(url).read()
		cacheHTML('newest', url, html)
	soup = getSoup(html)
	items = soup.findAll('h3')
	for i in items:
		if not i.get('class'): continue
		a = i.find('a')
		if not a: continue
		
		href = a.get('href') or ''
		ID = href.split('=',1)[-1]
		thumb = 'http://i1.ytimg.com/vi/%s/0.jpg' % ID
		addDir(a.get('title',''),ID,'video_id',thumb,playable=True,episode='',fanart='')
		
	return True
	
def showVideoURL(url):
	if not url: return False
	html = urllib2.urlopen(url).read()
	ID = re.search('(?is)<iframe.+?src="[^"]+?embed/(?P<id>[^/"]+)".+?</iframe>',html).group(1)
	showVideo(ID)
	return True
	
def showVideo(ID):
	url = 'plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=' + ID
	listitem = xbmcgui.ListItem(label='Video', path=url)
	listitem.setInfo(type='Video',infoLabels={"Title": 'Video'})
	xbmcplugin.setResolvedUrl(handle=int(sys.argv[1]), succeeded=True, listitem=listitem)
	return True

def hasPIL():
	try:
		import PIL # @UnresolvedImport @UnusedImport
		return True
	except:
		return False
	
def createFanart(url,page_url):
	if not hasPIL(): return url
	if '/vlogger/' in page_url or '/vlogs/' in page_url:
		outname = page_url.rsplit('/',1)[-1]
	else:
		outname = page_url.rsplit('/',1)[-1] + '.png'
		
	outfile = os.path.join(FANART_PATH,outname)
	if os.path.exists(outfile): return outfile
	if not url: return ''
	workfile = os.path.join(CACHE_PATH,'work.gif')
	urllib.urlretrieve(url, workfile)
	if '/vlogger/' in page_url or '/vlogs/' in page_url:
		try:
			img = tileImage(640,360,workfile)
			img.save(outfile,'PNG')
			return outfile
		except ImportError:
			pass
		except:
			ERROR('')
		return url
	
	try:
		from PIL import Image,ImageOps # @UnresolvedImport
		img = Image.open(workfile).convert('RGB')
		h = img.histogram()
		rgb = tuple([b.index(max(b)) for b in [ h[i*256:(i+1)*256] for i in range(3) ]])
		if img.size[0] == 60:
			img2 = ImageOps.expand(img,border=(580,150),fill=rgb)
		else:
			img2 = ImageOps.expand(img,border=(0,120),fill=rgb)
		img2.save(outfile,'PNG')
		return outfile
	except ImportError:
		pass
	except:
		ERROR('')
	return url
	
def tileImage(w,h,source):
	from PIL import Image # @UnresolvedImport
	source = Image.open(source).convert('RGBA')
	sw,sh = source.size
	target = Image.new('RGBA',(w,h),(0,0,0,255))
	x = 10
	y = 0
	switch = False
	while x < w:
		while y < h:
			nx = x  # @UnusedVariable
			ny = y
			nw = sw
			nh = sh
			paste = source
			if x + sw > w or y + sh > h or y < 0 or x < 0:
				if x + sw > w: nw = sw - (w - x)
				if y + sh > h: nh = sh - (h - y)
				if x < 0: nx = abs(x)  # @UnusedVariable
				if y < 0: ny = abs(y)
				paste = source.copy()
				paste.crop((0,ny,nw,nh))
			target.paste(paste,(x,y),paste)
			y+= sh + 15
		switch = not switch
		if switch:
			y = int(sw/2) * -1
		else:
			y = 0
		x+=sw + 10
	return target
		
def extractEpisode(title,url):
	test = re.search('(?i)(?:ep|#)(\d+)',title)
	if not test: test = re.search('(?i)_E(\d+)\.',url)
	if not test: test = re.search('[_\.]\d*(\d\d)\.',url)
	if test: return test.group(1)
	return ''

def cacheHTML(prefix,url,html):
	fname = prefix + '.' + hashlib.md5(url).hexdigest()
	with open(os.path.join(CACHE_PATH,fname),'w') as f:
		f.write(str(time.time()) + '\n' + html)
		
def getCachedHTML(prefix,url):
	fname = prefix + '.' + hashlib.md5(url).hexdigest()
	path = os.path.join(CACHE_PATH,fname)
	if not os.path.exists(path): return None
	with open(path,'r') as f:
		data = f.read()
		last, html = data.split('\n',1)
	try:
		if time.time() - float(last) > 3600:
			LOG('Cached file expired. Getting new html...')
			return None
	except:
		LOG('Failed to process file cache time')
		return None
	
	LOG('Using cached HTML')
	return html

def doPlugin():
	success = True
	cache = True
	update_dir = False
	
	params=get_params()
	
	mode = params.get('mode')
	url = urllib.unquote_plus(params.get('url',''))
	if not mode:
		showMain()
	elif mode == 'vlogs':
		showVlogs()
	elif mode == 'season':
		success = showSeason(url)
	elif mode == 'show':
		success = showShow(url)
	elif mode == 'video':
		success = showVideoURL(url)
		if success: return
	elif mode == 'video_id':
		success = showVideo(url)
		if success: return
	elif mode == 'newest':
		success = showNewest()
	elif mode == 'all':
		success = showAllShows()
		
	if mode != 9999: xbmcplugin.endOfDirectory(int(sys.argv[1]),succeeded=success,updateListing=update_dir,cacheToDisc=cache)

if __name__ == '__main__':	
	doPlugin()