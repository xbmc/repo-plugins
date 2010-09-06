# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# tvalacarta - XBMC Plugin
# Canal para Público TV
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

xbmc.output("[publicotv.py] init")

DEBUG = True
CHANNELNAME = "Público TV"
CHANNELCODE = "publicotv"

def mainlist(params,url,category):
	xbmc.output("[publicotv.py] mainlist")

	url = "http://video.publico.es"

	# --------------------------------------------------------
	# Descarga la página
	# --------------------------------------------------------
	data = scrapertools.cachePage(url)
	#xbmc.output(data)

	# --------------------------------------------------------
	# Extrae los programas
	# --------------------------------------------------------
	patron = '<option value="(.*?)">(.*?)</option>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	if DEBUG:
		scrapertools.printMatches(matches)

	for match in matches:
		scrapedtitle = match[1]
		try:
			scrapedtitle = unicode( scrapedtitle, "utf-8" ).encode("iso-8859-1")
		except:
			pass
		scrapedurl = match[0]
		
		scrapedthumbnail = ""
		scrapedplot = ""

		# Depuracion
		if (DEBUG):
			xbmc.output("scrapedtitle="+scrapedtitle)
			xbmc.output("scrapedurl="+scrapedurl)
			xbmc.output("scrapedthumbnail="+scrapedthumbnail)

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELCODE , "videolist" , CHANNELNAME , scrapedtitle , scrapedurl , scrapedthumbnail , scrapedplot )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )

	# Disable sorting...
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def videolist(params,url,category):
	xbmc.output("[publicotv.py] videolist")

	# --------------------------------------------------------
	# Descarga la página
	# --------------------------------------------------------
	data = scrapertools.cachePage(url)
	#xbmc.output(data)

	# Extrae los vídeos
	patron  = '<div class="video-overview a1">[^<]+'
	patron += '<a href="([^"]+)" title="Play">'
	patron += '<img.*?src="(.*?)".*?title="([^"]+)"[^>]+></a>\W*<h4></h4>\W*<p class="title">(.*?)</p>\W*<div class="video-info-line">\W*<p>(.*?)</p>\W*<p>(.*?)</p>\W*</div>\W*</div>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	if DEBUG: scrapertools.printMatches(matches)

	for match in matches:
		scrapedtitle = match[3] + " ("+match[5]+") ("+match[4]+")"
		scrapedurl = urlparse.urljoin(url,match[0])
		scrapedthumbnail = urlparse.urljoin(url,match[1])
		scrapedplot = scrapertools.entityunescape(match[2])
		
		seppos = scrapedplot.find("--")
		scrapedplot = scrapedplot[seppos+2:]
		
		if (DEBUG): xbmc.output("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		xbmctools.addnewvideo( CHANNELCODE , "play" , CHANNELNAME , "" , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# Página siguiente
	patron  = '<a href="([^"]+)" title="Ir a la siguiente[^"]+">Siguiente \&raquo\;</a></div>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	if DEBUG: scrapertools.printMatches(matches)

	if len(matches)>0:
		match = matches[0]
	
		scrapedtitle = "Página siguiente"
		scrapedurl = urlparse.urljoin(url,match)
		scrapedthumbnail = ""
		scrapedplot = ""
		if (DEBUG): xbmc.output("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELCODE , "videolist" , CHANNELNAME , scrapedtitle , scrapedurl , scrapedthumbnail , scrapedplot )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )

	# Disable sorting...
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def play(params,url,category):
	xbmc.output("[publicotv.py] play")

	title = unicode( xbmc.getInfoLabel( "ListItem.Title" ), "utf-8" )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = unicode( xbmc.getInfoLabel( "ListItem.Plot" ), "utf-8" )
	server = "Directo"
	
	#http://video.publico.es/videos/9/54777/1/recent
	'''
	1) La URL de detalle que encuentra ese patrón de arriba es del tipo: http://video.publico.es/videos/9/51046/1/recent
	2) El código en negrita tienes que usarlo para invocar a otra URL que te dará la ubicación del vídeo: http://video.publico.es/videos/v_video/51046
	3) En la respuesta de esa URL tienes el vídeo, dentro de la cabecera "Location" que he resaltado en negrita.

	HTTP/1.1 302 Found
	Date: Mon, 09 Nov 2009 13:34:14 GMT
	Server: Apache/2.2.3 (Red Hat)
	X-Powered-By: PHP/5.1.6
	Location: http://mm.publico.es/files/flvs/51046.49118.flv
	Content-Encoding: gzip
	Vary: Accept-Encoding
	Content-Length: 26
	Keep-Alive: timeout=5, max=77
	Connection: Keep-Alive
	Content-Type: text/html; charset=utf-8
	'''
	patron = 'http\:\/\/video.publico.es\/videos\/[^\/]+/([^\/]+)/'
	matches = re.compile(patron,re.DOTALL).findall(url)
	if DEBUG: scrapertools.printMatches(matches)
	
	if len(matches)==0:
		xbmctools.alerterrorpagina()
		return

	url = 'http://video.publico.es/videos/v_video/'+matches[0]
	xbmc.output("url="+url)
	
	url = scrapertools.getLocationHeaderFromResponse(url)

	xbmctools.playvideo(CHANNELCODE,server,url,category,title,thumbnail,plot)
