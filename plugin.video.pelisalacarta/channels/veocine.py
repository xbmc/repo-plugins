# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para veocine
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

CHANNELNAME = "veocine"

# Esto permite su ejecución en modo emulado
try:
	pluginhandle = int( sys.argv[ 1 ] )
except:
	pluginhandle = ""

# Traza el inicio del canal
logger.info("[veocine.py] init")

DEBUG = True

def mainlist(params,url,category):
	logger.info("[veocine.py] mainlist")

	# Añade al listado de XBMC
	xbmctools.addnewfolder( CHANNELNAME , "videolist" , "" , "Peliculas","http://www.veocine.es/peliculas.html","","")
	xbmctools.addnewfolder( CHANNELNAME , "videolist" , "" , "Documentales", "http://www.veocine.es/documentales.html","","")
	xbmctools.addnewfolder( CHANNELNAME , "videolist" , "" , "Peliculas infantiles", "http://www.veocine.es/infantil.html","","")
	xbmctools.addnewfolder( CHANNELNAME , "videolist" , "" , "Peliculas VOS", "http://www.veocine.es/peliculavos.html","","")
	xbmctools.addnewfolder( CHANNELNAME , "videolist" , "" , "Anime", "http://www.veocine.es/anime.html","","")

	if config.getSetting("singlechannel")=="true":
		xbmctools.addSingleChannelOptions(params,url,category)

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )

	# Disable sorting...
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def videolist(params,url,category):
	logger.info("[veocine.py] mainlist")

	# ------------------------------------------------------
	# Descarga la página
	# ------------------------------------------------------
	data = scrapertools.cachePage(url)
	#logger.info(data)

	# ------------------------------------------------------
	# Extrae las películas
	# ------------------------------------------------------
	patron  = '<tr.*?'
	patron += '<td.*?'
	patron += '<a href="([^"]+)">'
	patron += "<img src='([^']+)'.*?<a.*?>\s*(.*?)\s*<(.*?)"
	patron += "<img .*? alt='([^']+)' />"
	matches = re.compile(patron,re.DOTALL).findall(data)
	if DEBUG:
		scrapertools.printMatches(matches)

	for match in matches:
		try:
			scrapedtitle = unicode( match[2], "utf-8" ).encode("iso-8859-1") + " (" + match[4] + ")"
		except:
			scrapedtitle = match[2] + " (" + match[4] + ")"
		scrapedurl = urlparse.urljoin("http://www.veocine.es/",match[0])
		scrapedthumbnail = ""

		try:
			scrapedplot = unicode( match[3], "utf-8" ).encode("iso-8859-1")
		except:
			scrapedplot = match[3]

		scrapedplot = scrapedplot.replace("/a>","\n")
		scrapedplot = scrapedplot.replace("<br />","\n")
		scrapedplot = scrapedplot.replace("<b>","")
		scrapedplot = scrapedplot.replace("</b>","")
		scrapedplot = scrapedplot.replace("<i>","")
		scrapedplot = scrapedplot.replace("</i>","")
		scrapedplot = scrapedplot.replace("<!--colorstart:#589BB9-->","")
		scrapedplot = scrapedplot.replace("<!--colorend-->","")
		scrapedplot = scrapedplot.replace("<!--/colorend-->","")
		scrapedplot = scrapedplot.replace("<!--/colorstart-->","")
		scrapedplot = scrapedplot.replace('<span style="color:#589BB9">',"")
		scrapedplot = scrapedplot.replace("</span>","")
		scrapedplot = scrapedplot.strip()

		# Depuracion
		if DEBUG:
			logger.info("scrapedtitle="+scrapedtitle)
			logger.info("scrapedurl="+scrapedurl)
			logger.info("scrapedthumbnail="+scrapedthumbnail)
			logger.info("scrapedplot="+scrapedplot)

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELNAME , "listmirrors" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# ------------------------------------------------------
	# Extrae la página siguiente
	# ------------------------------------------------------
	patron = "<a href='([^']+)'>Siguiente</a>"
	matches = re.compile(patron,re.DOTALL).findall(data)
	if DEBUG:
		scrapertools.printMatches(matches)

	for match in matches:
		scrapedtitle = "Pagina siguiente"
		scrapedurl = urlparse.urljoin("http://www.veocine.es/",match)
		scrapedthumbnail = ""
		scrapeddescription = ""

		# Depuracion
		if DEBUG:
			logger.info("scrapedtitle="+scrapedtitle)
			logger.info("scrapedurl="+scrapedurl)
			logger.info("scrapedthumbnail="+scrapedthumbnail)

		# Añade al listado de XBMC
		xbmctools.addthumbnailfolder( CHANNELNAME , scrapedtitle , scrapedurl , scrapedthumbnail, "mainlist" )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )

	# Disable sorting...
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def listmirrors(params,url,category):
	logger.info("[veocine.py] listmirrors")

	#50=full list
	#xbmc.executebuiltin("Container.SetViewMode(50)")

	title = urllib.unquote_plus( params.get("title") )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = urllib.unquote_plus( params.get("plot") )

	# Descarga la página de detalle
	data = scrapertools.cachePage(url)
	#logger.info(data)
	
	# Extrae los enlaces a los vídeos (Megavídeo)
	#reproductor.php?video=53842&media=tutv&titulo=Obsesion Extraterrestre - Mirror 1&titulop=Obsesion Extraterrestre
	#reproductor.php?video=KXLMR3C2&media=megavideo&titulo=Ciencia al desnudo: Jupiter - Mirror 1&titulop=Ciencia al desnudo: Jupiter&des=http%3A%2F%2Fwww.veodescargas.com%2Fdocumentales%2F13743-ciencia-al-desnudo-jupiter-dvb-s-national-geographic.html%23post30969
	patron = 'reproductor.php\?video=([^\&]+)\&(?:amp\;)?media=([^\&]+)\&(?:amp\;)?titulo=([^"]+)"'
	matches = re.compile(patron,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)		

	for match in matches:
		try:
			scrapedtitle = unicode( match[2], "utf-8" ).encode("iso-8859-1") + " (" + match[0] + ")"
		except:
			scrapedtitle = match[2] + " (" + match[0] + ")"
		scrapedurl = match[0]
		
		if match[1]=="megavideo":
			server="Megavideo"
		elif match[1]=="tutv":
			server="tu.tv"
		else:
			server="Megavideo"

		# Añade al listado de XBMC
		xbmctools.addnewvideo( CHANNELNAME , "play" , category , server , scrapedtitle , scrapedurl , thumbnail , plot )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
		
	# Disable sorting...
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def play(params,url,category):
	logger.info("[veocine.py] play")

	title = urllib.unquote_plus( params.get("title") )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = urllib.unquote_plus( params.get("plot") )
	server = urllib.unquote_plus( params.get("server") )

	# Abre dialogo
	dialogWait = xbmcgui.DialogProgress()
	dialogWait.create( 'Accediendo al video...', title , plot )

	# Cierra dialogo
	dialogWait.close()
	del dialogWait

	xbmctools.playvideo(CHANNELNAME,server,url,category,title,thumbnail,plot)
