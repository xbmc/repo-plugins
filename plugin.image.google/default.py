#!/usr/bin/python

#This import first for Boxee compatability via my xbmcaddon module for Boxee
import xbmcaddon #@UnresolvedImport

import sys, urllib, urllib2, urlparse, re, time, os, random
import xbmc, xbmcgui, xbmcplugin
import BeautifulSoup # @UnresolvedImport
import htmlentitydefs

__plugin__ =  'google'
__author__ = 'ruuk'
__url__ = 'http://code.google.com/p/googleImagesXBMC/'
__date__ = '12-06-2012'
__settings__ = xbmcaddon.Addon(id='plugin.image.google')
__version__ = __settings__.getAddonInfo('version')
__language__ = __settings__.getLocalizedString

DEBUG = False

CACHE_PATH = os.path.join(xbmc.translatePath(__settings__.getAddonInfo('profile')),'cache')
HISTORY_PATH = os.path.join(xbmc.translatePath(__settings__.getAddonInfo('profile')),'history')
IMAGE_PATH = os.path.join(xbmc.translatePath(__settings__.getAddonInfo('path')),'resources','images')

if not os.path.exists(CACHE_PATH): os.makedirs(CACHE_PATH)

def LOG(msg):
	print 'GoogleImages: {0}'.format(msg)
	
def ERROR(message):
	LOG('ERROR: ' + message)
	import traceback
	traceback.print_exc()

LOG('Version: {0}'.format(__version__))

def cUConvert(m): return unichr(int(m.group(1)))
def cTConvert(m): return unichr(htmlentitydefs.name2codepoint.get(m.group(1),32))

def convertHTMLCodes(html):
	try:
		html = re.sub('&#(\d{1,5});',cUConvert,html.decode('utf-8','replace'))
		html = re.sub('&(\w+?);',cTConvert,html)
	except:
		ERROR('convertHTMLCodes()')
	return html

class googleImagesAPI:
	baseURL = 'https://www.google.com/search?hl=en&site=imghp&tbm=isch{start}{query}'
	perPage = 20
	
	def __init__(self):
		self.lastSearchTotal = '?'
		
	def lastTerms(self,terms=None):
		if not terms: return __settings__.getSetting('last_terms')
		__settings__.setSetting('last_terms',terms)
		
	def createQuery(self,terms,**kwargs):
		self.lastTerms(terms.lower())
		args = ['q={0}'.format(urllib.quote_plus(terms))]
		for k in kwargs.keys():
			if kwargs[k]: args.append('{0}={1}'.format(k,kwargs[k]))
		return '&'.join(args)
		
	def parseQuery(self,query):
		return dict(urlparse.parse_qsl(query))
	
	def parseImages(self,html):
		soup = BeautifulSoup.BeautifulSoup(html)
		self.lastSearchTotal = '?'
		totDiv = soup.find("div", { "id" : "resultStats" })
		if totDiv:
			try:
				#<div id="resultStats">About 69,300,000 results</div>
				self.lastSearchTotal = re.findall('\s([\d,]+)\s',totDiv.string)[-1]
			except:
				pass
			
		results = []
		for td in soup.findAll('td'):
			if td.find('td'): continue
			br = td.find('br')
			if br: br.extract()
			cite = td.find('cite')
			site = ''
			if cite:
				site = cite.string
				cite.extract()
			i = td.find('a')
			if not i: continue
			if i.text or not '/url?q' in i.get('href',''): continue
			for match in soup.findAll('b'):
				match.string = '[COLOR FF00FF00][B]{0}[/B][/COLOR]'.format(str(match.string))
				match.replaceWithChildren()
			title = ''
			info = ''
			br = td.find('br')
			if br:
				string = br.nextSibling
				if string and isinstance(string,BeautifulSoup.NavigableString):
					while string and isinstance(string,BeautifulSoup.NavigableString):
						title += str(string)
						string = string.nextSibling
					title = title.strip()
					br = string
					if br and br.name == 'br':
						string = br.nextSibling
						if string and isinstance(string,BeautifulSoup.NavigableString):
							info = str(string).strip()
					
			title = convertHTMLCodes(title).encode('utf-8')
			info = convertHTMLCodes(info)
			#image = urllib.unquote(i.get('href','').split('imgurl=',1)[-1].split('&',1)[0])
			page = urllib.unquote(i.get('href','').split('q=',1)[-1].split('&',1)[0]).encode('utf-8')
			tn = ''
			img = i.find('img')
			if img: tn = img.get('src')
			image = tn
			results.append({'title':title,'tbUrl':tn,'unescapedUrl':image,'site':site,'info':info,'page':page})
		return results
	
	def getImages(self,query,page=1):
		start = ''
		if page > 1: start = '&start=%s' % ((page - 1) * self.perPage)
		url = self.baseURL.format(start=start,query='&' + query)
		html = self.getPage(url)
		#open('/tmp/test.html','w').write(repr(html))	
		return self.parseImages(html)

	def getPage(self,url):
		opener = urllib2.build_opener()
		opener.addheaders = [('User-agent', 'Mozilla/5.0')]
		html = opener.open(url).read()
		return html
		
	def getPageImages(self,url):
		html = self.getPage(url)
		soup = BeautifulSoup.BeautifulSoup(html)
		results = []
		for img in soup.findAll('img'):
			src = img.get('src')
			results.append({'title':src,'url':urlparse.urljoin(url,src),'file':src.split('/')[-1]})
		final = []
		print 'test'
		lastTerms = self.lastTerms()
		spaceLess = lastTerms.replace(' ','')
		singular = re.sub('(\w{2,})s',r'\1',lastTerms)
		print lastTerms
		for r in results:
			if lastTerms in re.sub('[\+\.\-_,]',' ',r['file']).lower():
				final.append(r)
		for r in results:
			if spaceLess in r['file'].lower() and not r in final:
				final.append(r)
		for r in results:
			if singular in re.sub('[\+\.\-_,]',' ',r['file']).lower() and not r in final:
				final.append(r)
		for r in results:
			if not r in final: final.append(r)
		return final
			
class googleImagesSession:
	def __init__(self):
		self.api = googleImagesAPI()
		self.save_path = __settings__.getSetting('save_path')
		self.max_history = (None,10,20,30,50,100,200,500)[int(__settings__.getSetting('max_history'))]
		self.isSlideshow = False
		
	fileKeepCharacters = (' ','.','_')
	def createValidFilename(self,text):
		try:
			text = text.encode('utf-8','replace')
			return "".join(c for c in text if c.isalnum() or c in self.fileKeepCharacters).rstrip()
		except:
			ERROR('createValidFilename()')
			return 'saved_google_image_%s' % random.randint(1,999999)
		
	def addLink(self,name,url,iconimage,tot=0,showcontext=True):
		liz=xbmcgui.ListItem(name, iconImage="DefaultImage.png", thumbnailImage=iconimage)
		liz.setInfo( type="image", infoLabels={ "Title": name } )
		if showcontext:
			savename = self.createValidFilename(url.rsplit('/')[-1])
			contextMenu = [(__language__(32010),'XBMC.RunScript(special://home/addons/plugin.image.google/default.py,save,'+url+','+savename+')')]
			liz.addContextMenuItems(contextMenu)
		return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz,isFolder=False,totalItems=tot)

	def addDir(self,name,url,mode,iconimage,page=1,tot=0,sort=0):
		u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&page="+str(page)+"&name="+urllib.quote_plus(name)
		liz=xbmcgui.ListItem(name, 'test',iconImage="DefaultFolder.png", thumbnailImage=iconimage)
		liz.setInfo( type="image", infoLabels={"Title": name} )
		return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True,totalItems=tot)
	
	def htmlToText(self,html):
		html = re.sub('<.*?>','',html)
		return html	.replace("&lt;", "<")\
					.replace("&gt;", ">")\
					.replace("&amp;", "&")\
					.replace("&quot;",'"')\
					.replace("&apos;","'")
					
	def CATEGORIES(self):
		self.addDir(__language__(32200),'search',1,os.path.join(IMAGE_PATH,'search.png'),sort=0)
		self.addDir(__language__(32201),'advanced_search',2,os.path.join(IMAGE_PATH,'advanced.png'),sort=1)
		self.addDir(__language__(32202),'history',3,os.path.join(IMAGE_PATH,'history.png'),sort=2)
		self.addDir(__language__(32203),'saves',4,os.path.join(IMAGE_PATH,'saves.png'),sort=3)
		
	def PAGE_IMAGES(self,url):
		images = self.api.getPageImages(url)
		for img in images:
			#fn,ignore = urllib.urlretrieve(tn,os.path.join(CACHE_PATH,str(ct) + tm + '.jpg')) #@UnusedVariable
			if not self.addLink(img.get('title',''),img.get('url',''),img.get('url','')): break
		return True
	
	def SEARCH_IMAGES(self,query,page=1,**kwargs):
		clearDirFiles(CACHE_PATH)
		if not query:
			terms = self.getTerms()
			if not terms: return True
			query = self.api.createQuery(terms,**kwargs)
			self.addToHistory(query)
			
		images = []
		if self.isSlideshow:
			for page in range(1,11):  # @UnusedVariable
				try:
					images += self.api.getImages(query,page=page)
				except:
					break
			ct=0
			tm = str(time.time())
			for img in images:
				tn = img.get('tbUrl','')
				fn,ignore = urllib.urlretrieve(tn,os.path.join(CACHE_PATH,str(ct) + tm + '.jpg'))
				self.addLink(self.htmlToText(img.get('title','')),fn,fn,tot=100)
				ct+=1
			return True
		else:
			images = self.api.getImages(query,page=page)
			
		ct=0;
		tm = str(time.time())
		
		if page > 1 and not self.isSlideshow: self.addDir('[<- Previous Page ({0} - {1})]'.format(((page-2)*self.api.perPage)+1,(page-1)*self.api.perPage), query, 101, '', page=page-1)
			
		for img in images:
			title = self.htmlToText(img.get('title',''))
			tn = img.get('tbUrl','')
			fn,ignore = urllib.urlretrieve(tn,os.path.join(CACHE_PATH,str(ct) + tm + '.jpg')) #@UnusedVariable
			if not self.addDir(title,img.get('page',''),200,fn,tot=self.api.perPage): break
			ct+=1
			
		if not self.isSlideshow: self.addDir('[Next Page ({0} - {1} of {2}) ->]'.format((page*self.api.perPage)+1,(page+1)*self.api.perPage,self.api.lastSearchTotal), query, 101, '', page=page+1)
			
		return True
	
	def ADVANCED_SEARCH_IMAGES(self):
		__settings__.openSettings()
		tbs = []
		safe = ['','active'][int(__settings__.getSetting('safe'))]
		if safe: tbs.append('safe:%s' % safe)
		
		image_size = ['','i','m','l'][int(__settings__.getSetting('image_size'))]
		if image_size: tbs.append('isz:%s' % image_size)
		
		greyscale = ['','gray','color','trans'][int(__settings__.getSetting('greyscale'))]
		if greyscale:
			tbs.append('ic:%s' % greyscale)
		else:
			color = ['','black','blue','brown','gray','green','orange','pink','purple','red','teal','white','yellow'][int(__settings__.getSetting('color'))]
			if color: tbs.append('ic:specific,isc:%s' % color)
			
		itype = ['','face','photo','clipart','lineart'][int(__settings__.getSetting('type'))]
		if itype: tbs.append('itp:%s' % itype)
		
		filetype = ['','jpg','png','gif','bmp'][int(__settings__.getSetting('filetype'))]
		if filetype: tbs.append('ift:%s' % filetype)
		
		rights = ['','fmc','fc','fm','f'][int(__settings__.getSetting('rights'))]
		if rights: tbs.append('sur:%s' % rights)
		return self.SEARCH_IMAGES('',tbs=','.join(tbs))
		
	'''
	Grayscale  : https://www.google.com/search?q=cows&btnG=Search&um=1&hl=en&tbm=isch&tab=wi&hl=en&q=cows&tbm=isch&tbs=ic:gray&um=1
	Any Color  : https://www.google.com/search?q=cows&btnG=Search&um=1&hl=en&tbm=isch&tab=wi&hl=en&q=cows&tbas=0&tbm=isch&um=1
	Full Color : https://www.google.com/search?q=cows&btnG=Search&um=1&hl=en&tbm=isch&tab=wi&hl=en&q=cows&tbas=0&tbm=isch&tbs=ic:color&um=1
	Transparent: https://www.google.com/search?q=cows&btnG=Search&um=1&hl=en&tbm=isch&tab=wi&hl=en&q=cows&tbas=0&tbm=isch&tbs=ic:trans&um=1
	Red        : https://www.google.com/search?q=cows&btnG=Search&um=1&hl=en&tbm=isch&tab=wi&hl=en&q=cows&tbas=0&tbm=isch&tbs=ic:specific,isc:red&um=1
	             red, orange, yellow, green, teal, blue, purple, pink, white, gray, black, brown
	             
	Large      : https://www.google.com/search?q=cows&btnG=Search&um=1&hl=en&tbm=isch&tab=wi&hl=en&q=cows&tbas=0&tbm=isch&tbs=isz:l&um=1
	             l, m, i
	
	Face       : https://www.google.com/search?hl=en&site=imghp&tbm=isch&source=hp&biw=1751&bih=822&q=cows&oq=cows&q=cows&tbm=isch&tbs=itp:face
	             face, photo, clipart, lineart, animated
	             
	safe=active
	tbs=sur:fmc Labeled Commericial Reuse Mod
	tbs=sur:fm Labeled Reuse Mod
	tbs=sur:fc Labeled Commericial Reuse
	tbs=sur:f Labeled Reuse
	
	ex tbs=sur:fmc,ic-gray
	'''
		
	def HISTORY(self,query=None):
		if query:
			self.api.lastTerms(urllib.unquote_plus(self.api.parseQuery(query).get('q')))
			self.SEARCH_IMAGES(query)
		else:
			for q in self.getHistory():
				terms = ''
				params = []
				sparams = ''
				for p in q.split('&'):
					p_v = p.split('=')
					if p_v[0] == 'q': terms = urllib.unquote_plus(p_v[-1])
					else: params.append(p_v)
				if params: sparams = ' | ' + ', '.join(self.translateParams(params))
					
				self.addDir(terms + sparams,q,103,'')
				
	def SAVES(self):
		save_path = xbmc.translatePath(__settings__.getSetting('save_path'))
		images = os.listdir(save_path)
		tot=len(images)
		ct=0;
		for img in images:
			if '.jpg' in img or '.png' in img or '.gif' in img or '.bmp' in img:
				fullpath = os.path.join(save_path,img)
				if not self.addLink(img,fullpath,fullpath,tot=tot,showcontext=False): break
			ct+=1
		return True
		
	def translateParams(self,params):
					
		vals = {	'active':__language__(32103),
					
					'i':__language__(32112),
					'm':__language__(32114),
					'l':__language__(32115),
					
					'color':__language__(32123),
					'trans':__language__(32124),
					
					'black':__language__(32131),
					'blue':__language__(320132),
					'brown':__language__(32133),
					'gray':__language__(32134),
					'green':__language__(32135),
					'orange':__language__(32136),
					'pink':__language__(32137),
					'purple':__language__(32138),
					'red':__language__(32139),
					'teal':__language__(32140),
					'white':__language__(32141),
					'yellow':__language__(32142),
					
					'face':__language__(32152),
					'photo':__language__(32153),
					'clipart':__language__(32154),
					'lineart':__language__(32155),
		
					'fmc':__language__(32172),
					'fm':__language__(32173),
					'fc':__language__(32174),
					'f':__language__(32175)
				}
		
		tbsKeys = { 'safe':__language__(32002),
					'isz':__language__(32003),
					'ic':__language__(32005),
					'isc':__language__(32005),
					'itp':__language__(32006),
					'ift':__language__(32007),
					'sur':__language__(32008)
				}

		trans = []
		specific = False
		for p_v in params:
			if p_v[0] == 'tbs':
				for item in p_v[-1].split(','):
					k_v = item.split(':')
					if k_v[-1] == 'specific':
						specific = True
					else:
						if not specific and k_v[-1] == 'gray': k_v[-1] = __language__(32123)
						trans.append(tbsKeys.get(k_v[0],k_v[0]) +'='+ vals.get(k_v[-1],k_v[-1]))
			else:
				pass
		return trans
			
	def getHistory(self):
		if not os.path.exists(HISTORY_PATH): return []
		fobj = open(HISTORY_PATH,'r')
		history = fobj.read()
		fobj.close()
		return history.splitlines()
		
	def saveHistory(self,history):
		fobj = open(HISTORY_PATH,'w')
		fobj.write('\n'.join(history))
		fobj.close()
		
	def addToHistory(self,query):
		history = self.getHistory()
		if query in history: history.remove(query)
		history.insert(0,query)
		history = history[0:self.max_history]
		self.saveHistory(history)
	
	def getTerms(self):
		keyboard = xbmc.Keyboard('',__language__(32300))
		keyboard.doModal()
		if (keyboard.isConfirmed()):
			return keyboard.getText()
		else:
			return ''

def getUniqueFileName(self,fn):
	ct=0
	while os.path.exists(fn):
		if ct>100:break
		fn_ext = os.path.splitext(fn)
		fn = os.path.join(fn_ext[0] + str(ct),fn_ext[1])
		ct+=1
	return fn
	
class SaveImage:
	def __init__(self):
		url = sys.argv[2]
		savename = sys.argv[3]
		save_path = __settings__.getSetting('save_path')
		self.pd = xbmcgui.DialogProgress()
		self.pd.create(__language__(32015),__language__(32016))
		fail = False
		if save_path:
			try:
				urllib.urlretrieve(url,os.path.join(save_path,savename),self.progressUpdate)
			except:
				fail = True
		else:
			fail = True
			
		if fail:
			xbmcgui.Dialog().ok(__language__(32017),__language__(32018))
			__settings__.openSettings()
			save_path = __settings__.getSetting('save_path')
			try:
				urllib.urlretrieve(url,os.path.join(save_path,savename),self.progressUpdate)
			except:
				xbmcgui.Dialog().ok(__language__(32019),__language__(32020))
				
		self.pd.close()
		xbmcgui.Dialog().ok(__language__(32012),__language__(32013).replace('@REPLACE@',savename),__language__(32014).replace('@REPLACE@',save_path))
		
	def progressUpdate(self,blocks,bsize,fsize):
		#print 'cool',blocks,bsize,fsize
		if fsize == -1 or fsize <= bsize:
			self.pd.update(0)
			#print 'test'
			return
		percent = int((float(blocks) / (fsize/bsize)) * 100)
		#print percent
		self.pd.update(percent)
	

	
def clearDirFiles(filepath):
	if not os.path.exists(filepath): return
	for f in os.listdir(filepath):
		f = os.path.join(filepath,f)
		if os.path.isfile(f): os.remove(f)
		
## XBMC Plugin stuff starts here --------------------------------------------------------            
def get_params():
	param={}
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
							
	return param


### Do plugin stuff --------------------------------------------------------------------------
def doPlugin():
	params=get_params()
	url=None
	name=None
	mode=None
	page=1

	try:
			url=urllib.unquote_plus(params["url"])
	except:
			pass
	try:
			name=urllib.unquote_plus(params["name"])
	except:
			pass
	try:
			mode=int(params["mode"])
	except:
			pass
	try:
			page = int(params["page"])
	except:
			pass

	if DEBUG:
		print "Mode: "+str(mode)
		print "URL: "+str(url)
		print "Name: "+str(name)
		print "Page: "+str(page)

	update_dir = False
	success = True
	cache = True
	
	
	gis = googleImagesSession()
	
	gis.isSlideshow = params.get('plugin_slideshow_ss','false') == 'true'
	#xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_TRACKNUM)
	
	if mode==None or url==None or len(url)<1:
		gis.CATEGORIES()
	elif mode==1:
		success = gis.SEARCH_IMAGES('')
	elif mode==2:
		success = gis.ADVANCED_SEARCH_IMAGES()
	elif mode==3:
		gis.HISTORY()
	elif mode==4:
		gis.SAVES()
	elif mode==101:
		success = gis.SEARCH_IMAGES(url, page=page)
		update_dir=True
	elif mode==103:
		gis.HISTORY(query=url)
	elif mode==200:
		gis.PAGE_IMAGES(url)
	
	xbmcplugin.endOfDirectory(int(sys.argv[1]),succeeded=success,updateListing=update_dir,cacheToDisc=cache)

if sys.argv[1] == 'save':
	SaveImage()
else:
	doPlugin()

'''
safe?  	 This optional argument supplies the search safety level which may be one of:

    * safe=active - enables the highest level of safe search filtering
    * safe=moderate - enables moderate safe search filtering (default)
    * safe=off - disables safe search filtering

imgsz? 	This optional argument tells the image search system to restrict the search to images of the specified size, where size can be one of:

    * imgsz=icon - restrict to small images
    * imgsz=small|medium|large|xlarge - restrict to medium images
    * imgsz=xxlarge - restrict to large images
    * imgsz=huge - restrict to extra large images

imgc? 	This optional argument tells the image search system to restrict the search to images of the specified colorization, where colorization can be one of:

    * imgc=gray - restrict to grayscale images
    * imgc=color - restrict to color images

imgcolor?New!
(experimental) 	This optional argument tells the image search system to filter the search to images of the specified color:

    * imgcolor=black
    * imgcolor=blue
    * imgcolor=brown
    * imgcolor=gray
    * imgcolor=green
    * imgcolor=orange
    * imgcolor=pink
    * imgcolor=purple
    * imgcolor=red
    * imgcolor=teal
    * imgcolor=white
    * imgcolor=yellow

imgtype?
(experimental) 	This optional argument tells the image search system to restrict the search to images of the specified type:

    * imgtype=face - restrict to images of faces
    * imgtype=photo - restrict to photos
    * imgtype=clipart - restrict to clipart images
    * imgtype=lineart - restrict to images of line drawings

as_filetype? 	This optional argument tells the image search system to restrict the search to images of the specified filetype, where filetype can be one of:

    * as_filetype=jpg - restrict to jpg images
    * as_filetype=png - restrict to png images
    * as_filetype=gif - restrict to gif images
    * as_filetype=bmp - restrict to bmp images

as_rights? 	This optional argument tells the image search system to restrict the search to images labeled with the given licenses, where rights can be one or more of:

    * as_rights=cc_publicdomain - restrict to images with the publicdomain label
    * as_rights=cc_attribute - restrict to images with the attribute label
    * as_rights=cc_sharealike - restrict to images with the sharealike label
    * as_rights=cc_noncommercial - restrict to images with the noncomercial label
    * as_rights=cc_nonderived - restrict to images with the nonderived label

These restrictions can be used together, both positively or negatively. For instance, to emulate the commercial use with modification license, set the following:

        &as_rights=(cc_publicdomain|cc_attribute|cc_sharealike).-(cc_noncommercial|cc_nonderived)

Note: Images returned with this filter may still have conditions on the license for use. Please remember that violating copyright is strictly prohibited by the API Terms of Use. For more details, see this article.
as_sitesearch? 	This optional argument tells the image search system to restrict the search to images within the specified domain, e.g., as_sitesearch=photobucket.com. Note: This method restricts results to images found on pages at the given URL. 
'''