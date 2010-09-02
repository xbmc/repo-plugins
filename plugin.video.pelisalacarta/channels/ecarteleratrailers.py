# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para trailers de ecartelera
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

CHANNELNAME = "ecarteleratrailers"

# Esto permite su ejecución en modo emulado
try:
	pluginhandle = int( sys.argv[ 1 ] )
except:
	pluginhandle = ""

# Traza el inicio del canal
logger.info("[ecarteleratrailers.py] init")

DEBUG = True

def mainlist(params,url,category):
	logger.info("[ecarteleratrailers.py] mainlist")

	if url=="":
		url="http://www.ecartelera.com/videos/"
	
	# ------------------------------------------------------
	# Descarga la página
	# ------------------------------------------------------
	data = scrapertools.cachePage(url)
	#logger.info(data)

	# ------------------------------------------------------
	# Extrae las películas
	# ------------------------------------------------------
	patron  = '<div class="cuadronoticia">.*?<img src="([^"]+)".*?'
	patron += '<div class="cnottxtv">.*?<h3><a href="([^"]+)">([^<]+)</a></h3>.*?'
	patron += '<img class="bandera" src="http\:\/\/www\.ecartelera\.com\/images\/([^"]+)"[^<]+'
	patron += '<br/>([^<]+)</div>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	if DEBUG:
		scrapertools.printMatches(matches)

	for match in matches:
		try:
			scrapedtitle = unicode( match[2], "utf-8" ).encode("iso-8859-1")
		except:
			scrapedtitle = match[2]
		if match[3]=="fl_1.gif":
			scrapedtitle += " (Castellano)"
		elif match[3]=="fl_2.gif":
			scrapedtitle += " (Inglés)"
		
		scrapedurl = match[1]
		scrapedthumbnail = match[0]
		scrapedplot = match[4]

		# Depuracion
		if DEBUG:
			logger.info("scrapedtitle="+scrapedtitle)
			logger.info("scrapedurl="+scrapedurl)
			logger.info("scrapedthumbnail="+scrapedthumbnail)
			logger.info("scrapedplot="+scrapedplot)

		# Añade al listado de XBMC
		xbmctools.addnewvideo( CHANNELNAME , "play" , category , "Directo" , scrapedtitle , scrapedurl , scrapedthumbnail , scrapedplot )

	# ------------------------------------------------------
	# Extrae la página siguiente
	# ------------------------------------------------------
	patron = '<a href="([^"]+)">Siguiente</a>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	if DEBUG:
		scrapertools.printMatches(matches)

	for match in matches:
		scrapedtitle = "Pagina siguiente"
		scrapedurl = match
		scrapedthumbnail = ""
		scrapeddescription = ""

		# Depuracion
		if DEBUG:
			logger.info("scrapedtitle="+scrapedtitle)
			logger.info("scrapedurl="+scrapedurl)
			logger.info("scrapedthumbnail="+scrapedthumbnail)

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELNAME , "mainlist" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )

	# Disable sorting...
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

# Reproducir un vídeo
def play(params,url,category):
	logger.info("[ecarteleratrailers.py] play")

	title = urllib.unquote_plus( params.get("title") )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = unicode( xbmc.getInfoLabel( "ListItem.Plot" ), "utf-8" )
	server = params["server"]
	
	# ------------------------------------------------------
	# Descarga la página
	# ------------------------------------------------------
	data = scrapertools.cachePage(url)
	#logger.info(data)

	# ------------------------------------------------------
	# Extrae las películas
	# ------------------------------------------------------
	patron  = "so\.addVariable\('file','([^']+)'\)"
	#patron  = "s1\.addParam\('flashvars'\,'file\=([^\&]+)\&"
	matches = re.compile(patron,re.DOTALL).findall(data)
	if DEBUG:
		scrapertools.printMatches(matches)

	if len(matches)>0:
		url = urlparse.urljoin(url,matches[0])
		logger.info("[ecarteleratrailers.py] url="+url)
		xbmctools.playvideo(CHANNELNAME,server,url,category,title,thumbnail,plot)
