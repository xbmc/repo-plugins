# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para sevillista
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

CHANNELNAME = "sevillista"

# Esto permite su ejecución en modo emulado
try:
	pluginhandle = int( sys.argv[ 1 ] )
except:
	pluginhandle = ""

# Traza el inicio del canal
logger.info("[sevillista.py] init")

DEBUG = True

def mainlist(params,url,category):
	logger.info("[sevillista.py] mainlist")
	xbmctools.addnewfolder( CHANNELNAME , "novedades" , CHANNELNAME , "Películas - Novedades" , "http://www.pelis-sevillista56.org/" , "", "" )
	xbmctools.addnewfolder( CHANNELNAME , "categorias" , CHANNELNAME , "Películas - Por categoría" , "http://www.pelis-sevillista56.org/" , "", "" )
	xbmctools.addnewfolder( CHANNELNAME , "novedades" , CHANNELNAME , "Series - Novedades" , "http://www.pelis-sevillista56.org/search/label/Series" , "", "" )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def categorias(params,url,category):
	logger.info("[sevillista.py] categorias")
	
	# Descarga la página
	data = scrapertools.cachePage(url)
	#logger.info(data)

	# Extrae las entradas
	'''
	<h2>Categorías</h2>
	<div class='widget-content list-label-widget-content'>
	<ul>
	<li>
	<a dir='ltr' href='http://pelis-sevillista56.blogspot.com/search/label/Acci%C3%B3n'>Acción</a>
	<span dir='ltr'>(246)</span>
	</li>
	<li>
	<a dir='ltr' href='http://pelis-sevillista56.blogspot.com/search/label/Aventuras'>Aventuras</a>
	<span dir='ltr'>(102)</span>
	</li>
	<li>
	'''
	patron  = "<h2>Categor[^<]+</h2>[^<]+"
	patron += "<div class='widget-content list-label-widget-content'>(.*?)</div>"
	matches = re.compile(patron,re.DOTALL).findall(data)
	if len(matches)>0:
		data = matches[0]
		patron  = "<a dir='ltr' href='([^']+)'>([^<]+)</a>[^<]+"
		patron += "<span dir='ltr'>([^<]+)</span>"
		matches = re.compile(patron,re.DOTALL).findall(data)

		for match in matches:
			scrapedtitle = match[1]+" "+match[2]
			scrapedurl = urlparse.urljoin(url,match[0])
			scrapedthumbnail = ""
			scrapedplot = ""
			if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")
			xbmctools.addnewfolder( CHANNELNAME , "novedades" , category , scrapedtitle , scrapedurl , scrapedthumbnail , scrapedplot )

	# Cierra el directorio
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def novedades(params,url,category):
	logger.info("[sevillista.py] novedades")
	
	# Descarga la página
	data = scrapertools.cachePage(url)
	#logger.info(data)

	# Extrae las entradas
	patron  = "<div class='post hentry'>[^<]+"
	patron += "<a name='[^']+'></a>[^<]+"
	patron += "<h3 class='post-title entry-title'>[^<]+"
	patron += "<a href='([^']+)'>([^<]+)</a>[^<]+"
	patron += "</h3>.*?"
	patron += '<img.*?src="([^"]+)"'

	matches = re.compile(patron,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	for match in matches:
		scrapedtitle = xbmctools.unseo(match[1])
		scrapedurl = urlparse.urljoin(url,match[0])
		scrapedthumbnail = urlparse.urljoin(url,match[2])
		scrapedplot = ""
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")
		xbmctools.addnewfolder( CHANNELNAME , "detail" , category , scrapedtitle , scrapedurl , scrapedthumbnail , scrapedplot )

	patron  = "<div id='blog-pager'>.*?a href='([^']+)' id='[^']+' title='Entradas antiguas'>"
	matches = re.compile(patron,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)
	if len(matches)>0:
		scrapedtitle = "!Página siguiente"
		scrapedurl = urlparse.urljoin(url,matches[0])
		scrapedthumbnail = ""
		scrapedplot = ""
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")
		xbmctools.addnewfolder( CHANNELNAME , "novedades" , category , scrapedtitle , scrapedurl , scrapedthumbnail , scrapedplot )

	# Cierra el directorio
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def detail(params,url,category):
	logger.info("[sevillista.py] detail")

	# Recupera los parámetros
	title = urllib.unquote_plus( params.get("title") )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = urllib.unquote_plus( params.get("plot") )

	# Descarga la página de detalle, y busca el iframe
	data = scrapertools.cachePage(url)
	patron = '<iframe marginwidth="0" marginheight="0" src="([^"]+)"'
	matches = re.compile(patron,re.DOTALL).findall(data)
	if len(matches)>0:
		# Descarga el iframe
		url = matches[0]
		data = scrapertools.cachePage(url)
		
		# Busca vídeos no megavideo (playlist externa)
		patron = '<param name="flashvars" value=".amp.skin=.amp.plugins.captions.amp.file.([^\&]+)\&'
		matches = re.compile(patron,re.DOTALL).findall(data)
		if len(matches)>0:
			# Descarga la playlist
			url = matches[0]
			if url.endswith(".xml"):
				data2 = scrapertools.cachePage(url)
				# Busca los vídeos
				#<title>Parte 1</title>
				#<annotation>Castellano</annotation>
				#<location>http://video.ak.facebook.com/cfs-ak-ash1/27673/000/219/106288556079917_23239.mp4</location>
				patron  = '<title>([^<]+)</title>[^>]*'
				patron += '<annotation>([^<]+)</annotation>[^>]*'
				patron += '<location>([^<]+)</location>'
				matches = re.compile(patron,re.DOTALL).findall(data2)
				
				for match in matches:
					scrapedtitle = title + " " + match[0]+" "+match[1]+" [Directo]"
					scrapedurl = urlparse.urljoin(url,match[2])
					scrapedthumbnail = thumbnail
					scrapedplot = plot
					if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")
					xbmctools.addnewvideo( CHANNELNAME , "play" , category , "Directo" , scrapedtitle , scrapedurl , scrapedthumbnail , scrapedplot )
			else:
				xbmctools.addnewvideo( CHANNELNAME , "play" , category , "Directo" , title + " [Directo]" , url , thumbnail , plot )
	
	# ------------------------------------------------------------------------------------
	# Busca los enlaces a los videos conocidos en el iframe
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
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def play(params,url,category):
	logger.info("[sevillista.py] play")

	title = unicode( xbmc.getInfoLabel( "ListItem.Title" ), "utf-8" )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = unicode( xbmc.getInfoLabel( "ListItem.Plot" ), "utf-8" )
	server = params["server"]
	
	xbmctools.playvideo(CHANNELNAME,server,url,category,title,thumbnail,plot)
