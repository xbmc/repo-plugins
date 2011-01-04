# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Conector para Megalive by Bandavi
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------


import re, sys, os
import urlparse, urllib, urllib2,string
import os.path
import sys
import xbmc
import xbmcplugin
import xbmcgui
import config
import logger

COOKIEFILE               = os.path.join (config.DATA_PATH , "cookies.lwp")
_VALID_URL               = r'(?:(?:http://)?(?:\w+\.)?megalive\.com/(?:(?:v/)|\?(?:s=.+?&(?:amp;)?)?((?:(?:v\=))))?)?([A-Z0-9]{8})?$'
_TEMPLATE_URL            = 'http://www.megalive.com/?v=%s'
_SWF_URL                 = 'http://www.megalive.com/ml_player.swf'
_TEMPLATE_LIVE_URL       = "%s/videochat playpath=stream_%s swfurl=%s swfvfy=true pageUrl=%s"
_STREAM_REQUEST_URL      = "http://www.megalive.com/xml/stream.php?v=%s"
_USER_STREAM_REQUEST_URL = "http://www.megalive.com/xml/stream.php?v=%s&u=%s"

logger.debug("[megalive.py] Cookiefile="+COOKIEFILE) 



DEBUG = False


def getcode(mega):
	xbmc.output("[megalive.py] mega="+mega)
	mobj = re.match(_VALID_URL, mega)
	if mobj is None:
		xbmc.output("Invalid url: "+mega)
		server_response("Invalid url :",mega)
		return ""
	mega =mobj.group(2)
	xbmc.output("[megalive.py] mega="+mega)
	return mega

def Megalive(mega):
	xbmc.output("[megalive.py] Megalive")
	link = getLiveUrl(mega)
	xbmc.output("[megalive.py] link="+link)
		
	return link


def getLiveUrl(code,thumb=0):
	xbmc.output("[megalive.py] getLiveUrl")
	
	code=getcode(code)
	if code == "":
		if thumb == 0:
			return ""
		else:
			return "",""

	image = ""
	modoPremium = config.getSetting("megavideopremium")
	megalivelogin = config.getSetting("megavideouser")
	
	if len(megalivelogin)<=0:
		xbmc.output("[megalive.py] usando modo normal sin cuenta")
		req = urllib2.Request(_STREAM_REQUEST_URL % (code))
		req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.8.1.14) Gecko/20080404 Firefox/2.0.0.14')
		req.add_header('Referer', _TEMPLATE_URL % (code))
		page = urllib2.urlopen(req);response=page.read();page.close()
		try:
			rtmp  = re.compile('rtmp="(.+?)"').findall(response)[0]
			image = re.compile('image="(.+?)"').findall(response)[0]
			id    = re.compile('id="(.+?)"').findall(response)[0]
			livelink  = _TEMPLATE_LIVE_URL % (rtmp,id,_SWF_URL,_TEMPLATE_URL % (code))
			thumbnail = image			
			
		except:
			livelink  = ""
			thumbnail = ""
			sentence1 = re.compile(r'sentence1="(.+?)"').findall(response)[0]
			
			try:
				sentence2 = re.compile(r'sentence2="(.+?)"').findall(response)[0]
			except:
				sentence2 = ""
			server_response(sentence1,sentence2)			

	else:
		xbmc.output("[megalive.py] usando modo Usuario con cuenta ")
		megalivecookie = config.getSetting("megavideocookie")
		if DEBUG: xbmc.output("[megalive.py] megalivecookie=#"+megalivecookie+"#")

		xbmc.output("[megalive.py] Averiguando cookie...")
		
		if DEBUG: xbmc.output("[megalive.py] megaliveuser=#"+megalivelogin+"#")

		megalivepassword = config.getSetting("megavideopassword")
		if DEBUG: xbmc.output("[megalive.py] megalivepassword=#"+megalivepassword+"#")

		megalivecookie = GetMegaliveUser(megalivelogin, megalivepassword)
		if DEBUG: xbmc.output("[megalive.py] megalivecookie=#"+megalivecookie+"#")

		if len(megalivecookie) == 0:
			advertencia = xbmcgui.Dialog()
			resultado = advertencia.ok('Cuenta de Megalive errónea' , 'La cuenta de Megalive que usas no es válida' , 'Comprueba el login y password en la configuración')
			if thumb == 0:return ""
			else:return "",""
		req = urllib2.Request(_USER_STREAM_REQUEST_URL % (code,megalivecookie))
		req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.8.1.14) Gecko/20080404 Firefox/2.0.0.14')
		req.add_header('Referer', _TEMPLATE_URL % (code))
		page = urllib2.urlopen(req);response=page.read();page.close()
		
		try:
			rtmp  = re.compile('rtmp="(.+?)"').findall(response)[0]
			image = re.compile('image="(.+?)"').findall(response)[0]
			id    = re.compile('id="(.+?)"').findall(response)[0]
			livelink = _TEMPLATE_LIVE_URL % (rtmp,id,_SWF_URL,_TEMPLATE_URL % (code))
			thumbnail = image			
			
		except:
			livelink  = ""
			thumbnail = ""
			sentence1 = re.compile(r'sentence1="(.+?)"').findall(response)[0]
			try:
				sentence2 = re.compile(r'sentence2="(.+?)"').findall(response)[0]
			except:
				sentence2 = ""
				
			server_response(sentence1,sentence2)			

	if thumb == 0:
		return livelink
	else:
		return livelink,thumbnail



def GetMegaliveUser(login, password):
	xbmc.output("GetMegaliveUser")
	# ---------------------------------------
	#  Inicializa la librería de las cookies
	# ---------------------------------------
	ficherocookies = COOKIEFILE
	# Borra el fichero de cookies para evitar errores
	try:
		os.remove(ficherocookies)
	except:
		pass

	# the path and filename to save your cookies in

	cj = None
	ClientCookie = None
	cookielib = None

	# Let's see if cookielib is available
	try:
		import cookielib
	except ImportError:
		# If importing cookielib fails
		# let's try ClientCookie
		try:
			import ClientCookie
		except ImportError:
			# ClientCookie isn't available either
			urlopen = urllib2.urlopen
			Request = urllib2.Request
		else:
			# imported ClientCookie
			urlopen = ClientCookie.urlopen
			Request = ClientCookie.Request
			cj = ClientCookie.LWPCookieJar()

	else:
		# importing cookielib worked
		urlopen = urllib2.urlopen
		Request = urllib2.Request
		cj = cookielib.LWPCookieJar()
		# This is a subclass of FileCookieJar
		# that has useful load and save methods

	# ---------------------------------
	# Instala las cookies
	# ---------------------------------

	if cj is not None:
	# we successfully imported
	# one of the two cookie handling modules

		if os.path.isfile(ficherocookies):
			# if we have a cookie file already saved
			# then load the cookies into the Cookie Jar
			cj.load(ficherocookies)

		# Now we need to get our Cookie Jar
		# installed in the opener;
		# for fetching URLs
		if cookielib is not None:
			# if we use cookielib
			# then we get the HTTPCookieProcessor
			# and install the opener in urllib2
			opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
			urllib2.install_opener(opener)

		else:
			# if we use ClientCookie
			# then we get the HTTPCookieProcessor
			# and install the opener in ClientCookie
			opener = ClientCookie.build_opener(ClientCookie.HTTPCookieProcessor(cj))
			ClientCookie.install_opener(opener)

	#print "-------------------------------------------------------"
	url="http://www.megalive.com/?c=login"
	#print url
	#print "-------------------------------------------------------"
	theurl = url
	# an example url that sets a cookie,
	# try different urls here and see the cookie collection you can make !

	passwordesc=password.replace("&","%26")
	#txdata = "login=1&redir=1&username="+login+"&password="+passwordesc
	txdata = {'login':'1',
			  'redir':'1',
			  'username':login,
			  'password':passwordesc
			  }
	txdata = urllib.urlencode(txdata)
	# if we were making a POST type request,
	# we could encode a dictionary of values here,
	# using urllib.urlencode(somedict)
	
	txheaders =  {'User-Agent':'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3',
				  'Referer':'http://www.megalive.com/?c=login'
				 }
				  
	# fake a user agent, some websites (like google) don't like automated exploration

	req = Request(theurl, txdata, txheaders)
	handle = urlopen(req)
	cj.save(ficherocookies)                     # save the cookies again    

	data=handle.read()
	'''
	xbmc.output("----------------------")
	xbmc.output("Respuesta de Megalive")
	xbmc.output("----------------------")
	xbmc.output(data)
	xbmc.output("----------------------")
	'''
	handle.close()

	cookiedatafile = open(ficherocookies,'r')
	cookiedata = cookiedatafile.read()
	cookiedatafile.close();

	'''
	xbmc.output("----------------------")
	xbmc.output("Cookies despues")
	xbmc.output("----------------------")
	xbmc.output(cookiedata)
	xbmc.output("----------------------")
	'''

	patronvideos  = 'user="([^"]+)"'
	matches = re.compile(patronvideos,re.DOTALL).findall(cookiedata)
	if len(matches)==0:
		patronvideos  = 'user=([^\;]+);'
		matches = re.compile(patronvideos,re.DOTALL).findall(cookiedata)
	
	if len(matches)==0:
		xbmc.output("No se ha encontrado la cookie de Megalive")
		xbmc.output("----------------------")
		xbmc.output("Respuesta de Megalive")
		xbmc.output("----------------------")
		xbmc.output(data)
		xbmc.output("----------------------")
		xbmc.output("----------------------")
		xbmc.output("Cookies despues")
		xbmc.output("----------------------")
		xbmc.output(cookiedata)
		xbmc.output("----------------------")
		return ""
	else:
		return matches[0]

def server_response(sentence1 , sentence2=""):
	ventana = xbmcgui.Dialog()
	ok= ventana.ok ("Megalive","Server response...!", sentence1, sentence2)
	return
	