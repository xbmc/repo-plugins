#!/usr/bin/python

import facebook
import urllib, urlparse, sys, os, time, re
from cgi import parse_qs
import xbmc, xbmcgui, xbmcplugin, xbmcaddon


__plugin__ =  'facebook'
__author__ = 'ruuk'
__url__ = 'http://code.google.com/p/facebookphotos-xbmc/'
__date__ = '10-04-2010'
__version__ = '0.9.2'
__settings__ = xbmcaddon.Addon(id='plugin.image.facebook')
__language__ = __settings__.getLocalizedString

IMAGES_PATH = xbmc.translatePath( os.path.join( os.getcwd(), 'resources', 'images' ) )

CACHE_PATH = xbmc.translatePath('special://profile/addon_data/plugin.image.facebook/cache/')
if not os.path.exists(CACHE_PATH): os.makedirs(CACHE_PATH)

TOKEN_PATH = xbmc.translatePath('special://profile/addon_data/plugin.image.facebook/token')

class GraphWrapAuthError(Exception):
    def __init__(self, type, message):
        Exception.__init__(self, message)
        self.type = type
        
class GraphWrap(facebook.GraphAPI):
	def setLogin(self,email,passw):
		self.login_email = email
		self.login_pass = passw
		
	def setAppData(self,aid,redirect='http://www.facebook.com/connect/login_success.html',scope=None):
		self.client_id = aid
		self.redirect = redirect
		self.scope = scope
		
	def checkHasPermission(self,permission):
		import simplejson
		url = 'https://api.facebook.com/method/users.hasAppPermission?format=json&ext_perm='+permission+'&access_token='+self.access_token
		fobj = urllib.urlopen(url)
		try:
			response = simplejson.loads(fobj.read())
		finally:
			fobj.close()
		return (response == 1)
		
	def checkIsAppUser(self):
		import simplejson
		url = 'https://api.facebook.com/method/users.isAppUser?format=json&access_token='+self.access_token
		fobj = urllib.urlopen(url)
		try:
			response = simplejson.loads(fobj.read())
		finally:
			fobj.close()
		return response
		
	def getConnections(self, id, connection_name, **args):
		fail = False
		try:
			return self.get_connections(id, connection_name, **args)
		except facebook.GraphAPIError,e:
			print e.type
			if not e.type == 'OAuthException': raise
			fail = True

		if fail:
			if not self.getNewToken():
				if self.access_token: raise GraphWrapAuthError('RENEW_TOKEN_FAILURE','Failed to get new token')
				else: return None
			return self.get_connections(id, connection_name, **args)
			
	def getObject(self, id, **args):
		fail = False
		try:
			return self.get_object(id, **args)
		except GraphAPIError,e:
			if not e.type == 'OAuthException': raise
			fail = True
			
		if fail:
			if not self.getNewToken():
				if self.access_token: raise GraphWrapAuthError('RENEW_TOKEN_FAILURE','Failed to get new token')
				else: return None
			return self.get_object(id, **args)
			
	def getNewToken(self):
		import mechanize
		br = mechanize.Browser()
		br.set_handle_robots(False)
		scope = ''
		if self.scope: scope = '&scope=' + self.scope
		url = 	'https://graph.facebook.com/oauth/authorize?client_id='+self.client_id+\
				'&redirect_uri='+self.redirect+\
				'&type=user_agent&display=popup'+scope
		print url
		res = br.open(url)
		html = res.read()
		
		script = False
		try:
			#check for login form
			br.select_form(nr=0)
			print "HTML"
		except:
			script = True
			print "SCRIPT"
			
		if script:
			#no form, maybe we're logged in and the token is in javascript on the page
			token = self.parseTokenFromScript(html)
		else:
			try:
				#fill out the form and submit
				br['email'] = self.login_email
				br['pass'] = self.login_pass
				res = br.submit()
				url = res.geturl()
				print "FORM"
			except:
				#somethings wrong, abort
				print "FORM ERROR"
				return False
				
			script = False
			try:
				#we submitted the form, check the result url for the access token
				token = parse_qs(urlparse.urlparse(url)[4])['access_token']	
			except:
				script = True
			
			if script:
				#no token in the url, let's try to parse it from javascript on the page
				html = res.read()
				token = self.parseTokenFromScript(html)
		
		if 'html' in token or len(token) > 100: raise GraphWrapAuthError('RENEW_TOKEN_FAILURE','Failed to get new token')
		self.access_token = token
		self.saveToken()
		return True
		
	def parseTokenFromScript(self,html):
		return urllib.unquote_plus(html.split("#access_token=")[-1].split("&expires")[0])
		
	def saveToken(self):
		f = open(TOKEN_PATH,'w')
		f.write(self.access_token)
		f.close()
			

class facebookSession:
	def __init__(self):
		self.get_friends_photos = (__settings__.getSetting('get_friends_photos') == "true")
		self.get_album_photos = (__settings__.getSetting('get_album_photos') == "true")
		self.loadToken()
		self.graph = GraphWrap(self.token)
		self.setLoginData()
		self.graph.setAppData('150505371652086',scope='user_photos,friends_photos,user_photo_video_tags,friends_photo_video_tags')

	def getToken(self):
		if self.graph.getNewToken():
			self.token = self.graph.access_token
		
	def setLoginData(self):
		login_email = __settings__.getSetting('login_email') 
		login_pass = __settings__.getSetting('login_pass')
		self.graph.setLogin(login_email,login_pass)
		self.hasLoginData = True
		if not (login_email and login_pass): self.hasLoginData = False
		
	def loadToken(self):
		self.token = ''
		if os.path.exists(TOKEN_PATH):
			f = open(TOKEN_PATH,'r')
			self.token = f.read()
			f.close()
			
	def addLink(self,name,url,iconimage,tot=0):
		ok=True
		#u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&name="+urllib.quote_plus(name)
		liz=xbmcgui.ListItem(self.removeCRLF(name), iconImage="DefaultImage.png", thumbnailImage=iconimage)
		liz.setInfo( type="image", infoLabels={ "Title": name } )
		#if contextMenu: liz.addContextMenuItems(contextMenu)
		return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz,isFolder=False,totalItems=tot)

	def addDir(self,name,url,mode,iconimage,page=1,tot=0):
		name = self.removeCRLF(name)
		u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&page="+str(page)+"&name="+urllib.quote_plus(self.makeAscii(name))
		ok=True
		liz=xbmcgui.ListItem(name, 'test',iconImage="DefaultFolder.png", thumbnailImage=iconimage)
		liz.setInfo( type="image", infoLabels={"Title": name} )
		return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True,totalItems=tot)
		
	def CATEGORIES(self):
		self.addDir(__language__(30004),'me',1,os.path.join(IMAGES_PATH,'albums.png'))
		self.addDir(__language__(30010),'me',3,os.path.join(IMAGES_PATH,'videos.png'))
		self.addDir(__language__(30005),'friends',2,os.path.join(IMAGES_PATH,'friends.png'))
		self.addDir(__language__(30006),'me',101,os.path.join(IMAGES_PATH,'photosofme.png'))
		self.addDir(__language__(30011),'me',102,os.path.join(IMAGES_PATH,'videosofme.png'))
		
	def ALBUMS(self,uid='me',name=''):
		albums = self.graph.getConnections(uid,'albums')
		tot = len(albums['data'])
		for a in albums['data']:
			aid = a.get('id','')
			fn = os.path.join(CACHE_PATH,aid + '.jpg') #still works even if image is not jpg - doesn't work without the extension
			tn = "https://graph.facebook.com/"+aid+"/picture?access_token=" + self.graph.access_token
			if not os.path.exists(fn):
				if self.get_album_photos: fn,ignore  = urllib.urlretrieve(tn,fn)
				else: fn = ''
			if not self.addDir(a.get('name',''),aid,101,fn,tot=tot): break
		if uid != 'me':
			self.addDir(__language__(30012).replace('@REPLACE@',name),uid,3,os.path.join(IMAGES_PATH,'videos.png'))
			self.addDir(__language__(30007).replace('@REPLACE@',name),uid,101,os.path.join(IMAGES_PATH,'photosofme.png'))
			self.addDir(__language__(30013).replace('@REPLACE@',name),uid,102,os.path.join(IMAGES_PATH,'videosofme.png'))
	
	
	def FRIENDS(self):
		friends = self.graph.getConnections('me','friends')
		srt = []
		show = {}
		for f in friends['data']:
			name = f.get('name','')
			s = name.rsplit(' ',1)[-1] + name.rsplit(' ',1)[0]
			srt.append(s)
			show[s] = f
			srt.sort()
		tot = len(srt)
		for s in srt:
			uid = show[s].get('id','')
			fn = os.path.join(CACHE_PATH,uid + '.jpg') #still works even if image is not jpg - doesn't work without the extension
			tn = "https://graph.facebook.com/"+uid+"/picture?type=large&access_token=" + self.graph.access_token
			if not os.path.exists(fn):
				if self.get_friends_photos: fn,ignore  = urllib.urlretrieve(tn,fn)
				else: fn = ''
			#fn = "https://graph.facebook.com/"+uid+"/picture?access_token=" + self.graph.access_token + "&nonsense=image.jpg" #<-- crashes XBMC
			if not self.addDir(show[s].get('name',''),uid,1,fn,tot=tot): break
	
	def PHOTOS(self,aid):
		photos = self.graph.getConnections(aid,'photos')
		tot = len(photos['data'])
		for p in photos['data']:
			tn = p.get('picture','') + '?fix=' + str(time.time()) #why does this work? I have no idea. Why did I try it. I have no idea :)
			#print "BEFORE: " + tn
			tn = re.sub('/hphotos-\w+-\w+/\w+\.\w+/','/hphotos-ak-snc1/hs255.snc1/',tn) # this seems to get better results then using the random server
			#print "-AFTER: " + tn
			if not self.addLink(p.get('name',p.get('id','None')),p.get('source',''),tn,tot): break
			
	def VIDEOS(self,uid,uploaded=False):
		if uploaded: videos = self.graph.getConnections(uid,'videos/uploaded')
		else: videos = self.graph.getConnections(uid,'videos')
		tot = len(videos['data'])
		for v in videos['data']:
			tn = v.get('picture','') + '?fix=' + str(time.time()) #why does this work? I have no idea. Why did I try it. I have no idea :)
			if not self.addLink(v.get('name',v.get('id','None')),v.get('source',''),tn,tot): break
			
	def removeCRLF(self,text):
		return " ".join(text.split())
		
	def makeAscii(self,name):
		return name.encode('ascii','replace')

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

	fb = facebookSession()
	
	if not fb.hasLoginData:
		__settings__.openSettings()
		fb.setLoginData()
		
	if not fb.token:
		xbmcgui.Dialog().ok(__language__(30101),__language__(30102).replace('@REPLACE@','http://2ndmind.com/facebookphotos'),__language__(30103),__language__(30104))
		fb.getToken()
		
	if not fb.hasLoginData:
		xbmcgui.Dialog().ok(__language__(30105),__language__(30106),__language__(30107))
		success = False
	elif not fb.token:
		xbmcgui.Dialog().ok(__language__(30108),__language__(30109),__language__(30110))
		success = False
	elif mode==None or url==None or len(url)<1:
		fb.CATEGORIES()
	elif mode==1:
		fb.ALBUMS(url,name)
	elif mode==2:
		fb.FRIENDS()
	elif mode==3:
		fb.VIDEOS(url,uploaded=True)
	elif mode==101:
		fb.PHOTOS(url)
	elif mode==102:
		fb.VIDEOS(url)
		
	xbmcplugin.endOfDirectory(int(sys.argv[1]),succeeded=success,updateListing=update_dir,cacheToDisc=cache)
try:
	doPlugin()
except GraphWrapAuthError,e:
	xbmcgui.Dialog().ok(__language__(30111),__language__(30112),__language__(30113).replace('@REPLACE@','http://2ndmind.com/facebookphotos'),__language__(30114))
