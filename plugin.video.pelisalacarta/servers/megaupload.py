# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Conector para Megaupload
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------

import re, sys, os
import urlparse, urllib, urllib2
import os.path
import sys
import xbmc
import xbmcplugin
import xbmcgui
import megavideo
import scrapertools
import config

DEBUG = False

COOKIEFILE = os.path.join( config.DATA_PATH, 'cookies.lwp' )

# Convierte el código de megaupload a megavideo
def convertcode(megauploadcode):
	# Descarga la página de megavideo pasándole el código de megaupload
	url = "http://www.megavideo.com/?d="+megauploadcode
	data = scrapertools.cachePage(url)
	#xbmc.output(data)

	# Extrae las entradas (carpetas)
	patronvideos  = 'flashvars.v = "([^"]+)"'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	#scrapertools.printMatches(matches)
	
	megavideocode = ""
	if len(matches)>0:
		megavideocode = matches[0]

	return megavideocode

# Extrae directamente la URL del vídeo de Megaupload
def getmegauploaduser(login,password):

	# ---------------------------------------
	#  Inicializa la librería de las cookies
	# ---------------------------------------
	ficherocookies = COOKIEFILE
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
	url="http://www.megaupload.com/?c=login"
	#print url
	#print "-------------------------------------------------------"
	theurl = url
	# an example url that sets a cookie,
	# try different urls here and see the cookie collection you can make !

	passwordesc=password.replace("&","%26")
	txdata = "login=1&redir=1&username="+login+"&password="+passwordesc
	# if we were making a POST type request,
	# we could encode a dictionary of values here,
	# using urllib.urlencode(somedict)

	txheaders =  {'User-Agent':'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3',
				  'Referer':'http://www.megaupload.com'}
	# fake a user agent, some websites (like google) don't like automated exploration

	req = Request(theurl, txdata, txheaders)
	handle = urlopen(req)
	cj.save(ficherocookies)                     # save the cookies again    
	data=handle.read()
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

	if len(matches)==0 and DEBUG:
		xbmc.output("No se ha encontrado la cookie de Megaupload")
		xbmc.output("----------------------")
		xbmc.output("Respuesta de Megaupload")
		xbmc.output("----------------------")
		xbmc.output(data)
		xbmc.output("----------------------")
		xbmc.output("----------------------")
		xbmc.output("Cookies despues")
		xbmc.output("----------------------")
		xbmc.output(cookiedata)
		xbmc.output("----------------------")
		devuelve = ""
	else:
		devuelve = matches[0]

	return devuelve

def getmegauploadvideo(code,user):
	req = urllib2.Request("http://www.megaupload.com/?d="+code)
	req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
	req.add_header('Cookie', 'l=es; user='+user)
	try:
		response = urllib2.urlopen(req)
	except:
		req = urllib2.Request(url.replace(" ","%20"))
		req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
		response = urllib2.urlopen(req)
	data=response.read()
	response.close()
	#if DEBUG:
	#	xbmc.output("[megaupload.py] data=#"+data+"#")
	
	patronvideos  = '<div.*?id="downloadlink">[^<]+<a href="([^"]+)"'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)
	
	mediaurl = ""
	if len(matches)>0:
		mediaurl = matches[0]
	
	return mediaurl

def getvideo(code):
	return megavideo.Megavideo(convertcode(code))

def gethighurl(code):
	megavideologin = config.getSetting("megavideouser")
	if DEBUG:
		xbmc.output("[megaupload.py] megavideouser=#"+megavideologin+"#")
	megavideopassword = config.getSetting("megavideopassword")
	if DEBUG:
		xbmc.output("[megaupload.py] megavideopassword=#"+megavideopassword+"#")
	cookie = getmegauploaduser(megavideologin,megavideopassword)
	if DEBUG:
		xbmc.output("[megaupload.py] cookie=#"+cookie+"#")

	if len(cookie) == 0:
		advertencia = xbmcgui.Dialog()
		resultado = advertencia.ok('Cuenta de Megaupload errónea' , 'La cuenta de Megaupload que usas no es válida' , 'Comprueba el login y password en la configuración')
		return ""

	return getmegauploadvideo(code,cookie)

def getlowurl(code):
	return megavideo.getlowurl(convertcode(code))
