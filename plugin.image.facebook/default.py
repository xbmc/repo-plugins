#!/usr/bin/python

import facebook
import urllib, sys, os
from addon import AddonHelper

__plugin__ =  'facebook'
__author__ = 'ruuk'
__url__ = 'http://code.google.com/p/facebookphotos-xbmc/'
__date__ = '10-10-2010'
__version__ = '0.9.4'

def LOG(msg):
	try:
		print 'FACEBOOKPHOTOS: ' + msg.decode('utf-8','ignore').encode('ascii','replace')
	except:
		fb.xbmc().log('FACEBOOKPHOTOS: ' + msg.decode('utf-8','ignore').encode('ascii','replace'))
		
class GraphWrapAuthError(Exception):
	def __init__(self, type, message):
		Exception.__init__(self, message)
		self.type = type
		self.message = message

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
		except facebook.GraphAPIError,e:
			if not e.type == 'OAuthException': raise
			fail = True
			
		if fail:
			if not self.getNewToken():
				if self.access_token: raise GraphWrapAuthError('RENEW_TOKEN_FAILURE','Failed to get new token')
				else: return None
			return self.get_object(id, **args)
			
	def getNewToken(self):
		from webviewer import mechanize #@UnresolvedImport
		br = mechanize.Browser()
		br.set_handle_robots(False)
		scope = ''
		if self.scope: scope = '&scope=' + self.scope
		url = 	'https://graph.facebook.com/oauth/authorize?client_id='+self.client_id+\
				'&redirect_uri='+self.redirect+\
				'&type=user_agent&display=popup'+scope
		print url
		try:
			res = br.open(url)
			html = res.read()
		except:
			self.genericError()
			return False
		
		script = False
		try:
			#check for login form
			br.select_form(nr=0)
			print "HTML"
		except:
			self.genericError()
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
				self.genericError()
				#somethings wrong, abort
				print "FORM ERROR"
				return False
				
			script = False
			token = self.extractTokenFromURL(url)
			if not token: script = True
			
			if script:
				print "SCRIPT TOKEN"
				#no token in the url, let's try to parse it from javascript on the page
				html = res.read()
				token = self.parseTokenFromScript(html)
				
		if not self.tokenIsValid(token):
			#if script: LOG("HTML:" + html)
			return False
		
		self.access_token = token
		self.saveToken()
		return True
		
	def extractTokenFromURL(self,url):
		try:
			#we submitted the form, check the result url for the access token
			from cgi import parse_qs
			import urlparse
			token = parse_qs(urlparse.urlparse(url.replace('#','?',1))[4])['access_token'][0]
			print "URL TOKEN: %s" % token
			return token
		except:
			self.genericError()
			return None
		
	def tokenIsValid(self,token):
		if not token: return False
		if 'login_form' in token and 'standard_explanation' in token:
			reason = self.re().findall('id="standard_explanation">(?:<p>)?([^<]*)<',token)
			if reason: print reason[0]
			LOG("TOKEN: " + token)
			raise GraphWrapAuthError('LOGIN_FAILURE',reason)
			return False
		if 'html' in token or 'script' in token or len(token) > 160:
			LOG("TOKEN: " + token)
			raise GraphWrapAuthError('RENEW_TOKEN_FAILURE','Failed to get new token')
			return False
		return True
		
	def genericError(self):
		print 'ERROR: %s::%s (%d) - %s' % (self.__class__.__name__
								   , sys.exc_info()[2].tb_frame.f_code.co_name, sys.exc_info()[2].tb_lineno, sys.exc_info()[1])
								
	def parseTokenFromScript(self,html):
		return urllib.unquote_plus(html.split("#access_token=")[-1].split("&expires")[0])
		
	def saveToken(self,token=None):
		if token: self.access_token = token
		f = open(fb.TOKEN_PATH,'w')
		f.write(self.access_token)
		f.close()
			

class facebookSession(AddonHelper):
	def __init__(self):
		AddonHelper.__init__(self,'plugin.image.facebook')
		
		self.IMAGES_PATH = self.addonPath('resources/images')

		self.CACHE_PATH = self.dataPath('cache')
		if not os.path.exists(self.CACHE_PATH): os.makedirs(self.CACHE_PATH)

		self.TOKEN_PATH = self.dataPath('token')
		
		self.get_friends_photos = (self.getSetting('get_friends_photos') == "true")
		self.get_album_photos = (self.getSetting('get_album_photos') == "true")
		self.loadToken()
		self.graph = GraphWrap(self.token)
		self.setLoginData()
		self.graph.setAppData('150505371652086',scope='user_photos,friends_photos,user_photo_video_tags,friends_photo_video_tags')
		self.urlprx = None
		self.proxy = None
		
	def getToken(self):
		if self.graph.getNewToken():
			self.token = self.graph.access_token
		
	def setLoginData(self):
		login_email = self.getSetting('login_email') 
		login_pass = self.getSetting('login_pass')
		self.graph.setLogin(login_email,login_pass)
		self.hasLoginData = True
		if not (login_email and login_pass): self.hasLoginData = False
		
	def loadToken(self):
		self.token = ''
		if os.path.exists(self.TOKEN_PATH):
			f = open(self.TOKEN_PATH,'r')
			self.token = f.read()
			f.close()
		
	def CATEGORIES(self):
		self.addDir(self.lang(30004),os.path.join(self.IMAGES_PATH,'albums.png'),url='me',mode=1)
		self.addDir(self.lang(30010),os.path.join(self.IMAGES_PATH,'videos.png'),url='me',mode=3)
		self.addDir(self.lang(30005),os.path.join(self.IMAGES_PATH,'friends.png'),url='friends',mode=2)
		self.addDir(self.lang(30006),os.path.join(self.IMAGES_PATH,'photosofme.png'),url='me',mode=101)
		self.addDir(self.lang(30011),os.path.join(self.IMAGES_PATH,'videosofme.png'),url='me',mode=102)
		
	def ALBUMS(self,uid='me',name=''):
		albums = self.graph.getConnections(uid,'albums')
		tot = len(albums['data'])
		for a in albums['data']:
			aid = a.get('id','')
			fn = os.path.join(self.CACHE_PATH,aid + '.jpg') #still works even if image is not jpg - doesn't work without the extension
			tn = "https://graph.facebook.com/"+aid+"/picture?access_token=" + self.graph.access_token
			if not os.path.exists(fn):
				if self.get_album_photos: fn = self.getFile(tn,fn)
				else: fn = ''
			if not self.addDir(a.get('name',''),fn,url=aid,mode=101,tot=tot): break
		if uid != 'me':
			self.addDir(	self.lang(30012).replace('@REPLACE@',name),
							os.path.join(self.IMAGES_PATH,'videos.png'),
							url=uid,
							mode=3)
			self.addDir(self.lang(30007).replace('@REPLACE@',name),os.path.join(self.IMAGES_PATH,'photosofme.png'),url=uid,mode=101)
			self.addDir(self.lang(30013).replace('@REPLACE@',name),os.path.join(self.IMAGES_PATH,'videosofme.png'),url=uid,mode=102)
	
	
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
			fn = os.path.join(self.CACHE_PATH,uid + '.jpg') #still works even if image is not jpg - doesn't work without the extension
			tn = "https://graph.facebook.com/"+uid+"/picture?type=large&access_token=" + self.graph.access_token
			if not os.path.exists(fn):
				if self.get_friends_photos:
					try:
						fn = self.getFile(tn,fn)
					except:
						fn = ''
				else:
					fn = ''
			#fn = "https://graph.facebook.com/"+uid+"/picture?access_token=" + self.graph.access_token + "&nonsense=image.jpg" #<-- crashes XBMC
			name = show[s].get('name','')
			if not self.addDir(name,fn,url=uid,mode=1,tot=tot,name=name): break
	
	def PHOTOS(self,aid,isPaging=False):
		if isPaging:
			photos = self.graph.request(aid)
		else:
			photos = self.graph.getConnections(aid,'photos')
		tot = len(photos['data'])
		paging = photos.get('paging')
		next = None
		if paging:
			next = paging.get('next')
			prev = paging.get('previous')
			if self.areAlmostTheSame(prev,next):
				prev = None
				next = None
			if prev:
				if not self.addDir('<- %s' % self.lang(30014),os.path.join(self.IMAGES_PATH,'previous.png'),url=prev,mode=201): return
		for p in photos['data']:
			tn = p.get('picture','') + '?fix=' + str(self.time().time()) #why does this work? I have no idea. Why did I try it. I have no idea :)
			#print "BEFORE: " + tn
			tn = self.re().sub('/hphotos-\w+-\w+/\w+\.\w+/','/hphotos-ak-snc1/hs255.snc1/',tn) # this seems to get better results then using the random server
			#print "-AFTER: " + tn
			if not self.addLink(self.removeCRLF(p.get('name',p.get('id','None'))),p.get('source',''),tn,tot): return
		if next:
			if not self.addDir('%s ->' % self.lang(30015),os.path.join(self.IMAGES_PATH,'next.png'),url=next,mode=201): return
			
	def VIDEOS(self,uid,uploaded=False,isPaging=False):
		if isPaging:
			videos = self.graph.request(uid)
		else:
			if uploaded: videos = self.graph.getConnections(uid,'videos/uploaded')
			else: videos = self.graph.getConnections(uid,'videos')
		tot = len(videos['data'])
		paging = videos.get('paging')
		next = None
		if paging:
			next = paging.get('next')
			prev = paging.get('previous')
			if self.areAlmostTheSame(prev,next):
				prev = None
				next = None
			if prev:
				if not self.addDir('<- %s' % self.lang(30014),os.path.join(self.IMAGES_PATH,'previous.png'),url=prev,mode=202): return
		for v in videos['data']:
			tn = v.get('picture','') + '?fix=' + str(self.time().time()) #why does this work? I have no idea. Why did I try it. I have no idea :)
			if not self.addLink(self.removeCRLF(v.get('name',v.get('id','None'))),v.get('source',''),tn,tot): return
		if next:
			if not self.addDir('%s ->' % self.lang(30015),os.path.join(self.IMAGES_PATH,'next.png'),url=next,mode=202): return
			
	def areAlmostTheSame(self,first,second):
		if not first or not second: return False
		first = self.re().sub('(\d{4}-\d{2}-\d{2}T\d{2}%3A\d{2}%3A\d)\d(%2B\d{4})',r'\1x\2',first)
		second = self.re().sub('(\d{4}-\d{2}-\d{2}T\d{2}%3A\d{2}%3A\d)\d(%2B\d{4})',r'\1x\2',second)
		return first == second
	
	def removeCRLF(self,text):
		return " ".join(text.split())
		
	def makeAscii(self,name):
		return name.encode('ascii','replace')
	
	def doPlugin(self):
		mode = self.getParamInt('mode',None)
		url = self.getParamString('url',None)
		name = self.getParamString('name',None)
	
		update_dir = False
		success = True
		cache = True
		
		if not self.hasLoginData:
			self.openSettings()
			self.setLoginData()
			
		if not self.token:
			self.xbmcgui().Dialog().ok(self.lang(30101),self.lang(30102),self.lang(30103),self.lang(30104))
			self.xbmcplugin().endOfDirectory(int(sys.argv[1]),succeeded=success,updateListing=update_dir,cacheToDisc=cache)
			token = getAuth()
			if not token: self.getToken()
			return
			
		if not self.hasLoginData:
			self.xbmcgui().Dialog().ok(self.lang(30105),self.lang(30106),self.lang(30107))
			success = False
		elif not self.token:
			self.xbmcgui().Dialog().ok(self.lang(30108),self.lang(30109),self.lang(30110))
			success = False
		elif mode==None or url==None or len(url)<1:
			self.CATEGORIES()
		elif mode==1:
			self.ALBUMS(url,name)
		elif mode==2:
			self.FRIENDS()
		elif mode==3:
			self.VIDEOS(url,uploaded=True)
		elif mode==101:
			self.PHOTOS(url)
		elif mode==102:
			self.VIDEOS(url)
		elif mode==201:
			self.PHOTOS(url,isPaging=True)
			update_dir=True
		elif mode==202:
			self.VIDEOS(url,isPaging=True)
			update_dir=True
			
		self.xbmcplugin().endOfDirectory(int(sys.argv[1]),succeeded=success,updateListing=update_dir,cacheToDisc=cache)

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

def getAuth():
	redirect = urllib.quote('http://2ndmind.com/facebookphotos/complete.html')
	scope = urllib.quote('user_photos,friends_photos,user_photo_video_tags,friends_photo_video_tags,user_videos,friends_videos')
	url = 'https://graph.facebook.com/oauth/authorize?client_id=150505371652086&redirect_uri=%s&type=user_agent&scope=%s' % (redirect,scope)
	import xbmcplugin #@UnresolvedImport
	xbmcplugin.endOfDirectory(int(sys.argv[1]),succeeded=False)
	from webviewer import webviewer #@UnresolvedImport
	url,html = webviewer.getWebResult(url,autoForms=[{'action':'login.php'},{'action':'uiserver.php'}]) #@UnusedVariable
	token = fb.graph.extractTokenFromURL(url)
	if fb.graph.tokenIsValid(token):
		fb.graph.saveToken(token)
		return token
	return None
	

### Do plugin stuff --------------------------------------------------------------------------

try:
	fb = facebookSession()
	fb.doPlugin()
except GraphWrapAuthError,e:
	import xbmcgui,xbmcaddon #@UnresolvedImport
	__addon__ = xbmcaddon.Addon(id='plugin.image.facebook')
	__language__ = __addon__.getLocalizedString

	if e.type == 'LOGIN_FAILURE':
		xbmcgui.Dialog().ok(__language__(30115),__language__(30116),e.message)
	else:
		xbmcgui.Dialog().ok(__language__(30111),__language__(30112),__language__(30113),__language__(30114))
		token = getAuth()
		if not token: facebookSession().getToken()
