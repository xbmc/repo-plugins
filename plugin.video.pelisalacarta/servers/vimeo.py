# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Conector para Vimeo
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------

import urlparse,urllib2,urllib,re
import os.path
import sys
import xbmc
import os
import config
import logger
import socket
from xml.dom.minidom import parseString

COOKIEFILE = os.path.join (config.DATA_PATH , "cookies.lwp")

def geturl(urlvideo):
	videoid = urlvideo
	
	# ---------------------------------------
	#  Inicializa la libreria de las cookies
	# ---------------------------------------
	ficherocookies = COOKIEFILE
	try:
		os.remove(ficherocookies)
	except:
		pass
	#xbmc.output("ficherocookies %s", ficherocookies)
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
	url= "http://www.vimeo.com/moogaloop/load/clip:%s/local/" %videoid
	#print url
	#print "-------------------------------------------------------"
	
	theurl = url
	# an example url that sets a cookie,
	# try different urls here and see the cookie collection you can make !

	txdata = None
	# if we were making a POST type request,
	# we could encode a dictionary of values here,
	# using urllib.urlencode(somedict)
	
	txheaders =  {'User-Agent':'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3',
				  'Referer':'http://vimeo/%s' %urlvideo}
	# fake a user agent, some websites (like google) don't like automated exploration

	req = Request(theurl, txdata, txheaders)
	handle = urlopen(req)
	#cj.save(ficherocookies)                     # save the cookies again    

	data=handle.read()
	handle.close()
	print data

	

	#parseamos el xml en busca del codigo de signatura
	dom = parseString(data);
	xml = dom.getElementsByTagName("xml")




	for node in xml:
		try:
			request_signature = getNodeValue(node, "request_signature", "Unknown Uploader").encode( "utf-8" )
			request_signature_expires = getNodeValue(node, "request_signature_expires", "Unknown Uploader").encode( "utf-8")
		except:
			logger.info("Error : Video borrado")
			return ""
	try:
		quality =  ((config.getSetting("quality_flv") == "1" and "hd") or "sd")
	except:
		quality = "sd"
	video_url = "http://www.vimeo.com/moogaloop/play/clip:%s/%s/%s/?q=%s" % ( videoid, request_signature, request_signature_expires , quality )
	print video_url
	# Timeout del socket a 60 segundos
	socket.setdefaulttimeout(10)

	h=urllib2.HTTPHandler(debuglevel=0)
	request = urllib2.Request(video_url)

	opener = urllib2.build_opener(h)
	urllib2.install_opener(opener)
	try:
		connexion = opener.open(request)
		video_url = connexion.geturl()
	except urllib2.HTTPError,e:
		xbmc.output("[vimeo.py]  error %d (%s) al abrir la url %s" % (e.code,e.msg,video_url))
		
		print e.read()	
	#buscamos la url real en el headers
	#req = Request(theurl, txdata, txheaders)
	#handle = urllib2.urlopen(req)
	#video_url = handle.headers["Location"]


	#print data	
	if len(video_url) == 0:
		logger.info(" vimeo.geturl(): result was empty")
		return ""
	else:                
		logger.info (" vimeo.geturl(): done")
		return video_url
	'''	
	except urllib2.HTTPError, e:
	logger.info (" vimeo.geturl HTTPError: " + str(e))
	return (str(e), 303)
								
	except:
	logger.info (" Vimeo.geturl: uncaught exception")

	return ""
	'''
def getNodeValue(node, tag, default = ""):
        if node.getElementsByTagName(tag).item(0):
            if node.getElementsByTagName(tag).item(0).firstChild:
                return node.getElementsByTagName(tag).item(0).firstChild.nodeValue

