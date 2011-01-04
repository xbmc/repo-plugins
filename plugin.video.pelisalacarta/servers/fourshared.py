# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Conector para 4shared
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------
import urlparse,urllib2,urllib,re,httplib
import config

def geturl(url):
	#http://www.4shared.com/embed/392975628/ff297d3f
	print "url="+url

	import httplib
	parsedurl = urlparse.urlparse(url)
	print "parsedurl=",parsedurl

	try:
		host = parsedurl.netloc
	except:
		host = parsedurl[1]
	print "host=",host

	try:
		print "1"
		query = parsedurl.path+";"+parsedurl.query
	except:
		print "2"
		query = parsedurl[2]+";"+parsedurl[3]+"?"
	print "query=",query
	query = urllib.unquote( query )
	print "query = " + query

	import httplib
	conn = httplib.HTTPConnection(host)
	conn.request("GET", query)
	response = conn.getresponse()
	location = response.getheader("location")
	conn.close()
	
	print "location=",location

	#Location: http://www.4shared.com/flash/player.swf?file=http://dc237.4shared.com/img/392975628/ff297d3f/dlink__2Fdownload_2Flj9Qu-tF_3Ftsid_3D20101030-200423-87e3ba9b/preview.flv&d
	patron = "file\=([^\&]+)\&"
	matches = re.compile(patron,re.DOTALL).findall(location)
	videourl = matches[0]

	print "videourl=",videourl

	return videourl
