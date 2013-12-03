#!/usr/bin/python

import flickrapi
import urllib
import xbmc, xbmcgui, xbmcplugin, xbmcaddon #@UnresolvedImport
import sys, os, time
from urllib2 import HTTPError, URLError

__plugin__ = 'flickr'
__author__ = 'ruuk'
__url__ = 'http://code.google.com/p/flickrxbmc/'
__date__ = '01-07-2013'
__settings__ = xbmcaddon.Addon(id='plugin.image.flickr')
__version__ = __settings__.getAddonInfo('version')
__language__ = __settings__.getLocalizedString

IMAGES_PATH = os.path.join(xbmc.translatePath(__settings__.getAddonInfo('path')),'resources', 'images')
CACHE_PATH = xbmc.translatePath('special://profile/addon_data/plugin.image.flickr/cache/')

import locale
loc = locale.getdefaultlocale()
ENCODING = loc[1] or 'utf-8'

ShareSocial = None

def ENCODE(string):
	return string.encode(ENCODING,'replace')

def LOG(message):
	print 'plugin.image.flickr: %s' % ENCODE(str(message))
	
def ERROR(message,caption=''):
	LOG(message)
	import traceback
	traceback.print_exc()
	err = str(sys.exc_info()[1])
	xbmcgui.Dialog().ok(__language__(30520) + caption,err)
	return err

if not os.path.exists(CACHE_PATH): os.makedirs(CACHE_PATH)

class flickrPLUS(flickrapi.FlickrAPI):
	def walk_photos_by_page(self, method, **params):
			rsp = method(**params) 

			photoset = rsp.getchildren()[0]
			page = int(photoset.attrib.get('page','1'))
			pages = int(photoset.attrib.get('pages','1'))
			perpage = int(photoset.attrib.get('perpage','1'))
			total = int(photoset.attrib.get('total','1'))
			self.TOTAL = total
			self.TOTAL_ON_LAST_PAGE = total % perpage
			self.TOTAL_ON_PAGE = perpage
			self.TOTAL_PAGES = pages
			if page == pages: self.TOTAL_ON_PAGE = self.TOTAL_ON_LAST_PAGE
			
			photos = rsp.findall('*/photo')

			# Yield each photo 
			for photo in photos:
				yield photo
				
	def get_full_token(self, mini_token):
		'''Gets the token given a certain frob. Used by ``get_token_part_two`` and
		by the web authentication method.
		'''
		
		# get a token
		rsp = self.auth_getFullToken(mini_token=mini_token, format='xmlnode')

		token = rsp.auth[0].token[0].text
		flickrapi.LOG.debug("get_token: new token '%s'" % token)
		
		# store the auth info for next time
		self.token_cache.token = token

		return token

def photoURL(farm,server,nsid,secret='',buddy=False,size='',ext='jpg'):
	replace = (farm,server,nsid)
	if secret: secret = '_' + secret
	if buddy:
		return 'http://farm%s.staticflickr.com/%s/buddyicons/%s.jpg' % replace #last %s not is to use same replace
	elif not size:
		return 'http://farm%s.staticflickr.com/%s/%s%s.jpg' % (replace + (secret,))
	else:
		return 'http://farm%s.staticflickr.com/%s/%s%s_%s.%s' % (replace + (secret,size,ext))
		
	'''
	s	small square 75x75
	q	large square 150x150
	t	thumbnail, 100 on longest side
	m	small, 240 on longest side
	n	small, 320 on longest side
	-	medium, 500 on longest side
	z	medium 640, 640 on longest side
	b	large, 1024 on longest side*
	o	original image, either a jpg, gif or png, depending on source format
	'''
	
class Maps:
	def __init__(self):
		self.map_source = ['google','yahoo','osm'][int(__settings__.getSetting('default_map_source'))]
		if self.map_source == 'yahoo':
			import elementtree.ElementTree as et #@UnresolvedImport
			self.ET = et
		self.zoom =  {	'country':int(__settings__.getSetting('country_zoom')),
						'region':int(__settings__.getSetting('region_zoom')),
						'locality':int(__settings__.getSetting('locality_zoom')),
						'neighborhood':int(__settings__.getSetting('neighborhood_zoom')),
						'photo':int(__settings__.getSetting('photo_zoom'))}
		self.default_map_type = ['hybrid','satellite','terrain','roadmap'][int(__settings__.getSetting('default_map_type'))]
		
	def getMap(self,lat,lon,zoom,width=256,height=256,scale=1,marker=False):
		#640x36
		source = self.map_source
		lat = str(lat)
		lon = str(lon)
		zoom = str(self.zoom[zoom])
		#create map file name from lat,lon,zoom and time. Take that thumbnail cache!!! :)
		fnamebase = (lat+lon+zoom+str(int(time.time()))).replace('.','')
		ipath = os.path.join(CACHE_PATH,fnamebase+'.jpg')
		mark = ''
		if marker:
			if source == 'osm': 
				mark = '&mlat0=' + lat + '&mlon0=' + lon + '&mico0=0'
			elif source == 'yahoo':
				mark = ''
			else:
				mark = '&markers=color:blue|' + lat + ',' + lon
		if source == 'osm':
			url = "http://ojw.dev.openstreetmap.org/StaticMap/?lat="+lat+"&lon="+lon+"&z="+zoom+"&w="+str(width)+"&h="+str(height)+"&show=1&fmt=jpg"
		elif source == 'yahoo':
			#zoom = str((int((21 - int(zoom)) * (12/21.0)) or 1) + 1)
			zoom = self.translateZoomToYahoo(zoom)
			xml = urllib.urlopen("http://local.yahooapis.com/MapsService/V1/mapImage?appid=BteTjhnV34E7M.r_gjDLCI33rmG0FL7TFPCMF7LHEleA_iKm6S_rEjpCmns-&latitude="+lat+"&longitude="+lon+"&image_height="+str(height)+"&image_width="+str(width)+"&zoom="+zoom).read()
			url = self.ET.fromstring(xml).text.strip()
			url = urllib.unquote_plus(url)
			if 'error' in url: return ''
		else:
			url = "http://maps.google.com/maps/api/staticmap?center="+lat+","+lon+"&zoom="+zoom+"&size="+str(width)+"x"+str(height)+"&sensor=false&maptype="+self.default_map_type+"&scale="+str(scale)+"&format=jpg"

		fname,ignore  = urllib.urlretrieve(url + mark,ipath) #@UnusedVariable
		return fname

	def translateZoomToYahoo(self,zoom):
		#Yahoo and your infernal static maps 12 level zoom!
		#This matches as closely as possible the defaults for google and osm while allowing all 12 values
		zoom = 16 - int(zoom)
		if zoom < 1: zoom = 1
		if zoom >12: zoom = 12
		return str(zoom)
		
	def doMap(self):
		clearDirFiles(CACHE_PATH)
		self.getMap(sys.argv[2],sys.argv[3],'photo',width=640,height=360,scale=2,marker=True)
		xbmc.executebuiltin('SlideShow('+CACHE_PATH+')')
	
class FlickrSession:
	API_KEY = '0a802e6334304794769996c84c57d187'
	API_SECRET = '655ce70e86ac412e'
	
	MOBILE_API_KEY = 'f9b69ca9510b3f55fdc15aa869614b39'
	MOBILE_API_SECRET = 'fdba8bb77fc10921'
	
	DISPLAY_VALUES = ['Square','Thumbnail','Small','Medium','Medium640','Large','Original']
	SIZE_KEYS = {	'Square':'url_sq',
					'Thumbnail':'url_t',
					'Small':'url_s',
					'Medium':'url_m',
					'Medium640':'url_z',
					'Large':'url_l',
					'Original':'url_o'}
	
	def __init__(self,username=None):
		self.flickr = None
		self._authenticated = False
		self.mobile = True
		self.username = username
		self.user_id = None
		self.loadSettings()
		self.maps = None
		self.justAuthorized = False
		self.isSlideshow = False
		self._isMobile = None
		if __settings__.getSetting('enable_maps') == 'true': self.maps = Maps()
		
	def authenticated(self): return self._authenticated
		
	def loadSettings(self):
		self.username = __settings__.getSetting('flickr_username')
		self.defaultThumbSize = self.getDisplayValue(__settings__.getSetting('default_thumb_size'))
		self.defaultDisplaySize = self.getDisplayValue(__settings__.getSetting('default_display_size'))
		mpp = __settings__.getSetting('max_per_page')
		mpp = [10,20,30,40,50,75,100,200,500][int(mpp)]
		self.max_per_page = mpp
	
	def getDisplayValue(self,index):
		return self.DISPLAY_VALUES[int(index)]

	def isMobile(self,set=None):
		if set == None:
			if self._isMobile != None: return self._isMobile  
			return __settings__.getSetting('mobile') == 'true'
		if set:
			__settings__.setSetting('mobile','true')
			self.flickr.api_key = self.MOBILE_API_KEY
			self.flickr.secret = self.MOBILE_API_SECRET
		else:
			__settings__.setSetting('mobile','false')
			self.flickr.api_key = self.API_KEY
			self.flickr.secret = self.API_SECRET
		self._isMobile = set
	
	def getKeys(self):
		if self.isMobile():
			return self.MOBILE_API_KEY,self.MOBILE_API_SECRET
		else:
			return self.API_KEY,self.API_SECRET
		
	def doTokenDialog(self,frob,perms):
		if False:
			try:
				from webviewer import webviewer #@UnresolvedImport @UnusedImport
				yes = xbmcgui.Dialog().yesno('Authenticate','Press \'Yes\' to authenticate in any browser','Press \'No\' to use Web Viewer (If Installed)')
				if not yes:
					self.isMobile(False)
					self.doNormalTokenDialog(frob, perms)
					return
			except ImportError:
				LOG("Web Viewer Not Installed - Using Mobile Method")
				pass
			except:
				ERROR('')
				return
			
		self.isMobile(True)
		self.doMiniTokenDialog(frob, perms)
		
	def doNormalTokenDialog(self,frob,perms):
		url = self.flickr.auth_url('read',frob)
		if PLUGIN: xbmcplugin.endOfDirectory(int(sys.argv[1]),succeeded=False)
		self.justAuthorized = True
		xbmcgui.Dialog().ok(__language__(30507),__language__(30508),__language__(30509))
		from webviewer import webviewer #@UnresolvedImport
		autoforms = [	{'action':'login.yahoo.com/config/login'},
						{'url':'.+perms=.+','action':'services/auth','index':2},
						{'url':'.+services/auth/$','action':'services/auth'}]
		autoClose = {	'url':'.+services/auth/$',
						'html':'(?s).+successfully authorized.+',
						'heading':__language__(30505),
						'message':__language__(30506)}
		url,html = webviewer.getWebResult(url,autoForms=autoforms,autoClose=autoClose) #@UnusedVariable
		LOG('AUTH RESPONSE URL: ' + url)

	def extractTokenFromURL(self,url):
		from cgi import parse_qs
		import urlparse
		try:
			token = parse_qs(urlparse.urlparse(url.replace('#','?',1))[4])['token'][0].strip()
		except:
			LOG('Invalid Token')
			return None
		return token
	
	def doMiniTokenDialog(self,frob,perms):
		xbmcgui.Dialog().ok("AUTHENTICATE",'Go to http://xbmc.2ndmind.com/auth','get the code and click OK to continue')
		mini_token = ''
		message = 'Enter 9 digit code'
		while not len(mini_token) == 9 or not mini_token.isdigit():
			keyboard = xbmc.Keyboard('',message)
			message = 'BAD CODE. Re-enter 9 digit code'
			keyboard.doModal()
			if not keyboard.isConfirmed(): return
			mini_token = keyboard.getText().replace('-','')
			if not mini_token: return
		token = self.flickr.get_full_token(mini_token) #@UnusedVariable
		
	def authenticate(self,force=False):
		key,secret = self.getKeys()
		self.flickr = flickrPLUS(key,secret)
		if force:
			self.flickr.token_cache.token = ''
		else:
			if __settings__.getSetting('authenticate') != 'true': return True
		(token, frob) = self.flickr.get_token_part_one(perms='read',auth_callback=self.doTokenDialog)
		if self.isMobile():
			result = self.authenticateMobile(self.flickr.token_cache.token)
		else:
			result = self.authenticateWebViewer(token,frob)

		if result: self._authenticated = True
		return result

	def authenticateWebViewer(self,token,frob):
		try:
			self.flickr.get_token_part_two((token, frob))
		except:
			if self.justAuthorized:
				xbmcgui.Dialog().ok(__language__(30520),__language__(30521),str(sys.exc_info()[1]))
			else:
				xbmcgui.Dialog().ok(__language__(30522),__language__(30523),str(sys.exc_info()[1]))
			LOG("Failed to get token. Probably did not authorize.")
		LOG("AUTH DONE")
		if self.justAuthorized: return False
		return self.finishAuthenticate(token)
		
	def authenticateMobile(self,token):
		if not token:
			LOG("Failed to get token (Mobile). Probably did not authorize.")
			return False
		return self.finishAuthenticate(token)
		
	def finishAuthenticate(self,token):
		self.flickr.token_cache.token = token
		if self.username:
			user = self.flickr.people_findByUsername(username=self.username)
			self.user_id = user.findall('*')[0].get('id')
		else:
			rsp = self.flickr.auth_checkToken(auth_token=token,format='xmlnode')
			user = rsp.auth[0].user[0]
			self.user_id = user.attrib.get('nsid')
			self.username = user.attrib.get('username')
			if self.username: __settings__.setSetting('flickr_username',self.username)
		return True
			
	def getCollectionsInfoList(self,userid=None,cid='0'):
		if not userid: userid = self.user_id
		col = self.flickr.collections_getTree(user_id=userid,collection_id=cid)
		info_list = []
		mode = None
		colCount = len(col.find('collections').findall('collection'));
		if colCount < 1: return (2,[])
		if colCount > 1 or (colCount < 2 and col.find('collections').find('collection').attrib.get('id') != cid):
			mode = 2
			for c in col.find('collections').findall('collection'):
				if cid != c.attrib.get('id'): info_list.append({'title':c.attrib.get('title',''),'id':c.attrib.get('id',''),'tn':c.attrib.get('iconlarge','')})
		else:
			mode = 103
			tn_dict = self.getSetsThumbnailDict(userid=userid)
			for c in col.find('collections').find('collection').findall('set'):
				info_list.append({'title':c.attrib.get('title',''),'id':c.attrib.get('id',''),'tn':tn_dict.get(c.attrib.get('id',''),'')})
		
		return (mode, info_list)
		
	def getSetsInfoList(self,userid=None):
		if not userid: userid = self.user_id
		sets = self.flickr.photosets_getList(user_id=userid)
		info_list = []
		for s in sets.find('photosets').findall('photoset'):
			tn = "http://farm"+s.attrib.get('farm','')+".static.flickr.com/"+s.attrib.get('server','')+"/"+s.attrib.get('primary','')+"_"+s.attrib.get('secret','')+"_s.jpg"
			info_list.append({'title':s.find('title').text,'count':s.attrib.get('photos','0'),'id':s.attrib.get('id',''),'tn':tn})
		return info_list
		
	def getContactsInfoList(self,userid=None):
		if userid: contacts = self.flickr.contacts_getPublicList(user_id=userid)
		else: contacts = self.flickr.contacts_getList()
		info_list = []
		for c in contacts.find('contacts').findall('contact'):
			if c.attrib.get('iconserver','') == '0':
				tn = 'http://l.yimg.com/g/images/buddyicon.jpg'
			else:
				tn = "http://farm"+c.attrib.get('iconfarm','')+".static.flickr.com/"+c.attrib.get('iconserver','')+"/buddyicons/"+c.attrib.get('nsid','')+".jpg"
			info_list.append({'username':c.attrib.get('username',''),'id':c.attrib.get('nsid',''),'tn':tn})
		return info_list
	
	def getGroupsInfoList(self,userid=None,search=None,page=1):
		total = None
		if search:
			groups = self.flickr.groups_search(text=search,page=page,per_page=self.max_per_page)
			info = groups.find('groups')
			page = int(info.attrib.get('page','1'))
			pages = int(info.attrib.get('pages','1'))
			perpage = int(info.attrib.get('perpage','1'))
			total = int(info.attrib.get('total','1'))
			self.flickr.TOTAL = total
			self.flickr.TOTAL_ON_LAST_PAGE = total % perpage
			self.flickr.TOTAL_ON_PAGE = perpage
			self.flickr.TOTAL_PAGES = pages
			if page == pages: self.flickr.TOTAL_ON_PAGE = self.flickr.TOTAL_ON_LAST_PAGE
		else:
			if not userid: userid = self.user_id
			groups = self.flickr.groups_pools_getGroups(user_id=userid)
		info_list = []
		for g in groups.find('groups').findall('group'):
			tn = "http://farm"+g.attrib.get('iconfarm','')+".static.flickr.com/"+g.attrib.get('iconserver','')+"/buddyicons/"+g.attrib.get('nsid','')+".jpg"
			info_list.append({'name':g.attrib.get('name','0'),'count':g.attrib.get('photos',g.attrib.get('pool_count','0')),'id':g.attrib.get('id',g.attrib.get('nsid','')),'tn':tn})
		return info_list

	def getGalleriesInfoList(self,userid=None):
		if not userid: userid = self.user_id
		galleries = self.flickr.galleries_getList(user_id=userid)
		info_list = []
		for g in galleries.find('galleries').findall('gallery'):
			tn = "http://farm"+g.attrib.get('primary_photo_farm','')+".static.flickr.com/"+g.attrib.get('primary_photo_server','')+"/"+g.attrib.get('primary_photo_id','')+"_"+g.attrib.get('primary_photo_secret','')+"_s.jpg"
			info_list.append({	'title':g.find('title').text,
								'id':g.attrib.get('id'),
								'tn':tn})
		return info_list
		
	def getTagsList(self,userid=None):
		if not userid: userid = self.user_id
		tags = self.flickr.tags_getListUser(user_id=userid)
		t_list = []
		for t in tags.find('who').find('tags').findall('tag'):
			t_list.append(t.text)
		return t_list
		
	def getPlacesInfoList(self,pid,woeid=None):
		#12,8,7
		places = self.flickr.places_placesForUser(place_type_id=pid,woe_id=woeid)
		info_list=[]
		for p in places.find('places').findall('place'):
			info_list.append({	'place':p.text.split(',')[0],
								'woeid':p.attrib.get('woeid'),
								'count':p.attrib.get('photo_count'),
								'lat':p.attrib.get('latitude'),
								'lon':p.attrib.get('longitude')})
		return info_list
		
	def getSetsThumbnailDict(self,userid=None):
		if not userid: userid = self.user_id
		sets = self.flickr.photosets_getList(user_id=userid)
		tn_dict = {}
		for s in sets.find('photosets').findall('photoset'):
			tn_dict[s.attrib.get('id','0')] =  "http://farm"+s.attrib.get('farm','')+".static.flickr.com/"+s.attrib.get('server','')+"/"+s.attrib.get('primary','')+"_"+s.attrib.get('secret','')+"_s.jpg"
		return tn_dict
		
	def getImageUrl(self,pid,label='Square'):
		ps = self.flickr.photos_getSizes(photo_id=pid)
		if label == 'all':
			allsizes = {}
			for s in ps.find('sizes').findall('size'):
				allsizes[s.get('label')] = s.get('source')
			#if not 'Original' in allsizes: allsizes['Original'] = ps.find('sizes')[0].findall('size')[-1].get('source')
			return allsizes
		for s in ps.find('sizes').findall('size'):
			if s.get('label') == label:
				return s.get('source')
		
	def addPhotos(self,method,mode,url='BLANK',page='1',mapOption=True,with_username=False,**kwargs):
		global ShareSocial
		try:
			import ShareSocial #@UnresolvedImport
		except:
			pass
		
		page = int(page)
		
		#Add Previous Header if necessary
		if page > 1:
			previous = '<- '+__language__(30511)
			pg = (page==2) and '-1' or  str(page-1) #if previous page is one, set to -1 to differentiate from initial showing
			self.addDir(previous.replace('@REPLACE@',str(self.max_per_page)),url,mode,os.path.join(IMAGES_PATH,'previous.png'),page = pg,userid=kwargs.get('userid',''))
			
		#info_list = []
		extras = 'media, date_upload, date_taken, url_sq, url_t, url_s, url_m, url_l,url_o' + self.SIZE_KEYS[self.defaultThumbSize] + ',' + self.SIZE_KEYS[self.defaultDisplaySize]
		if mapOption: extras += ',geo'
		
		#Walk photos
		ct=1
		mpp = self.max_per_page
		if self.isSlideshow: mpp = 500
		for photo in self.flickr.walk_photos_by_page(method,page=page,per_page=mpp,extras=extras,**kwargs):
			ct+=1
			ok = self.addPhoto(photo, mapOption=mapOption,with_username=with_username)
			if not ok: break
			
		#Add Next Footer if necessary
		#print "PAGES: " + str(page) + " " + str(self.flickr.TOTAL_PAGES) + " " + self.flickr.TOTAL_ON_LAST_PAGE
		if ct >= self.max_per_page:
			nextp = '('+str(page*self.max_per_page)+'/'+str(self.flickr.TOTAL)+') '
			replace = ''
			if page + 1 == self.flickr.TOTAL_PAGES:
				nextp += __language__(30513)
				if self.flickr.TOTAL_ON_LAST_PAGE: replace = str(self.flickr.TOTAL_ON_LAST_PAGE)
				else: replace = str(self.max_per_page)
			else: 
				nextp += __language__(30512)
				replace = str(self.max_per_page)
			if page < self.flickr.TOTAL_PAGES: self.addDir(nextp.replace('@REPLACE@',replace)+' ->',url,mode,os.path.join(IMAGES_PATH,'next.png'),page=str(page+1),userid=kwargs.get('userid',''))
		
	def addPhoto(self,photo,mapOption=False,with_username=False):
		pid = photo.get('id')
		title = photo.get('title')
		if not title:
			title = photo.get('datetaken')
			if not title:
				try: title = time.strftime('%m-%d-%y %I:%M %p',time.localtime(int(photo.get('dateupload'))))
				except: pass
				if not title: title = pid
				
		if with_username:
			username = photo.get('username','') or ''
			title = '[B]%s:[/B] %s' % (username,title)
			
		ptype = photo.get('media') == 'video' and 'video' or 'image'
		#ptype = 'image'
		thumb = photo.get(self.SIZE_KEYS[self.defaultThumbSize])
		display = photo.get(self.SIZE_KEYS[self.defaultDisplaySize])
		if not (thumb and display):
			display = photo.get(self.SIZE_KEYS[self.defaultDisplaySize],photo.get('url_o',''))
			thumb = photo.get(self.SIZE_KEYS[self.defaultThumbSize],photo.get('url_s',''))
			if not display:
				rd = self.DISPLAY_VALUES[:]
				rd.reverse()
				for s in rd:
					if photo.get(s):
						display = photo.get(s)
						break
		sizes = {}
		if ptype == 'video':
			sizes = self.getImageUrl(pid,'all')
			display = sizes.get('Site MP4',photo.get('Video Original',''))
			#display = 'plugin://plugin.image.flickr/?play_video&' + pid
		contextMenu = []
		if mapOption:
			lat=photo.get('latitude')
			lon=photo.get('longitude')
			if not lat+lon == '00':
				contextMenu.append((__language__(30510),'XBMC.RunScript(special://home/addons/plugin.image.flickr/default.py,map,'+lat+','+lon+')'))
		
		if ShareSocial:
			run = self.getShareString(photo,sizes)
			if run: contextMenu.append(('Share...',run))
		
		saveURL = photo.get('url_o',display)
		contextMenu.append((__language__(30517),'XBMC.RunScript(special://home/addons/plugin.image.flickr/default.py,save,'+urllib.quote_plus(saveURL)+','+title+')'))
		#contextMenu.append(('Test...','XBMC.RunScript(special://home/addons/plugin.image.flickr/default.py,slideshow)'))
		
		return self.addLink(title,display,thumb,tot=self.flickr.TOTAL_ON_PAGE,contextMenu=contextMenu,ltype=ptype)
		
	def getShareString(self,photo,sizes):
		plink = 'http://www.flickr.com/photos/%s/%s' % (photo.get('owner',self.user_id),photo.get('id'))
		if photo.get('media') == 'photo':
			share = ShareSocial.getShare('plugin.image.flickr','image')
		else:
			share = ShareSocial.getShare('plugin.image.flickr','video')
			
		share.sourceName = 'flickr'
		share.page = plink
		share.latitude = photo.get('latitude')
		share.longitude = photo.get('longitude')
		
		if photo.get('media') == 'photo':
			share.thumbnail = photo.get('url_t',photo.get('url_s',''))
			share.media = photo.get('url_l',photo.get('url_o',photo.get('url_t','')))
			share.title = 'flickr Photo: %s' % photo.get('title')
		elif photo.get('media') == 'video':
			share.thumbnail = photo.get('url_o',photo.get('url_l',photo.get('url_m','')))
			embed = '<object type="application/x-shockwave-flash" width="%s" height="%s" data="%s"  classid="clsid:D27CDB6E-AE6D-11cf-96B8-444553540000"> <param name="flashvars" value="flickr_show_info_box=false"></param> <param name="movie" value="%s"></param><param name="bgcolor" value="#000000"></param><param name="allowFullScreen" value="true"></param><embed type="application/x-shockwave-flash" src="%s" bgcolor="#000000" allowfullscreen="true" flashvars="flickr_show_info_box=false" height="%s" width="%s"></embed></object>'
			url = sizes.get('Video Player','')
			embed = embed % (640,480,url,url,url,480,640)
			share.title = 'flickr Video: %s' % photo.get('title')
			share.swf = url
			share.media = sizes.get('Site MP4',sizes.get('Video Original',''))
			share.embed = embed
		else:
			return None
		
		return share.toPluginRunscriptString()
		
	def userID(self):
		if self.user_id: return self.user_id
		username = __settings__.getSetting('flickr_username')
		self.username = username
		if not username: return None
		self.user_id = self.getUserID(username)
		return self.userID()
		
	def getUserID(self,username):
		if not username: return None
		obj = self.flickr.people_findByUsername(username=username)
		user = obj.find('user')
		return user.attrib.get('nsid')
		
	def CATEGORIES(self):
		uid = self.userID()
		if self.authenticated():
			self.addDir(__language__(30300),'photostream',1,os.path.join(IMAGES_PATH,'photostream.png'))
			self.addDir(__language__(30301),'collections',2,os.path.join(IMAGES_PATH,'collections.png'))
			self.addDir(__language__(30302),'sets',3,os.path.join(IMAGES_PATH,'sets.png'))
			self.addDir(__language__(30303),'galleries',4,os.path.join(IMAGES_PATH,'galleries.png'))
			self.addDir(__language__(30304),'tags',5,os.path.join(IMAGES_PATH,'tags.png'))
			self.addDir(__language__(30307),'places',8,os.path.join(IMAGES_PATH,'places.png'))
			self.addDir(__language__(30305),'favorites',6,os.path.join(IMAGES_PATH,'favorites.png'))
			self.addDir(__language__(30306),'contacts',7,os.path.join(IMAGES_PATH,'contacts.png'))
			self.addDir(__language__(30311),'groups',12,os.path.join(IMAGES_PATH,'groups.png'))
			self.addDir(__language__(30308),'@@search@@',9,os.path.join(IMAGES_PATH,'search_photostream.png'))
		elif uid:
			self.CONTACT(uid, self.username)
		self.addDir(__language__(30309),'@@search@@',10,os.path.join(IMAGES_PATH,'search_flickr.png'))
		self.addDir(__language__(30312),'@@search@@',13,os.path.join(IMAGES_PATH,'search_flickr.png'))
		self.addDir(__language__(30310),'interesting',11,os.path.join(IMAGES_PATH,'interesting.png'))
		
	def PHOTOSTREAM(self,page,mode=1,userid='me'):
		#if not self.authenticated() and userid == 'me':
		#	userid = self.userID()
		#	if not userid: return
		#
		self.addPhotos(self.flickr.photos_search,mode,url=userid,page=page,user_id=userid)
		
	def COLLECTION(self,cid,userid=None):
		if cid == 'collections': cid = 0
		mode,cols = self.getCollectionsInfoList(cid=cid,userid=userid)
		total = len(cols)
		for c in cols:
			if not self.addDir(c['title'],c['id'],mode,c['tn'],tot=total,userid=userid): break
			
	def SETS(self,mode=103,userid=None):
		sets = self.getSetsInfoList(userid=userid)
		total = len(sets)
		for s in sets:
			if not self.addDir(s['title']+' ('+s['count']+')',s['id'],mode,s['tn'],tot=total): break
	
	def GALLERIES(self,userid=None):
		galleries = self.getGalleriesInfoList(userid=userid)
		for g in galleries:
			if not self.addDir(g.get('title',''),g.get('id'),104,g.get('tn'),tot=len(galleries)): break
	
	def TAGS(self,userid=''):
		tags = self.getTagsList(userid=userid)
		for t in tags:
			if not self.addDir(t,t,105,'',tot=len(tags),userid=userid): break
			
	def PLACES(self,pid,woeid=None,name='',zoom='2'):
		places = self.getPlacesInfoList(pid,woeid=woeid)
		
		#If there are no places in this place id level, show all the photos
		if not places:
			self.PLACE(woeid,1)
			return
			
		if woeid and len(places) > 1: self.addDir(__language__(30500).replace('@REPLACE@',name),woeid,1022,'')
		idx=0
		for p in places:
			count = p.get('count','0')
			tn = ''
			if self.maps: tn = self.maps.getMap(p.get('lat','0'),p.get('lon','0'),zoom)
			if not self.addDir(p.get('place','')+' ('+count+')',p.get('woeid'),1000 + pid,tn,tot=len(places)): break
			idx+=1
		
	def FAVORITES(self,page,userid=None):
		self.addPhotos(self.flickr.favorites_getList,6,page=page,user_id=userid)
		
	def CONTACTS(self,userid=None):
		contacts = self.getContactsInfoList(userid=userid)
		total = len(contacts) + 1
		for c in contacts:
			if not self.addDir(c['username'],c['id'],107,c['tn'],tot=total): break
		if contacts:
			self.addDir("[B][%s][/B]" % __language__(30518),'recent_photos',800,os.path.join(IMAGES_PATH,'photostream.png'),tot=total)
			
	def CONTACTS_RECENT_PHOTOS(self,userid=None):
		self.addPhotos(self.flickr.photos_getContactsPhotos,800,mapOption=True, with_username=True, count=50)
		
	def GROUPS(self,userid=None):
		groups = self.getGroupsInfoList(userid)
		total = len(groups)
		for g in groups:
			if not self.addDir(g['name'] + ' (%s)' % g['count'],g['id'],112,g['tn'],tot=total): break
			
	def getText(self,prompt=__language__(30501)):
		keyboard = xbmc.Keyboard('',prompt)
		keyboard.doModal()
		if (keyboard.isConfirmed()):
			return keyboard.getText()
		return None
	
	def SEARCH_GROUPS(self,tags,page=1):
		if not tags or tags == '@@search@@':
			tags = self.getText() or tags
		groups = self.getGroupsInfoList(search=tags,page=page)
		total = len(groups)
		
		page = int(page)
		#Add Previous Header if necessary
		if page > 1:
			previous = '<- '+__language__(30511)
			pg = (page==2) and '-1' or  str(page-1) #if previous page is one, set to -1 to differentiate from initial showing
			self.addDir(previous.replace('@REPLACE@',str(self.max_per_page)),tags,13,os.path.join(IMAGES_PATH,'previous.png'),page = pg)
			
		for g in groups:
			if not self.addDir(g['name'] + ' (%s)' % g['count'],g['id'],112,g['tn'],tot=total): break
		if total >= self.max_per_page:
			nextp = '('+str(page*self.max_per_page)+'/'+str(self.flickr.TOTAL)+') '
			replace = ''
			if page + 1 == self.flickr.TOTAL_PAGES:
				nextp += __language__(30513)
				if self.flickr.TOTAL_ON_LAST_PAGE: replace = str(self.flickr.TOTAL_ON_LAST_PAGE)
				else: replace = str(self.max_per_page)
			else: 
				nextp += __language__(30512)
				replace = str(self.max_per_page)
			if page < self.flickr.TOTAL_PAGES: self.addDir(nextp.replace('@REPLACE@',replace)+' ->',tags,13,os.path.join(IMAGES_PATH,'next.png'),page=str(page+1))
			
	def SEARCH_TAGS(self,tags,page,mode=9,userid=None):
		if tags == '@@search@@' or tags == userid:
			tags = self.getText() or tags
		self.addPhotos(self.flickr.photos_search,mode,url=tags,page=page,tags=tags,user_id=userid)
		
	def INTERESTING(self,page):
		self.addPhotos(self.flickr.interestingness_getList,11,page=page)
		
	def SET(self,psid,page):
		self.addPhotos(self.flickr.photosets_getPhotos,103,url=psid,page=page,photoset_id=psid)
		
	def GALLERY(self,gid,page):
		self.addPhotos(self.flickr.galleries_getPhotos,103,url=gid,page=page,gallery_id=gid)
		
	def TAG(self,tag,page,userid=None):
		if not userid: userid = 'me'
		self.addPhotos(self.flickr.photos_search,105,url=tag,page=page,tags=tag,user_id=userid)
		
	def CONTACT(self,cid,name):
		self.addDir(__language__(30514).replace('@NAMEREPLACE@',name).replace('@REPLACE@',__language__(30300)),cid,701,os.path.join(IMAGES_PATH,'photostream.png'))
		self.addDir(__language__(30515).replace('@NAMEREPLACE@',name).replace('@REPLACE@',__language__(30301)),cid,702,os.path.join(IMAGES_PATH,'collections.png'))
		self.addDir(__language__(30515).replace('@NAMEREPLACE@',name).replace('@REPLACE@',__language__(30302)),cid,703,os.path.join(IMAGES_PATH,'sets.png'))
		self.addDir(__language__(30515).replace('@NAMEREPLACE@',name).replace('@REPLACE@',__language__(30303)),cid,704,os.path.join(IMAGES_PATH,'galleries.png'))
		self.addDir(__language__(30515).replace('@NAMEREPLACE@',name).replace('@REPLACE@',__language__(30304)),cid,705,os.path.join(IMAGES_PATH,'tags.png'))
		if self.authenticated(): self.addDir(__language__(30515).replace('@NAMEREPLACE@',name).replace('@REPLACE@',__language__(30305)),cid,706,os.path.join(IMAGES_PATH,'favorites.png'))
		self.addDir(__language__(30515).replace('@NAMEREPLACE@',name).replace('@REPLACE@',__language__(30306)),cid,707,os.path.join(IMAGES_PATH,'contacts.png'))
		self.addDir(__language__(30516).replace('@NAMEREPLACE@',name),cid,709,os.path.join(IMAGES_PATH,'search_photostream.png'))
		
	def GROUP(self,groupid):
		self.addPhotos(self.flickr.groups_pools_getPhotos,112,mapOption=True,group_id=groupid)
		
	def PLACE(self,woeid,page):
		self.addPhotos(self.flickr.photos_search,1022,url=woeid,page=page,woe_id=woeid,user_id='me',mapOption=True)
	
	def addLink(self,name,url,iconimage,tot=0,contextMenu=None,ltype='image'):
		#u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&name="+urllib.quote_plus(name)
		liz=xbmcgui.ListItem(name, iconImage="DefaultImage.png", thumbnailImage=iconimage)
		liz.setInfo( type=ltype, infoLabels={ "Title": name } )
		liz.setProperty( "sharing","handled" )
		if contextMenu: liz.addContextMenuItems(contextMenu)
		return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz,isFolder=False,totalItems=tot)

	def addDir(self,name,url,mode,iconimage,page=1,tot=0,userid=''):
		if userid: userid = "&userid="+urllib.quote_plus(userid)
		u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&page="+str(page)+userid+"&name="+urllib.quote_plus(name.encode('ascii','replace'))
		liz=xbmcgui.ListItem(name, 'test',iconImage="DefaultFolder.png", thumbnailImage=iconimage)
		liz.setInfo( type="image", infoLabels={"Title": name} )
		return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True,totalItems=tot)

class ImageShower(xbmcgui.Window):
	def showImage(self,image):
		self.addControl(xbmcgui.ControlImage(0,0,self.getWidth(),self.getHeight(), image, aspectRatio=2))
		
	def onAction(self,action):
		if action == 10 or action == 9: self.close()		

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
	else:
		param={}					
	return param

### Do plugin stuff --------------------------------------------------------------------------
def doPlugin():
	params=get_params()

	url = urllib.unquote_plus(params.get("url",''))
	page = int(params.get("page",'1'))
	userid = urllib.unquote_plus(params.get("userid",''))
	name = urllib.unquote_plus(params.get("name",''))
	mode = int(params.get("mode",'0'))

	#print "Mode: "+str(mode)
	#print "URL: "+str(url)
	#print "Name: "+str(name)
	#print "Page: "+str(page)

	update_dir = False
	success = True
	cache = True

	try:
		fsession = FlickrSession()
		fsession.isSlideshow = params.get('plugin_slideshow_ss','false') == 'true'
		if not fsession.authenticate():
			mode = 9999
			url = 'AUTHENTICATE'

		if page>1 or page<0: update_dir=True
		page = abs(page)

		if mode==0 or url==None or len(url)<1:
			LOG('Version: ' + __version__)
			LOG('Encoding: ' + ENCODING)
			registerAsShareTarget()
			clearDirFiles(CACHE_PATH)
			fsession.CATEGORIES()
		elif mode==1:
			fsession.PHOTOSTREAM(page)
		elif mode==2:
			fsession.COLLECTION(url,userid=userid)
		elif mode==3:
			fsession.SETS()
		elif mode==4:
			fsession.GALLERIES()
		elif mode==5:
			fsession.TAGS()
		elif mode==6:
			fsession.FAVORITES(page)
		elif mode==7:
			fsession.CONTACTS()
		elif mode==8:
			clearDirFiles(CACHE_PATH)
			fsession.PLACES(12,zoom='country')
		elif mode==9:
			fsession.SEARCH_TAGS(url,page,mode=9,userid='me')
		elif mode==10:
			fsession.SEARCH_TAGS(url,page,mode=10)
		elif mode==11:
			fsession.INTERESTING(page)
		elif mode==12:
			fsession.GROUPS()
		elif mode==13:
			fsession.SEARCH_GROUPS(url,page)
		elif mode==103:
			fsession.SET(url,page)
		elif mode==104:
			fsession.GALLERY(url,page)
		elif mode==105:
			fsession.TAG(url,page,userid=userid)
		elif mode==107:
			fsession.CONTACT(url,name)
		elif mode==112:
			fsession.GROUP(url)
		elif mode==701:
			fsession.PHOTOSTREAM(page,mode=701,userid=url)
		elif mode==702:
			fsession.COLLECTION('collections',userid=url)
		elif mode==703:
			fsession.SETS(userid=url)
		elif mode==704:
			fsession.GALLERIES(userid=url)
		elif mode==705:
			fsession.TAGS(userid=url)
		elif mode==706:
			fsession.FAVORITES(page,userid=url)
		elif mode==707:
			fsession.CONTACTS(userid=url)
		elif mode==709:
			fsession.SEARCH_TAGS(url,page,mode=709,userid=url)
		elif mode==800:
			fsession.CONTACTS_RECENT_PHOTOS()
		elif mode==1022:
			fsession.PLACE(url,page)
		elif mode==1007:
			fsession.PLACES(22,woeid=url,name=name,zoom='neighborhood')
		elif mode==1008:
			fsession.PLACES(7,woeid=url,name=name,zoom='locality')
		elif mode==1012:
			fsession.PLACES(8,woeid=url,name=name,zoom='region')
	except HTTPError,e:
		if(e.reason[1] == 504):
			xbmcgui.Dialog().ok(__language__(30502), __language__(30504))
			success = False
		else:
			ERROR('UNHANDLED HTTP ERROR',' (HTTP)')
	except URLError,e:
		LOG(e.reason)
		if(e.reason[0] == 110):
			xbmcgui.Dialog().ok(__language__(30503), __language__(30504))
			success = False
		else:
			ERROR('UNHANDLED URL ERROR',' (URL)')
	except:
		ERROR('UNHANDLED ERROR')
		
	if mode != 9999: xbmcplugin.endOfDirectory(int(sys.argv[1]),succeeded=success,updateListing=update_dir,cacheToDisc=cache)

def playVideo():
		fsession = FlickrSession()
		if not fsession.authenticate():
			return None
		vid = sys.argv[2].split('=')[-1]
		LOG('Playing video with ID: ' + vid)
		sizes = fsession.getImageUrl(vid, 'all')
		url = sizes.get('Site MP4',sizes.get('Video Original',''))
		listitem = xbmcgui.ListItem(label='flickr Video', path=url)
		listitem.setInfo(type='Video',infoLabels={"Title": 'flickr Video'})
		xbmcplugin.setResolvedUrl(handle=int(sys.argv[1]), succeeded=True, listitem=listitem)

class SavePhoto:
	def __init__(self):
		url = urllib.unquote_plus(sys.argv[2])
		savename = sys.argv[3]
		if not savename.lower().endswith('.jpg'): savename += '.jpg' #Would be better if we determined image type but it should be .jpg 99.9% of the time
		save_path = __settings__.getSetting('save_path')
		saveFullPath = os.path.join(save_path,savename)
		basePath = saveFullPath
		ct=1
		while os.path.exists(saveFullPath):
			base = os.path.splitext(basePath)[0]
			saveFullPath = base + '_%s.jpg' % ct
			ct+=1
			if ct > 99: break
		self.pd = xbmcgui.DialogProgress()
		self.pd.create(__language__(30415),__language__(30416))
		try:
			fail = False
			if save_path:
				try:
					urllib.urlretrieve(url,saveFullPath,self.progressUpdate)
				except:
					fail = True
			else:
				fail = True
				
			if fail:
				xbmcgui.Dialog().ok(__language__(30417),__language__(30418))
				__settings__.openSettings()
				save_path = __settings__.getSetting('save_path')
				try:
					urllib.urlretrieve(url,saveFullPath,self.progressUpdate)
				except:
					import traceback
					traceback.print_exc()
					xbmcgui.Dialog().ok(__language__(30419),__language__(30420))
					return
		finally:
			self.pd.close()
		xbmcgui.Dialog().ok(__language__(30412),__language__(30413).replace('@REPLACE@',os.path.basename(saveFullPath)),__language__(30414).replace('@REPLACE@',save_path))
		
	def progressUpdate(self,blocks,bsize,fsize):
		#print 'cool',blocks,bsize,fsize
		if fsize == -1 or fsize <= bsize:
			self.pd.update(0)
			#print 'test'
			return
		percent = int((float(blocks) / (fsize/bsize)) * 100)
		#print percent
		self.pd.update(percent)
		
def registerAsShareTarget():
	try:
		import ShareSocial #@UnresolvedImport
	except:
		LOG('Could not import ShareSocial')
		return
	
	target = ShareSocial.getShareTarget()
	target.addonID = 'plugin.image.flickr'
	target.name = 'flickr'
	target.importPath = 'share'
	target.provideTypes = ['feed']
	ShareSocial.registerShareTarget(target)
	LOG('Registered as share target with ShareSocial')

PLUGIN = False
if __name__ == '__main__':
	#print sys.argv
	if sys.argv[1] == 'map':
		Maps().doMap()
	elif sys.argv[1] == 'save':
		SavePhoto()
	elif sys.argv[1] == 'slideshow':
		xbmc.executebuiltin('SlideShow(plugin://plugin.image.flickr?mode=1&url=slideshow&name=photostream)')
	elif sys.argv[1] == 'reset_auth':
		fsession = FlickrSession()
		if fsession.authenticate(force=True):
			xbmcgui.Dialog().ok(__language__(30507),__language__(30506))
		else:
			xbmcgui.Dialog().ok(__language__(30520),__language__(30521))
		
	elif len(sys.argv) > 2 and sys.argv[2].startswith('?video_id'):
		playVideo()
	else:
		PLUGIN = True
		doPlugin()
