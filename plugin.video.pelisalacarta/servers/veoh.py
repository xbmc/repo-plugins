# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Conector para Veoh
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------

import urlparse,urllib2,urllib,re
import os.path
import sys
import xbmc
import scrapertools
import config

def getvideo(code):
	xbmc.output("[veoh.py] code="+code)
	url = 'http://www.flashvideodownloader.org/download.php?u=http://www.veoh.com/browse/videos/category/entertainment/watch/'+code
	xbmc.output("[veoh.py] url="+url)
	data = scrapertools.cachePage(url)
	#xbmc.output("[veoh.py] data="+data)
	patronvideos  = '<a href="(http://content.veoh.com.*?)"'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	movielink=""
	if len(matches)>0:
		movielink = matches[0]
	xbmc.output("[veoh.py] movielink="+movielink)
	
	import httplib
	parsedurl = urlparse.urlparse(movielink)
	#xbmc.output("[veoh.py] parsedurl="+parsedurl)
	print "parsedurl=",parsedurl

	try:
		xbmc.output("[veoh.py] 1")
		host = parsedurl.netloc
	except:
		xbmc.output("[veoh.py] 2")
		host = parsedurl[1]
	xbmc.output("[veoh.py] host="+host)

	try:
		xbmc.output("[veoh.py] 1")
		query = parsedurl.path+parsedurl.query
	except:
		xbmc.output("[veoh.py] 2")
		query = parsedurl[2]+parsedurl[3]
	xbmc.output("[veoh.py] query = " + query)
	query = urllib.unquote( query )
	xbmc.output("[veoh.py] query = " + query)

	try:
		xbmc.output("[veoh.py] 1")
		params = parsedurl.params
	except:
		xbmc.output("[veoh.py] 2")
		params = parsedurl[4]
	xbmc.output("[veoh.py] params = " + params)

	import httplib
	conn = httplib.HTTPConnection(host)
	conn.request("GET", query+"?"+params)
	response = conn.getresponse()
	location = response.getheader("location")
	conn.close()

	if location!=None:
		xbmc.output("[veoh.py] Encontrado header location")
		xbmc.output("[veoh.py] location="+location)
	else:
		location=""
	
	return location
