#!/usr/bin/python

import flickrapi
import urllib
import xbmc, xbmcgui, xbmcplugin, xbmcaddon
import sys, os
from urllib2 import HTTPError, URLError

__plugin__ =  'flickr'
__author__ = 'ruuk'
__url__ = 'http://2ndmind.com'
__date__ = '09-8-2010'
__version__ = '0.5.0'
__settings__ = xbmcaddon.Addon(id='plugin.image.flickr')
__language__ = __settings__.getLocalizedString

IMAGES_PATH = xbmc.translatePath( os.path.join( os.getcwd(), 'resources', 'images' ) )
CACHE_PATH = xbmc.translatePath('special://profile/addon_data/plugin.image.flickr/cache/')

if not os.path.exists(CACHE_PATH): os.makedirs(CACHE_PATH)

class flickrPLUS(flickrapi.FlickrAPI):
	def walk_photos_by_page(self, method, **params):
			rsp = method(**params) 

			photoset = rsp.getchildren()[0]
			page = int(photoset.attrib.get('page','1'))
			pages = int(photoset.attrib.get('pages','1'))
			perpage = int(photoset.attrib.get('perpage','1'))
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

	
class FlickrSession:
	API_KEY = '0a802e6334304794769996c84c57d187'
	API_SECRET = '655ce70e86ac412e'
	
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
		self.username = username
		self.user_id = None
		self.loadSettings()
		
	def loadSettings(self):
		self.username = __settings__.getSetting('flickr_username')
		self.defaultThumbSize = self.getDisplayValue(__settings__.getSetting('default_thumb_size'))
		self.defaultDisplaySize = self.getDisplayValue(__settings__.getSetting('default_display_size'))
		mpp = __settings__.getSetting('max_per_page')
		mpp = [10,20,30,40,50,75,100,200,500][int(mpp)]
		self.max_per_page = mpp
	
	def getDisplayValue(self,index):
		return self.DISPLAY_VALUES[int(index)]
		
	def doTokenDialog(self,frob,perms):
		dialog = xbmcgui.Dialog()
		ok = dialog.ok('Authorize flickrXBMC','Go to: 2ndmind.com/flickrXBMC', 'follow the instructions, then click OK')
		keyboard = xbmc.Keyboard('','Enter the email address here:')
		keyboard.doModal()
		if (keyboard.isConfirmed()):
			email = keyboard.getText()
		keyboard = xbmc.Keyboard('','Enter the code:')
		keyboard.doModal()
		if (keyboard.isConfirmed()):
			code = keyboard.getText()
		try:
			f = urllib.urlopen("http://2ndmind.com/flickrxbmc/index.py?gettoken="+email+'-'+code)
			token = f.read()
			f.close()
			if not token: raise
		except:
			dialog = xbmcgui.Dialog()
			ok = dialog.ok('Error fetching token', '')
			xbmcplugin.endOfDirectory(int(sys.argv[1]))
		self.flickr.token_cache.token = token

	def authenticate(self):
		#try:
		self.flickr = flickrPLUS(self.API_KEY,self.API_SECRET)
		(token, frob) = self.flickr.get_token_part_one(perms='read',auth_callback=self.doTokenDialog)
		#if not token:
		#	token = doTokenDialog()
		#self.flickr.get_token_part_two((token, frob))
		if self.username:
			user = self.flickr.people_findByUsername(username=self.username)
			self.user_id = user.findall('*')[0].get('id')
		else:
			rsp = self.flickr.auth_checkToken(auth_token=token,format='xmlnode')
			user = rsp.auth[0].user[0]
			self.user_id = user.attrib.get('nsid')
			self.username = user.attrib.get('username')
			if self.username: __settings__.setSetting('flickr_username',self.username)
				
		#except:
		#	dialog = xbmcgui.Dialog()
		#	ok = dialog.ok('Authentication Error', '?')
		#	xbmcplugin.endOfDirectory(int(sys.argv[1]))
			
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
		
	def addPhotos(self,method,mode,url='BLANK',page='1',**kwargs):
		page = int(page)
		
		#Add Previous Header if necessary
		if page > 1:
			if page == 2: self.addDir('<- Previous ' + str(self.max_per_page) + ' photos',url,mode,os.path.join(IMAGES_PATH,'previous.png'),page='-1',userid=kwargs.get('userid',''))
			else: self.addDir('<- Previous ' + str(self.max_per_page) + ' photos',url,mode,os.path.join(IMAGES_PATH,'previous.png'),page=str(page-1),userid=kwargs.get('userid',''))
		info_list = []
		extras = self.SIZE_KEYS[self.defaultThumbSize] + ',' + self.SIZE_KEYS[self.defaultDisplaySize]
		
		#Walk photos
		ct=1
		for photo in self.flickr.walk_photos_by_page(method,page=page,per_page=self.max_per_page,extras=extras,**kwargs):
			ct+=1
			self.addPhoto(	photo.get('title'),
							photo.get('id'),
							photo.get(self.SIZE_KEYS[self.defaultThumbSize]),
							photo.get(self.SIZE_KEYS[self.defaultDisplaySize]))
			
		#Add Next Footer if necessary
		#print "PAGES: " + str(page) + " " + str(self.flickr.TOTAL_PAGES) + " " + self.flickr.TOTAL_ON_LAST_PAGE
		if ct >= self.max_per_page:
			next = '('+str(page*self.max_per_page)+'/'+str(self.flickr.TOTAL)+') '
			if page + 1 == self.flickr.TOTAL_PAGES:
				if self.flickr.TOTAL_ON_LAST_PAGE: next += 'Last ' + str(self.flickr.TOTAL_ON_LAST_PAGE)
				else: next += 'Last ' + str(self.max_per_page)
			else: 
				next += 'Next ' + str(self.max_per_page)
			if page < self.flickr.TOTAL_PAGES: self.addDir(next + ' photos ->',url,mode,os.path.join(IMAGES_PATH,'next.png'),page=str(page+1),userid=kwargs.get('userid',''))
		
	def addPhoto(self,title,pid,thumb,display):
		if not (thumb and display):
			urls = self.getImageUrl(pid,label='all')
			display = urls.get(self.defaultDisplaySize,urls.get('Original',''))
			thumb = urls.get(self.defaultThumbSize,urls.get('Square',''))
			if not display:
				rd = self.DISPLAY_VALUES[:]
				rd.reverse()
				for s in rd:
					if urls.get(s):
						display = urls.get(s)
						break
		self.addLink(title,display,thumb,tot=self.flickr.TOTAL_ON_PAGE)
		
	def CATEGORIES(self):
		self.addDir(__language__(30300),'photostream',1,os.path.join(IMAGES_PATH,'photostream.png'))
		self.addDir(__language__(30301),'collections',2,os.path.join(IMAGES_PATH,'collections.png'))
		self.addDir(__language__(30302),'sets',3,os.path.join(IMAGES_PATH,'sets.png'))
		self.addDir(__language__(30303),'galleries',4,os.path.join(IMAGES_PATH,'galleries.png'))
		self.addDir(__language__(30304),'tags',5,os.path.join(IMAGES_PATH,'tags.png'))
		self.addDir(__language__(30307),'places',8,os.path.join(IMAGES_PATH,'places.png'))
		self.addDir(__language__(30305),'favorites',6,os.path.join(IMAGES_PATH,'favorites.png'))
		self.addDir(__language__(30306),'contacts',7,os.path.join(IMAGES_PATH,'contacts.png'))
		self.addDir(__language__(30308),'@@search@@',9,os.path.join(IMAGES_PATH,'search_photostream.png'))
		self.addDir(__language__(30309),'@@search@@',10,os.path.join(IMAGES_PATH,'search_flickr.png'))
		self.addDir(__language__(30310),'interesting',11,os.path.join(IMAGES_PATH,'interesting.png'))
		
	def PHOTOSTREAM(self,page,mode=1,userid='me'):
		self.addPhotos(self.flickr.photos_search,mode,url=userid,page=page,user_id=userid)
		
	def COLLECTION(self,cid,userid=None):
		if cid == 'collections': cid = 0
		mode,cols = self.getCollectionsInfoList(cid=cid,userid=userid)
		total = len(cols)
		for c in cols:
			self.addDir(c['title'],c['id'],mode,c['tn'],tot=total,userid=userid)
			
	def SETS(self,mode=103,userid=None):
		sets = self.getSetsInfoList(userid=userid)
		total = len(sets)
		for s in sets:
			self.addDir(s['title']+' ('+s['count']+')',s['id'],mode,s['tn'],tot=total)
	
	def GALLERIES(self,userid=None):
		galleries = self.getGalleriesInfoList(userid=userid)
		for g in galleries:
			self.addDir(g.get('title',''),g.get('id'),104,g.get('tn'),tot=len(galleries))
	
	def TAGS(self,userid=''):
		tags = self.getTagsList(userid=userid)
		for t in tags:
			self.addDir(t,t,105,'',tot=len(tags),userid=userid)
			
	def PLACES(self,pid,woeid=None,name='',zoom='2'):
		places = self.getPlacesInfoList(pid,woeid=woeid)
		
		#If there are no places in this place id level, show all the photos
		if not places:
			self.PLACE(woeid,1)
			return
			
		if woeid and len(places) > 1: self.addDir(__language__(30500)+' '+name,woeid,1022,'')
		idx=0
		for p in places:
			count = p.get('count','0')
			#tn, x = urllib.urlretrieve("http://ojw.dev.openstreetmap.org/StaticMap/?lat="+p.get('lat','0')+"&lon="+p.get('lon','0')+"&z=2&w=256&h=256&show=1&fmt=png")
			#tn,x  = urllib.urlretrieve("http://maps.google.com/maps/api/staticmap?center="+p.get('lat','0')+","+p.get('lon','0')+"&zoom="+zoom+"&size=256x256&sensor=false&maptype=hybrid&format=jpg",os.path.join(CACHE_PATH,str(idx)+'.jpg'))
			#BteTjhnV34E7M.r_gjDLCI33rmG0FL7TFPCMF7LHEleA_iKm6S_rEjpCmns-
			#tn = "http://maps.google.com/maps/api/staticmap?center=40.714728,-73.998672&zoom=12&size=256x256&sensor=false&maptype=hybrid"
			#xml = urllib.urlopen("http://local.yahooapis.com/MapsService/V1/mapImage?appid=BteTjhnV34E7M.r_gjDLCI33rmG0FL7TFPCMF7LHEleA_iKm6S_rEjpCmns-&latitude="+p.get('lat','0')+"&longitude="+p.get('lon','0')+"&image_height=256&image_width=256&zoom=10").read()
			#tn = xml.split('</Result>')[0].split('">')[1]
			#tn = urllib.unquote_plus(tn)
			#print "TEST: "+tn
			#urllib.urlretrieve(tn,'test.png')
			#tn="http://gws.maps.yahoo.com/mapimage?MAPDATA=B.KuOud6wXXC3vi5X0zQEdMkX1ubUTsq.MWWDhhCYyi9fXv5J1oRq1gn7GILfmqt93QGvUGHqQx0AOGf7YQW_P_iYvB8s_t1GQXG5dxj9TW76FE-&mvt=m&cltype=onnetwork&.intl=us&appid=BteTjhnV34E7M.r_gjDLCI33rmG0FL7TFPCMF7LHEleA_iKm6S_rEjpCmns-&oper=&_proxy=ydn,xml"
			self.addDir(p.get('place','')+' ('+count+')',p.get('woeid'),1000 + pid,'',tot=len(places))
			idx+=1
		
	def FAVORITES(self,page,userid=None):
		self.addPhotos(self.flickr.favorites_getList,6,page=page,user_id=userid)
		
	def CONTACTS(self,userid=None):
		contacts = self.getContactsInfoList(userid=userid)
		total = len(contacts)
		for c in contacts:
			self.addDir(c['username'],c['id'],107,c['tn'],tot=total
			
			)
			
	def SEARCH_TAGS(self,tags,page,mode=9,userid=None):
		if tags == '@@search@@' or tags == userid:
			keyboard = xbmc.Keyboard('','Enter search tags:')
			keyboard.doModal()
			if (keyboard.isConfirmed()):
				tags = keyboard.getText()
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
		self.addDir(name+"'s "+ __language__(30300),cid,701,os.path.join(IMAGES_PATH,'photostream.png'))
		self.addDir(name+"'s "+ __language__(30301),cid,702,os.path.join(IMAGES_PATH,'collections.png'))
		self.addDir(name+"'s "+ __language__(30302),cid,703,os.path.join(IMAGES_PATH,'sets.png'))
		self.addDir(name+"'s "+ __language__(30303),cid,704,os.path.join(IMAGES_PATH,'galleries.png'))
		self.addDir(name+"'s "+ __language__(30304),cid,705,os.path.join(IMAGES_PATH,'tags.png'))
		self.addDir(name+"'s "+ __language__(30305),cid,706,os.path.join(IMAGES_PATH,'favorites.png'))
		self.addDir(name+"'s "+ __language__(30306),cid,707,os.path.join(IMAGES_PATH,'contacts.png'))
		self.addDir(__language__(30308),cid,709,os.path.join(IMAGES_PATH,'search_photostream.png'))
		
	def PLACE(self,woeid,page):
		self.addPhotos(self.flickr.photos_search,1022,url=woeid,page=page,woe_id=woeid,user_id='me')
	
	def addLink(self,name,url,iconimage,tot=0):
		ok=True
		#u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&name="+urllib.quote_plus(name)
		liz=xbmcgui.ListItem(name, iconImage="DefaultImage.png", thumbnailImage=iconimage)
		liz.setInfo( type="image", infoLabels={ "Title": name } )
		ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz,isFolder=False,totalItems=tot)
		return ok


	def addDir(self,name,url,mode,iconimage,page=1,tot=0,userid=''):
		if userid: userid = "&userid="+urllib.quote_plus(userid)
		u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&page="+str(page)+userid+"&name="+urllib.quote_plus(name)
		ok=True
		liz=xbmcgui.ListItem(name, 'test',iconImage="DefaultFolder.png", thumbnailImage=iconimage)
		liz.setInfo( type="image", infoLabels={"Title": name} )
		ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True,totalItems=tot)
		return ok


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
        
### GET THE PARAMS --------------------------------------------------------------------------
params=get_params()
url=None
name=None
mode=None
page=1
userid=''

try:
        url=urllib.unquote_plus(params["url"])
except:
        pass
try:
        page=int(params["page"])
except:
        pass
try:
        userid=urllib.unquote_plus(params["userid"])
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
print "Page: "+str(page)

update_dir = False

try:
	fsession = FlickrSession()
	fsession.authenticate()

	if page>1 or page<0: update_dir=True
	page = abs(page)

	if mode==None or url==None or len(url)<1:
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
		fsession.PLACES(12)
	elif mode==9:
		fsession.SEARCH_TAGS(url,page,mode=9,userid='me')
	elif mode==10:
		fsession.SEARCH_TAGS(url,page,mode=10)
	elif mode==11:
		fsession.INTERESTING(page)
	elif mode==103:
		fsession.SET(url,page)
	elif mode==104:
		fsession.GALLERY(url,page)
	elif mode==105:
		fsession.TAG(url,page,userid=userid)
	elif mode==107:
		fsession.CONTACT(url,name)
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
	elif mode==1022:
		fsession.PLACE(url,page)
	elif mode==1007:
		fsession.PLACES(22,woeid=url,name=name,zoom='10')
	elif mode==1008:
		fsession.PLACES(7,woeid=url,name=name,zoom='7')
	elif mode==1012:
		fsession.PLACES(8,woeid=url,name=name,zoom='4')
except HTTPError,e:
	if(e.reason[1] == 504):
		dialog = xbmcgui.Dialog()
		ok = dialog.ok('HTTP Timeout', 'Try again.')
	else:
		raise
except URLError,e:
	print e.reason
	if(e.reason[0] == 110):
		dialog = xbmcgui.Dialog()
		ok = dialog.ok('Connection Timeout', 'Try again.')
	else:
		raise
	
xbmcplugin.endOfDirectory(int(sys.argv[1]),updateListing=update_dir)
