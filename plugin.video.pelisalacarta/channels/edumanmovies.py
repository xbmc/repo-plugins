# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para edumanmovies
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

CHANNELNAME = "edumanmovies"

# Esto permite su ejecución en modo emulado
try:
	pluginhandle = int( sys.argv[ 1 ] )
except:
	pluginhandle = ""

# Traza el inicio del canal
logger.info("[edumanmovies.py] init")

DEBUG = True

def mainlist(params,url,category):
	logger.info("[edumanmovies.py] mainlist")

	# Añade al listado de XBMC
	xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , "Películas - Novedades"            ,"http://edumanmovies.com/","","")
	xbmctools.addnewfolder( CHANNELNAME , "peliscat"   , category , "Películas - Lista por categorías" ,"http://edumanmovies.com/","","")
	xbmctools.addnewfolder( CHANNELNAME , "pelisalfa"  , category , "Películas - Lista alfabética"     ,"","","")
	xbmctools.addnewfolder( CHANNELNAME , "search"     , category , "Buscar"                           ,"","","")

	if config.getSetting("singlechannel")=="true":
		xbmctools.addSingleChannelOptions(params,url,category)

	# Cierra el directorio
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def listvideos(params,url,category):
	logger.info("[edumanmovies.py] listvideos")

	# Descarga la página
	data = scrapertools.cachePage(url)
	#logger.info(data)

	# Extrae las entradas (carpetas)
	patronvideos  = '<div class="item">[^<]+'
	patronvideos += '<div class="thumbwrap">[^<]+'
	patronvideos += '<div class="thumbnail" style="background. url\(([^\)]+)\) top left no-repeat.">[^<]+'
	patronvideos += '<a href="([^"]+)" Title="[^"]+"><img[^>]+></a>[^<]+'
	patronvideos += '</div>[^<]+'
	patronvideos += '</div>[^<]+'
	patronvideos += '<div class="content">[^<]+'
	patronvideos += '<h2><a href="[^"]+">([^<]+)</a></h2>[^<]+'
	patronvideos += '<p>([^<]+)<'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)
	
	for match in matches:
		# Atributos
		scrapedtitle = match[2]
		scrapedurl = urlparse.urljoin(url,match[1])
		scrapedthumbnail = urlparse.urljoin(url,match[0])
		scrapedplot = match[3]
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELNAME , "detail" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# Extrae la marca de siguiente página
	patronvideos  = '<a href="([^"]+)" class="nextpostslink">.raquo.</a>'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	if len(matches)>0:
		scrapedtitle = "Página siguiente"
		scrapedurl = urlparse.urljoin(url,matches[0])
		scrapedthumbnail = ""
		scrapedplot = ""
		xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def pelisalfa(params, url, category):

	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "0-9","http://edumanmovies.com/tag/0-9/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "A","http://edumanmovies.com/tag/A/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "B","http://edumanmovies.com/tag/B/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "C","http://edumanmovies.com/tag/C/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "D","http://edumanmovies.com/tag/D/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "E","http://edumanmovies.com/tag/E/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "F","http://edumanmovies.com/tag/F/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "G","http://edumanmovies.com/tag/G/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "H","http://edumanmovies.com/tag/H/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "I","http://edumanmovies.com/tag/I/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "J","http://edumanmovies.com/tag/J/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "K","http://edumanmovies.com/tag/K/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "L","http://edumanmovies.com/tag/L/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "M","http://edumanmovies.com/tag/M/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "N","http://edumanmovies.com/tag/N/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "O","http://edumanmovies.com/tag/O/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "P","http://edumanmovies.com/tag/P/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "Q","http://edumanmovies.com/tag/Q/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "R","http://edumanmovies.com/tag/R/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "S","http://edumanmovies.com/tag/S/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "T","http://edumanmovies.com/tag/T/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "U","http://edumanmovies.com/tag/U/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "V","http://edumanmovies.com/tag/V/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "W","http://edumanmovies.com/tag/W/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "X","http://edumanmovies.com/tag/X/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "Y","http://edumanmovies.com/tag/Y/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "Z","http://edumanmovies.com/tag/Z/","","")

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def search(params,url,category):
	logger.info("[edumanmovies.py] search")

	keyboard = xbmc.Keyboard('')
	keyboard.doModal()
	if (keyboard.isConfirmed()):
		tecleado = keyboard.getText()
		if len(tecleado)>0:
			#convert to HTML
			tecleado = tecleado.replace(" ", "+")
			searchUrl = "http://edumanmovies.com/?s="+tecleado
			listvideos(params,searchUrl,category)

def performsearch(texto):
	logger.info("[edumanmovies.py] performsearch")
	url = "http://edumanmovies.com/?s="+texto

	# Descarga la página
	data = scrapertools.cachePage(url)

	# Extrae las entradas (carpetas)
	patronvideos  = '<div class="item">[^<]+'
	patronvideos += '<div class="thumbwrap">[^<]+'
	patronvideos += '<div class="thumbnail" style="background. url\(([^\)]+)\) top left no-repeat.">[^<]+'
	patronvideos += '<a href="([^"]+)" Title="[^"]+"><img[^>]+></a>[^<]+'
	patronvideos += '</div>[^<]+'
	patronvideos += '</div>[^<]+'
	patronvideos += '<div class="content">[^<]+'
	patronvideos += '<h2><a href="[^"]+">([^<]+)</a></h2>[^<]+'
	patronvideos += '<p>([^<]+)<'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)
	
	resultados = []

	for match in matches:
		# Atributos


		scrapedtitle = match[2]
		scrapedurl = urlparse.urljoin(url,match[1])
		scrapedthumbnail = urlparse.urljoin(url,match[0])
		scrapedplot = match[3]
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		resultados.append( [CHANNELNAME , "detail" , "buscador" , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot ] )

	return resultados

def peliscat(params,url,category):
	logger.info("[edumanmovies.py] peliscat")

	# Descarga la página
	data = scrapertools.cachePage(url)

	# Extrae las entradas (carpetas)
	patronvideos  = '<li class="cat-item cat-item-3"><a href="([^"]+)" title="[^"]+">([^<]+)</a>'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	for match in matches:
		# Atributos
		scrapedtitle = match[1]
		scrapedurl = urlparse.urljoin(url,match[0])
		scrapedthumbnail = ""
		scrapedplot = ""
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def detail(params,url,category):
	logger.info("[edumanmovies.py] detail")

	title = urllib.unquote_plus( params.get("title") )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = urllib.unquote_plus( params.get("plot") )

	# Descarga la página
	data = scrapertools.cachePage(url)
	#logger.info(data)
	#<iframe name="frame" marginwidth="0" marginheight="0" src="/p.php?f=43&#038;n=negrologoxd" scrolling="no" frameborder="0"

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

	# Cierra el directorio
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def play(params,url,category):
	logger.info("[edumanmovies.py] play")

	title = unicode( xbmc.getInfoLabel( "ListItem.Title" ), "utf-8" )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = unicode( xbmc.getInfoLabel( "ListItem.Plot" ), "utf-8" )
	server = params["server"]
	
	xbmctools.playvideo(CHANNELNAME,server,url,category,title,thumbnail,plot)
