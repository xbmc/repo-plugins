# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para seriespepito
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------
import urlparse,urllib2,urllib,re
import os
import sys
import xbmc
import xbmcgui
import xbmcplugin
import scrapertools
import megavideo
import servertools
import binascii
import xbmctools
import config
import logger

CHANNELNAME = "seriespepito"

# Esto permite su ejecución en modo emulado
try:
	pluginhandle = int( sys.argv[ 1 ] )
except:
	pluginhandle = ""

logger.info("[seriespepito.py] init")

DEBUG = True

def mainlist(params,url,category):
	logger.info("[seriespepito.py] mainlist")

	xbmctools.addnewfolder( CHANNELNAME , "updatedserieslist", category , "Series actualizadas","http://www.seriespepito.com/","","")
	xbmctools.addnewfolder( CHANNELNAME , "lastepisodelist"  , category , "Nuevos capítulos","http://www.seriespepito.com/nuevos-capitulos/","","")
	xbmctools.addnewfolder( CHANNELNAME , "listalfabetico"   , category , "Listado alfabético","","","")
	xbmctools.addnewfolder( CHANNELNAME , "allserieslist"    , category , "Listado completo","http://www.seriespepito.com/","","")

	if config.getSetting("singlechannel")=="true":
		xbmctools.addSingleChannelOptions(params,url,category)

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
		
	# Disable sorting...
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def updatedserieslist(params,url,category):
	logger.info("[seriespepito.py] lastepisodeslist")

	# Descarga la página
	data = scrapertools.cachePage(url)
	#logger.info(data)

	# Extrae las entradas (carpetas)
	patron  = '<td valign="top" align="center" width="20%">[^<]+'
	patron += '<a class="azulverde" href="([^"]+)" title="">[^<]+'
	patron += "<img src='([^']+)'.*?/><br>([^<]+)</a>"
	matches = re.compile(patron,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	for match in matches:
		# Titulo
		scrapedtitle = match[2]

		# URL
		scrapedurl = match[0]
		
		# Thumbnail
		scrapedthumbnail = match[1]
		
		# procesa el resto
		scrapedplot = ""

		# Depuracion
		if (DEBUG):
			logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELNAME , "episodelist" , category , scrapedtitle , scrapedurl , scrapedthumbnail , scrapedplot )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )

	# Disable sorting...
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def alphaserieslist(params,url,category):
	logger.info("[seriespepito.py] alphaserieslist")

	# Descarga la página
	data = scrapertools.cachePage(url)
	#logger.info(data)

	# Extrae las entradas (carpetas)
	
	patron  = '<td valign="top" align="center" width="33%">[^<]+'
	patron += '<a class="azulverde" href="([^"]+)" title="[^"]+">[^<]+'
	patron += "<img src='([^']+)'.*?/><br />([^<]+)</a>[^<]+"
	matches = re.compile(patron,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	for match in matches:
		# Titulo
		scrapedtitle = match[2]

		# URL
		scrapedurl = match[0]
		
		# Thumbnail
		scrapedthumbnail = match[1]
		
		# procesa el resto
		scrapedplot = ""

		# Depuracion
		if (DEBUG):
			logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELNAME , "episodelist" , category , scrapedtitle , scrapedurl , scrapedthumbnail , scrapedplot )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )

	# Disable sorting...
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def lastepisodelist(params,url,category):
	logger.info("[seriespepito.py] lastepisodeslist")

	# Descarga la página
	data = scrapertools.cachePage(url)
	#logger.info(data)

	# Extrae las entradas (carpetas)
	patron  = '<td valign="top" align="center" width="33%">[^<]+'
	patron += '<a href="([^"]+)"[^>]+>[^<]+'
	patron += "<img src='([^']+)'.*?<br />[^<]+"
	patron += '<a.*?title="([^"]+).*?'
	patron += '<a.*?title="([^"]+).*?'
	patron += '<a.*?title="([^"]+)'


	matches = re.compile(patron,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	for match in matches:
		# Titulo
		scrapedtitle = match[2]+" - "+match[3]+" - "+match[4]

		# URL
		scrapedurl = match[0]
		
		# Thumbnail
		scrapedthumbnail = match[1]
		
		# procesa el resto
		scrapedplot = ""

		# Depuracion
		if (DEBUG):
			logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELNAME , "mirrorlist" , category , scrapedtitle , scrapedurl , scrapedthumbnail , scrapedplot )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )

	# Disable sorting...
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def allserieslist(params,url,category):
	logger.info("[seriespepito.py] lastepisodeslist")

	# Descarga la página
	data = scrapertools.cachePage(url)
	#logger.info(data)

	# Extrae las entradas (carpetas)
	patron  = '<b><a class="azulverde" href="([^"]+)">([^<]+)</a></b><br />'
	matches = re.compile(patron,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	for match in matches:
		# Titulo
		scrapedtitle = match[1]

		# URL
		scrapedurl = match[0]
		
		# Thumbnail
		scrapedthumbnail = ""
		
		# procesa el resto
		scrapedplot = ""

		# Depuracion
		if (DEBUG):
			logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELNAME , "episodelist" , category , scrapedtitle , scrapedurl , scrapedthumbnail , scrapedplot )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )

	# Disable sorting...
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def listalfabetico(params, url, category):
	
	xbmctools.addnewfolder(CHANNELNAME , "alphaserieslist" , category , "0-9","http://www.seriespepito.com/lista-series-num/","","")
	xbmctools.addnewfolder(CHANNELNAME , "alphaserieslist" , category , "A","http://www.seriespepito.com/lista-series-a/","","")
	xbmctools.addnewfolder(CHANNELNAME , "alphaserieslist" , category , "B","http://www.seriespepito.com/lista-series-b/","","")
	xbmctools.addnewfolder(CHANNELNAME , "alphaserieslist" , category , "C","http://www.seriespepito.com/lista-series-c/","","")
	xbmctools.addnewfolder(CHANNELNAME , "alphaserieslist" , category , "D","http://www.seriespepito.com/lista-series-d/","","")
	xbmctools.addnewfolder(CHANNELNAME , "alphaserieslist" , category , "E","http://www.seriespepito.com/lista-series-e/","","")
	xbmctools.addnewfolder(CHANNELNAME , "alphaserieslist" , category , "F","http://www.seriespepito.com/lista-series-f/","","")
	xbmctools.addnewfolder(CHANNELNAME , "alphaserieslist" , category , "G","http://www.seriespepito.com/lista-series-g/","","")
	xbmctools.addnewfolder(CHANNELNAME , "alphaserieslist" , category , "H","http://www.seriespepito.com/lista-series-h/","","")
	xbmctools.addnewfolder(CHANNELNAME , "alphaserieslist" , category , "I","http://www.seriespepito.com/lista-series-i/","","")
	xbmctools.addnewfolder(CHANNELNAME , "alphaserieslist" , category , "J","http://www.seriespepito.com/lista-series-j/","","")
	xbmctools.addnewfolder(CHANNELNAME , "alphaserieslist" , category , "K","http://www.seriespepito.com/lista-series-k/","","")
	xbmctools.addnewfolder(CHANNELNAME , "alphaserieslist" , category , "L","http://www.seriespepito.com/lista-series-l/","","")
	xbmctools.addnewfolder(CHANNELNAME , "alphaserieslist" , category , "M","http://www.seriespepito.com/lista-series-m/","","")
	xbmctools.addnewfolder(CHANNELNAME , "alphaserieslist" , category , "N","http://www.seriespepito.com/lista-series-n/","","")
	xbmctools.addnewfolder(CHANNELNAME , "alphaserieslist" , category , "O","http://www.seriespepito.com/lista-series-o/","","")
	xbmctools.addnewfolder(CHANNELNAME , "alphaserieslist" , category , "P","http://www.seriespepito.com/lista-series-p/","","")
	xbmctools.addnewfolder(CHANNELNAME , "alphaserieslist" , category , "Q","http://www.seriespepito.com/lista-series-q/","","")
	xbmctools.addnewfolder(CHANNELNAME , "alphaserieslist" , category , "R","http://www.seriespepito.com/lista-series-r/","","")
	xbmctools.addnewfolder(CHANNELNAME , "alphaserieslist" , category , "S","http://www.seriespepito.com/lista-series-s/","","")
	xbmctools.addnewfolder(CHANNELNAME , "alphaserieslist" , category , "T","http://www.seriespepito.com/lista-series-t/","","")
	xbmctools.addnewfolder(CHANNELNAME , "alphaserieslist" , category , "U","http://www.seriespepito.com/lista-series-u/","","")
	xbmctools.addnewfolder(CHANNELNAME , "alphaserieslist" , category , "V","http://www.seriespepito.com/lista-series-v/","","")
	xbmctools.addnewfolder(CHANNELNAME , "alphaserieslist" , category , "W","http://www.seriespepito.com/lista-series-w/","","")
	xbmctools.addnewfolder(CHANNELNAME , "alphaserieslist" , category , "X","http://www.seriespepito.com/lista-series-x/","","")
	xbmctools.addnewfolder(CHANNELNAME , "alphaserieslist" , category , "Y","http://www.seriespepito.com/lista-series-y/","","")
	xbmctools.addnewfolder(CHANNELNAME , "alphaserieslist" , category , "Z","http://www.seriespepito.com/lista-series-z/","","")

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )

	# Disable sorting...
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def episodelist(params,url,category):
	logger.info("[seriespepito.py] list")

	# Descarga la página
	data = scrapertools.cachePage(url)
	#logger.info(data)

	# Extrae las entradas (carpetas)
	patron = "<li class='li_capitulo'><a class='capitulo1' href='([^']+)' title='[^']+'>([^<]+)</a>&nbsp;<img src='([^']+)'[^>]+></li>"
	matches = re.compile(patron,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	for match in matches:
		# Match[2] es el icono del idioma (http://www.seriespepito.com/seriespepito/idiomas/es.png)
		
		# Titulo
		scrapedtitle = match[1] + " ["+match[2][49:-4]+"]"

		# URL
		scrapedurl = match[0]
		
		# Thumbnail
		scrapedthumbnail = ""
		
		# procesa el resto
		scrapedplot = ""

		# Depuracion
		if (DEBUG):
			logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELNAME , "mirrorlist" , category , scrapedtitle , scrapedurl , scrapedthumbnail , scrapedplot )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )

	# Disable sorting...
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def mirrorlist(params,url,category):
	logger.info("[seriespepito.py] mirrorlist")

	title = urllib.unquote_plus( params.get("title") )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = urllib.unquote_plus( params.get("plot") )

	# Descarga la página
	data = scrapertools.cachePage(url)
	#logger.info(data)

	# ------------------------------------------------------------------------------------
	# Busca los enlaces a los videos
	# ------------------------------------------------------------------------------------
	listavideos = servertools.findvideos(data)

	for video in listavideos:
		videotitle = video[0]
		url = video[1]
		server = video[2]
		xbmctools.addnewvideo( CHANNELNAME , "play" , category , server , title.strip() + " - " + videotitle , url , thumbnail , plot )
	# ------------------------------------------------------------------------------------

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
		
	# Disable sorting...
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def play(params,url,category):
	logger.info("[seriespepito.py] play")

	title = unicode( xbmc.getInfoLabel( "ListItem.Title" ), "utf-8" )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = unicode( xbmc.getInfoLabel( "ListItem.Plot" ), "utf-8" )
	server = params["server"]
	
	xbmctools.playvideo(CHANNELNAME,server,url,category,title,thumbnail,plot)
