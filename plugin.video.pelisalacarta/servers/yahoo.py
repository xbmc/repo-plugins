# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Conector para Vreel
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------

import urlparse,urllib2,urllib,re
import os.path
import sys
import xbmc
import os
import config
import logger
import htmlentitydefs

COOKIEFILE = os.path.join (config.DATA_PATH , "cookies.lwp")

def geturl(urlvideo):
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
	url= "http://video.yahoo.com/watch/%s" %urlvideo
	#url = "http://new.music.yahoo.com/videos/"
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
				  'Referer':'http://video.yahoo.com/',
				  'X-Forwarded-For': '12.13.14.15'}
	# fake a user agent, some websites (like google) don't like automated exploration

	req = Request(theurl, txdata, txheaders)
	handle = urlopen(req)
	cj.save(ficherocookies)                     # save the cookies again    

	data=handle.read()
	handle.close()
	#print data


	'''
	# Extract video height and width
	mobj = re.search(r'<meta name="video_height" content="([0-9]+)" />', data)
	if mobj is None:
		logger.info('ERROR: unable to extract video height')
		return ""
	yv_video_height = mobj.group(1)

	mobj = re.search(r'<meta name="video_width" content="([0-9]+)" />', data)
	if mobj is None:
		logger.info('ERROR: unable to extract video width')
		return ""
	yv_video_width = mobj.group(1)
	'''

	# Retrieve video playlist to extract media URL
	# I'm not completely sure what all these options are, but we
	# seem to need most of them, otherwise the server sends a 401.
	yv_lg = 'R0xx6idZnW2zlrKP8xxAIR'  # not sure what this represents
	yv_bitrate = '700'  # according to Wikipedia this is hard-coded
	url = ('http://cosmos.bcst.yahoo.com/up/yep/process/getPlaylistFOP.php?node_id=' + urlvideo +
					  '&tech=flash&mode=playlist&lg=' + yv_lg + '&bitrate=' + yv_bitrate + '&vidH=720'+
				  '&vidW=1280'  + '&swf=as3&rd=video.yahoo.com&tk=null&adsupported=v1,v2,&eventid=1301797')
	#http://cosmos.bcst.yahoo.com/up/yep/process/getPlaylistFOP.php?node_id=v205690975&tech=flash&mode=playlist&lg=xRen3QvzZ_5wj1x8BbzEcR&bitrate=700&vidH=324&vidW=576&swf=as3&rd=video.yahoo.com-offsite&tk=null&adsupported=v1,v2,&eventid=1301797			  
	#url = 'http://video.music.yahoo.com/up/music_e/process/getPlaylistFOP.php?node_id='+ urlvideo  + '&tech=flash&bitrate=20000&mode=&vidH=720&vidW=1280'

	req = Request(url, txdata, txheaders)
	handle = urlopen(req)
	cj.save(ficherocookies)                     # save the cookies again    

	data2=handle.read()
	handle.close()
	print data2

	
	# Extract media URL from playlist XML
	mobj = re.search(r'<STREAM APP="(http://.*)" FULLPATH="/?(/.*\.flv\?[^"]*)"', data2)
	if mobj is not None:
		video_url = urllib.unquote(mobj.group(1) + mobj.group(2)).decode('utf-8')
		video_url = re.sub(r'(?u)&(.+?);', htmlentity_transform, video_url)
		print video_url
		return video_url		
	else:	
		logger.info('ERROR: Unable to extract media URL http')
		mobj = re.search(r'<STREAM (APP="[^>]+)>', data2)
		if mobj is None:
			logger.info('ERROR: Unable to extract media URL rtmp')
			return ""
		#video_url = mobj.group(1).replace("&amp;","&")
		video_url = urllib.unquote(mobj.group(1).decode('utf-8'))
		video_url = re.sub(r'(?u)&(.+?);', htmlentity_transform, video_url)
		'''
		<STREAM APP="rtmp://s1sflod020.bcst.cdn.s1s.yimg.com/StreamCache" 
		FULLPATH="/s1snfs06r01/001/__S__/lauvpf/76414327.flv?StreamID=76414327&xdata=Njc3Mzc4MzA2NGNiNzI5MW-205754530-0&pl_auth=2598a5574b592b7c6ab262e4775b3930&ht=180&b=eca0lm561k1gn4cb7291a&s=396502118&br=700&q=ahfG2he5gqV40Laz.RUcnB&rd=video.yahoo.com-offsite&so=%2FMUSIC" 
		CLIPID="v205690975" TYPE="STREAMING" AD="NO" 
		APPNAME="ContentMgmt" URLPREFIX="rtmp://" 
		SERVER="s1sflod020.bcst.cdn.s1s.yimg.com" 
		BITRATE="7000" PORT="" 
		PATH="/s1snfs06r01/001/__S__/lauvpf/76414327.flv" 
		QUERYSTRING="StreamID=76414327&xdata=Njc3Mzc4MzA2NGNiNzI5MW-205754530-0&pl_auth=2598a5574b592b7c6ab262e4775b3930&ht=180&b=eca0lm561k1gn4cb7291a&s=396502118&br=700&q=ahfG2he5gqV40Laz.RUcnB&rd=video.yahoo.com-offsite&so=%2FMUSIC" 
		URL="" TITLE="-" AUTHOR="-" COPYRIGHT="(c) Yahoo! Inc. 2006" STARTTIME="" ENDTIME=""/>
		'''
		swfUrl = 'http://d.yimg.com/ht/yep/vyc_player.swf'
		try:
			App         = re.compile(r'APP="([^"]+)"').findall(video_url)[0]
			Fullpath    = re.compile(r'FULLPATH="([^"]+)"').findall(video_url)[0]
			Appname     = re.compile(r'APPNAME="([^"]+)"').findall(video_url)[0]
			#Server      = re.compile(r'SERVER="([^"]+)"').findall(video_url)[0]
			Path        = re.compile(r'PORT=""  PATH="([^"]+)"').findall(video_url)[0].replace(".flv","")
			#Querystring = re.compile(r'QUERYSTRING="([^"]+)"').findall(video_url)[0]
			playpath = Fullpath
			App = App.replace("/StreamCache",":1935/StreamCache/")
			video_url = "%s%s%s playpath=%s swfurl=%s swfvfy=true" %(App,Appname,playpath,Path,swfUrl)
		except:
			logger.info('ERROR: re.compile failed')
			video_url = ""
		
	print video_url.encode("utf-8")
	return video_url

def htmlentity_transform(matchobj):
	"""Transforms an HTML entity to a Unicode character.
	
	This function receives a match object and is intended to be used with
	the re.sub() function.
	"""
	entity = matchobj.group(1)

	# Known non-numeric HTML entity
	if entity in htmlentitydefs.name2codepoint:
		return unichr(htmlentitydefs.name2codepoint[entity])

	# Unicode character
	mobj = re.match(ur'(?u)#(x?\d+)', entity)
	if mobj is not None:
		numstr = mobj.group(1)
		if numstr.startswith(u'x'):
			base = 16
			numstr = u'0%s' % numstr
		else:
			base = 10
		return unichr(long(numstr, base))

	# Unknown entity in name, return its literal representation
	return (u'&%s;' % entity)
