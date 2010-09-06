# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# tvalacarta - XBMC Plugin
# Canal para Clan TV
# http://blog.tvalacarta.info/plugin-xbmc/tvalacarta/
#------------------------------------------------------------

import urlparse,urllib2,urllib,re
import os
import sys
import xbmc
import xbmcgui
import xbmcplugin
import scrapertools
import binascii
import xbmctools

try:
	pluginhandle = int( sys.argv[ 1 ] )
except:
	pluginhandle = ""

xbmc.output("[clantv.py] init")

DEBUG = True
CHANNELNAME = "Clan TV"
CHANNELCODE = "clantv"

def mainlist(params,url,category):
	xbmc.output("[clantv.py] mainlist")

	url = 'http://www.rtve.es/infantil/videos-juegos/#/videos/clan/todos/'

	# --------------------------------------------------------
	# Descarga la página
	# --------------------------------------------------------
	data = scrapertools.cachePage(url)
	#xbmc.output(data)

	# --------------------------------------------------------
	# Extrae las categorias (carpetas)
	# --------------------------------------------------------
	patron = '<li.*?><a rel="([^"]+)" title="[^"]+" href="([^"]+)"><strong>([^<]+)</strong><img src="([^"]+)".*?><span>([^<]+)</span>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	if DEBUG:
		scrapertools.printMatches(matches)

	for match in matches:
		try:
			scrapedtitle = unicode( match[2], "utf-8" ).encode("iso-8859-1")
		except:
			scrapedtitle = match[2]
		scrapedtitle = scrapedtitle + " ("+match[4].replace("&iacute;","i")+")"
		scrapedtitle = scrapertools.entityunescape(scrapedtitle)
		
		#scrapedurl = "http://www.rtve.es/infantil/components/"+match[0]+"/videos/videos-1.inc"
		scrapedurl = "http://www.rtve.es/infantil/components/"+match[0]+"/videos.xml.inc"
		scrapedthumbnail = urlparse.urljoin(url,match[3])
		scrapedplot = ""

		# Depuracion
		if (DEBUG):
			xbmc.output("scrapedtitle="+scrapedtitle)
			xbmc.output("scrapedurl="+scrapedurl)
			xbmc.output("scrapedthumbnail="+scrapedthumbnail)

		# Añade al listado de XBMC
		#addvideo( scrapedtitle , scrapedurl , category )
		xbmctools.addnewfolder( CHANNELCODE , "videolist" , CHANNELNAME , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )

	# Disable sorting...
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def videolist(params,url,category):
	xbmc.output("[clantv.py] videolist")

	# --------------------------------------------------------
	# Descarga la página
	# --------------------------------------------------------
	data = scrapertools.cachePage2(url,[["Referer","http://www.rtve.es/infantil/videos-juegos/#/videos/edebits/todos/"],["User-Agent","Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; SLCC1; .NET CLR 2.0.50727; .NET CLR 3.0.04506; InfoPath.2)"]])
	xbmc.output(data)

	# --------------------------------------------------------
	# Extrae los capítulos
	# --------------------------------------------------------
	patron = '<video id="[^"]+" thumbnail="([^"]+)" url="([^"]+)" publication_date="([^T]+)T[^>]+>[^<]+<title>([^<]+)</title>[^<]+<sinopsis([^<]+)<'
	matches = re.compile(patron,re.DOTALL).findall(data)
	if DEBUG:
		scrapertools.printMatches(matches)

	for match in matches:
		try:
			scrapedtitle = unicode( match[3], "utf-8" ).encode("iso-8859-1")
		except:
			scrapedtitle = match[3]
		scrapedtitle = scrapedtitle + " ("+match[2]+")"
		scrapedtitle = scrapertools.entityunescape(scrapedtitle)
		scrapedurl = urlparse.urljoin(url,match[1])
		scrapedthumbnail = urlparse.urljoin(url,match[0])
		scrapedplot = match[4]

		# Depuracion
		if (DEBUG):
			xbmc.output("scrapedtitle="+scrapedtitle)
			xbmc.output("scrapedurl="+scrapedurl)
			xbmc.output("scrapedthumbnail="+scrapedthumbnail)

		# Añade al listado de XBMC
		xbmctools.addnewvideo( CHANNELCODE , "play" , CHANNELNAME , "" , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )

	# Disable sorting...
	#xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def play(params,url,category):
	xbmc.output("[clantv.py] play")

	title = unicode( xbmc.getInfoLabel( "ListItem.Title" ), "utf-8" )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = unicode( xbmc.getInfoLabel( "ListItem.Plot" ), "utf-8" )
	server = "Directo"
	
	xbmctools.playvideo(CHANNELNAME,server,url,category,title,thumbnail,plot)
