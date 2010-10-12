#!/usr/bin/python
import urllib, re, simplejson, time, os
import xbmc, xbmcgui, xbmcplugin, xbmcaddon

__plugin__ =  'google'
__author__ = 'ruuk'
__url__ = 'http://code.google.com/p/googleImagesXBMC/'
__date__ = '10-12-2010'
__version__ = '0.9.0'
__settings__ = xbmcaddon.Addon(id='plugin.image.google')
__language__ = __settings__.getLocalizedString

CACHE_PATH = xbmc.translatePath('special://profile/addon_data/plugin.image.google/cache/')
HISTORY_PATH = xbmc.translatePath('special://profile/addon_data/plugin.image.google/history')
IMAGE_PATH = xbmc.translatePath('special://home/addons/plugin.image.google/resources/images/')

if not os.path.exists(CACHE_PATH): os.makedirs(CACHE_PATH)

class googleImagesAPI:
	base_url = 'http://ajax.googleapis.com/ajax/services/search/images?v=1.0&start=%s&rsz=8&%s'
	
	def createQuery(self,terms,**kwargs):
		qdict = {'q':terms}
		for k in kwargs.keys():
			if kwargs[k]: qdict[k] = kwargs[k]
		return urllib.urlencode(qdict)
		
	def getImagesFromQueryString(self,query):
		results = []
		for start in (0,8,16,24):
			url = self.base_url % (start,query)
			#print url
			search_results = urllib.urlopen(url)
			json = simplejson.loads(search_results.read())
			search_results.close()
			results += json['responseData']['results']
		return results
	
	def getImages(self,terms,**kwargs):
		query = self.createQuery(terms,kwargs)
		return self.getImagesWithQueryString(query)
	
	''' content
		GsearchResultClass
		visibleUrl
		titleNoFormatting
		originalContextUrl
		unescapedUrl
		url
		title
		imageId
		height
		width
		tbUrl
		tbWidth
		contentNoFormatting
		tbHeight
	'''

class googleImagesSession:
	def __init__(self):
		self.api = googleImagesAPI()
		self.save_path = __settings__.getSetting('save_path')
		self.max_history = (None,10,20,30,50,100,200,500)[int(__settings__.getSetting('max_history'))]
	
	def addLink(self,name,url,iconimage,tot=0,showcontext=True):
		ok=True
		liz=xbmcgui.ListItem(name, iconImage="DefaultImage.png", thumbnailImage=iconimage)
		liz.setInfo( type="image", infoLabels={ "Title": name } )
		if showcontext:
			savename = url.rsplit('/')[-1]
			if not ('.jpg' in savename or '.png' in savename or '.gif' in savename or '.bmp' in savename):
				savename = name.encode('ascii','replace').replace(' ','_')
			contextMenu = [(__language__(30010),'XBMC.RunScript(special://home/addons/plugin.image.google/default.py,save,'+url+','+savename+')')]
			liz.addContextMenuItems(contextMenu)
		return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz,isFolder=False,totalItems=tot)

	def addDir(self,name,url,mode,iconimage,page=1,tot=0):
		u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&page="+str(page)+"&name="+urllib.quote_plus(name)
		ok=True
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
		self.addDir(__language__(30200),'search',1,os.path.join(IMAGE_PATH,'search.png'))
		self.addDir(__language__(30201),'advanced_search',2,os.path.join(IMAGE_PATH,'advanced.png'))
		self.addDir(__language__(30202),'history',3,os.path.join(IMAGE_PATH,'history.png'))
		self.addDir(__language__(30203),'saves',4,os.path.join(IMAGE_PATH,'saves.png'))
		
	def SEARCH_IMAGES(self,query,**kwargs):
		clearDirFiles(CACHE_PATH)
		if not query:
			terms = self.getTerms()
			if not terms: return False
			query = self.api.createQuery(terms,**kwargs)
			self.addToHistory(query)
		images = self.api.getImagesFromQueryString(query)
		ct=0;
		tm = str(time.time())
		for img in images:
			title = self.htmlToText(img.get('title',''))
			tn = img.get('tbUrl','')
			fn,ignore = urllib.urlretrieve(tn,os.path.join(CACHE_PATH,str(ct) + tm + '.jpg'))
			if not self.addLink(title,img.get('unescapedUrl',''),fn,tot=32): break
			ct+=1
		return True
	
	def ADVANCED_SEARCH_IMAGES(self):
		__settings__.openSettings()
		safe = ['off','moderate','active'][int(__settings__.getSetting('safe'))]
		image_size = ['','icon','small','medium','large','xlarge','xxlarge','huge'][int(__settings__.getSetting('image_size'))]
		greyscale = ['','gray','color'][int(__settings__.getSetting('greyscale'))]
		color = ['','black','blue','brown','gray','green','orange','pink','purple','red','teal','white','yellow'][int(__settings__.getSetting('color'))]
		itype = ['','face','photo','clipart','lineart'][int(__settings__.getSetting('type'))]
		filetype = ['','jpg','png','gif','bmp'][int(__settings__.getSetting('filetype'))]
		rights = ['','cc_publicdomain','cc_attribute','cc_sharealike','cc_noncommercial','cc_nonderived'][int(__settings__.getSetting('rights'))]
		return self.SEARCH_IMAGES('',safe=safe,imgsz=image_size,imgc=greyscale,imgcolor=color,imgtype=itype,as_filetype=filetype,as_rights=rights)
		
	def HISTORY(self,query=None):
		if query:
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
		save_path = __settings__.getSetting('save_path')
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
		keys = {	'safe':__language__(30002),
					'imgsz':__language__(30003),
					'imgc':__language__(30004),
					'imgcolor':__language__(30005),
					'imgtype':__language__(30006),
					'as_filetype':__language__(30007),
					'as_rights':__language__(30008)}
					
		vals = {	'moderate':__language__(30102),
					'active':__language__(30103),
					
					'icon':__language__(30112),
					'small':__language__(30113),
					'medium':__language__(30114),
					'large':__language__(30115),
					'xlarge':__language__(30116),
					'xxlarge':__language__(30117),
					'huge':__language__(30118),
					
					'color':__language__(30123),
					
					'black':__language__(30131),
					'blue':__language__(300132),
					'brown':__language__(30133),
					'gray':__language__(30134),
					'green':__language__(30135),
					'orange':__language__(30136),
					'pink':__language__(30137),
					'purple':__language__(30138),
					'red':__language__(30139),
					'teal':__language__(30140),
					'white':__language__(30141),
					'yellow':__language__(30142),
					
					'face':__language__(30152),
					'photo':__language__(30153),
					'clipart':__language__(30154),
					'lineart':__language__(30155),
					
					'cc_publicdomain':__language__(30172),
					'cc_attribute':__language__(30173),
					'cc_sharealike':__language__(30174),
					'cc_noncommercial':__language__(30175),
					'cc_nonderived':__language__(30176)}
		trans = []
		for p_v in params:
			trans.append(keys.get(p_v[0],'') +'='+ vals.get(p_v[-1],''))
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
		history.insert(0,query)
		history = history[0:self.max_history]
		self.saveHistory(history)
	
	def getTerms(self):
		keyboard = xbmc.Keyboard('',__language__(30300))
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
		self.pd.create(__language__(30015),__language__(30016))
		fail = False
		try:
			fn,ignore = urllib.urlretrieve(url,os.path.join(save_path,savename),self.progressUpdate)
		except:
			fail = True
			
		if fail:
			xbmcgui.Dialog().ok(__language__(30017),__language__(30018))
			__settings__.openSettings()
			save_path = __settings__.getSetting('save_path')
			try:
				fn,ignore = urllib.urlretrieve(url,os.path.join(save_path,savename),self.progressUpdate)
			except:
				xbmcgui.Dialog().ok(__language__(30019),__language__(30020))
				
		self.pd.close()
		xbmcgui.Dialog().ok(__language__(30012),__language__(30013).replace('@REPLACE@',savename),__language__(30014).replace('@REPLACE@',save_path))
		
	def progressUpdate(self,blocks,bsize,fsize):
		print 'cool',blocks,bsize,fsize
		if fsize == -1 or fsize <= bsize:
			self.pd.update(0)
			print 'test'
			return
		percent = int((float(blocks) / (fsize/bsize)) * 100)
		print percent
		self.pd.update(percent)
	

	
def clearDirFiles(filepath):
	if not os.path.exists(filepath): return
	for f in os.listdir(filepath):
		f = os.path.join(filepath,f)
		if os.path.isfile(f): os.remove(f)
		
## XBMC Plugin stuff starts here --------------------------------------------------------            
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
							
	return param
        
       
### Do plugin stuff --------------------------------------------------------------------------
def doPlugin():
	params=get_params()
	url=None
	name=None
	mode=None


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

	print "Mode: "+str(mode)
	print "URL: "+str(url)
	print "Name: "+str(name)

	update_dir = False
	success = True
	cache = True

	gis = googleImagesSession()
	
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
	elif mode==103:
		gis.HISTORY(query=url)
		
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