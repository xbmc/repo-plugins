# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para yotix
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

CHANNELNAME = "yotix"

# Esto permite su ejecución en modo emulado
try:
	pluginhandle = int( sys.argv[ 1 ] )
except:
	pluginhandle = ""

# Traza el inicio del canal
logger.info("[yotix.py] init")

DEBUG = True

def mainlist(params,url,category):
	logger.info("[yotix.py] mainlist")

	# Añade al listado de XBMC
	xbmctools.addnewfolder( CHANNELNAME , "videolist"      , "" , "Novedades","http://yotix.tv/","","")
	xbmctools.addnewfolder( CHANNELNAME , "listcategorias" , "" , "Listado por categorías","http://yotix.tv/","","")
	xbmctools.addnewfolder( CHANNELNAME , "search"         , "" , "Buscador","http://yotix.tv/","","")

	if config.getSetting("singlechannel")=="true":
		xbmctools.addSingleChannelOptions(params,url,category)

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def search(params,url,category):
	logger.info("[yotix.py] search")

	keyboard = xbmc.Keyboard('')
	keyboard.doModal()
	if (keyboard.isConfirmed()):
		tecleado = keyboard.getText()
		if len(tecleado)>0:
			#convert to HTML
			tecleado = tecleado.replace(" ", "+")
			searchUrl = "http://yotix.tv/?s="+tecleado
			videolist(params,searchUrl,category)

def performsearch(texto):
	logger.info("[yotix.py] performsearch")
	url = "http://yotix.tv/?s="+texto

	# Descarga la página
	data = scrapertools.cachePage(url)

	# Extrae las entradas (carpetas)
	patronvideos  = '<div class="galleryitem">[^<]+'
	patronvideos += '<h1><a title="([^"]+)"[^<]+</a></h1>[^<]+'
	patronvideos += '<a href="([^"]+)"><img src="([^"]+)"'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)
	
	resultados = []

	for match in matches:
		# Atributos
		scrapedtitle = match[0].replace("&#8211;","-")
		scrapedurl = match[1]
		scrapedthumbnail = match[2]
		scrapedplot = ""

		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		resultados.append( [CHANNELNAME , "listmirrors" , "buscador" , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot ] )
		
	return resultados

def listcategorias(params,url,category):
	logger.info("[yotix.py] listcategorias")

	# ------------------------------------------------------
	# Descarga la página
	# ------------------------------------------------------
	data = scrapertools.cachePage(url)
	#logger.info(data)

	# ------------------------------------------------------
	# Extrae las entradas de la home como carpetas
	# ------------------------------------------------------
	patron  = '<a href="(/categoria/[^"]+)">([^<]+)</a>'

	matches = re.compile(patron,re.DOTALL).findall(data)
	if DEBUG: scrapertools.printMatches(matches)

	for match in matches:
		# Atributos
		scrapedtitle = match[1]
		scrapedurl = urlparse.urljoin(url,match[0])
		scrapedthumbnail = ""
		scrapedplot = ""
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELNAME , "videolist" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def videolist(params,url,category):
	logger.info("[yotix.py] videolist")

	# ------------------------------------------------------
	# Descarga la página
	# ------------------------------------------------------
	data = scrapertools.cachePage(url)
	#logger.info(data)

	# ------------------------------------------------------
	# Extrae las entradas de la home como carpetas
	# ------------------------------------------------------
	patron  = '<div class="galleryitem">[^<]+'
	patron += '<h1><a title="([^"]+)"[^<]+</a></h1>[^<]+'
	patron += '<a href="([^"]+)"><img src="([^"]+)"'

	matches = re.compile(patron,re.DOTALL).findall(data)
	if DEBUG: scrapertools.printMatches(matches)

	for match in matches:
		# Atributos
		scrapedtitle = match[0].replace("&#8211;","-")
		scrapedurl = match[1]
		scrapedthumbnail = match[2]
		scrapedplot = ""
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELNAME , "listmirrors" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# ------------------------------------------------------
	# Extrae la página siguiente
	# ------------------------------------------------------
	patron = '<a href="([^"]+)" >&raquo;</a>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	if DEBUG: scrapertools.printMatches(matches)

	for match in matches:
		scrapedtitle = "Pagina siguiente"
		scrapedurl = match
		scrapedthumbnail = ""
		scrapeddescription = ""
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		xbmctools.addthumbnailfolder( CHANNELNAME , scrapedtitle , scrapedurl , scrapedthumbnail, "mainlist" )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def listmirrors(params,url,category):
	logger.info("[yotix.py] listmirrors")

	title = urllib.unquote_plus( params.get("title") )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = urllib.unquote_plus( params.get("plot") )

	# Descarga la página de detalle
	data = scrapertools.cachePage(url)
	#logger.info(data)
	
	# Extrae el argumento
	patronvideos  = '<div class="texto-sinopsis">(.*?)<div'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)
	if len(matches)>0:
		plot = scrapertools.htmlclean(matches[0].strip())

	# Extrae los enlaces si el video está en la misma página
	patron = 'so.addParam\(\'flashvars\',\'.*?file\=([^\&]+)\&'
	matches = re.compile(patron,re.DOTALL).findall(data)
	if len(matches)>0:
		url = matches[0]
		xbmctools.addnewvideo( CHANNELNAME , "play2" , category , "Directo" , title , url , thumbnail , plot )

	# Extrae los enlaces a los vídeos (Megavídeo)
	patronvideos  = '<a.*?href="(http://yotix.tv/flash/[^"]+)"[^>]*>(.*?)</a>'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)		

	for match in matches:
		# Añade al listado de XBMC
		scrapedtitle = scrapertools.htmlclean(match[1].replace("&#8211;","-")).strip()
		scrapedurl = match[0]
		xbmctools.addnewvideo( CHANNELNAME , "play" , category , "Megavideo" , scrapedtitle , scrapedurl , thumbnail , plot )

	# Extrae los enlaces a los vídeos (Directo)
	extraevideos('<a.*?href="(http://yotix.tv/sitio/[^"]+)"[^>]*>(.*?)</a>',data,category,thumbnail,plot)
	extraevideos('<a.*?href="(http://yotix.tv/media/[^"]+)"[^>]*>(.*?)</a>',data,category,thumbnail,plot)
	extraevideos('<a.*?href="(http://yotix.tv/video/[^"]+)"[^>]*>(.*?)</a>',data,category,thumbnail,plot)
	extraevideos('<a.*?href="(http://yotix.tv/ver/[^"]+)"[^>]*>(.*?)</a>',data,category,thumbnail,plot)
	extraevideos('<a.*?href="(http://yotix.tv/rt/[^"]+)"[^>]*>(.*?)</a>',data,category,thumbnail,plot)
	extraevideos('<a.*?href="(http://yotix.tv/anime/[^"]+)"[^>]*>(.*?)</a>',data,category,thumbnail,plot)
	extraevideos('<a.*?href="(http://yotix.tv/gb/[^"]+)"[^>]*>(.*?)</a>',data,category,thumbnail,plot)
	extraevideos('<a.*?href="(http://yotix.tv/online/[^"]+)"[^>]*>(.*?)</a>',data,category,thumbnail,plot)

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def extraevideos(patronvideos,data,category,thumbnail,plot):
	logger.info("patron="+patronvideos)
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)		

	for match in matches:
		scrapedtitle = scrapertools.htmlclean(match[1].replace("&#8211;","-")).strip()
		scrapedurl = match[0]
		xbmctools.addnewvideo( CHANNELNAME , "play" , category , "Directo" , scrapedtitle , scrapedurl , thumbnail , plot )

def play(params,url,category):
	logger.info("[yotix.py] play")

	title = urllib.unquote_plus( params.get("title") )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = urllib.unquote_plus( params.get("plot") )
	server = urllib.unquote_plus( params.get("server") )

	# Abre dialogo
	dialogWait = xbmcgui.DialogProgress()
	dialogWait.create( 'Accediendo al video...', title , plot )

	if server=="Directo":
		# Descarga la página del reproductor
		# http://yotix.com/flash/UPY6KEB4/cleaner.html
		logger.info("url="+url)
		data = scrapertools.cachePage(url)

		patron = 'so.addParam\(\'flashvars\',\'\&file\=([^\&]+)\&'
		matches = re.compile(patron,re.DOTALL).findall(data)
		if len(matches)>0:
			url = matches[0]
	else:
		patron = 'http://yotix.tv/flash/([^\/]+)/'
		matches = re.compile(patron,re.DOTALL).findall(url)
		if len(matches)>0:
			url = matches[0]

	logger.info("url="+url)

	# Cierra dialogo
	dialogWait.close()
	del dialogWait

	xbmctools.playvideo(CHANNELNAME,server,url,category,title,thumbnail,plot)

def play2(params,url,category):
	logger.info("[yotix.py] play")

	title = urllib.unquote_plus( params.get("title") )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = urllib.unquote_plus( params.get("plot") )
	server = urllib.unquote_plus( params.get("server") )

	xbmctools.playvideo(CHANNELNAME,server,url,category,title,thumbnail,plot)
