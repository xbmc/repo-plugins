# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para frozenlayer
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

CHANNELNAME = "frozenlayer"

# Esto permite su ejecución en modo emulado
try:
	pluginhandle = int( sys.argv[ 1 ] )
except:
	pluginhandle = ""

# Traza el inicio del canal
logger.info("[frozenlayer.py] init")

DEBUG = True

def mainlist(params,url,category):
	logger.info("[frozenlayer.py] mainlist")

	#53=wall
	#xbmc.executebuiltin("Container.SetViewMode(53)")

	if url=='':
		url = "http://www.frozen-layer.com/anime/streaming"

	# ------------------------------------------------------
	# Descarga la página
	# ------------------------------------------------------
	data = scrapertools.cachePage(url)
	#logger.info(data)

	# ------------------------------------------------------
	# Series de la página
	# ------------------------------------------------------
	patron  = '<tr class="nada">[^<]+<td class="lista_titulo">[^<]+<a href="([^"]+)">([^<]+)</a>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	if DEBUG:
		scrapertools.printMatches(matches)

	for match in matches:
		scrapedtitle = match[1]
		scrapedurl = match[0]
		scrapedthumbnail = ""
		
		#http://www.frozen-layer.com/animes/2743-afro-samurai
		#http://flnimg.frozen-layer.com/images/anime/2743/portada.jpg
		patronurl = 'http\:\/\/www.frozen-layer.com\/animes\/([0-9]+)'
		matchesurl = re.compile(patronurl,re.DOTALL).findall(scrapedurl)
		scrapertools.printMatches(matchesurl)
		codigo=''
		if len(matchesurl)>0:
			codigo=matchesurl[0]
			scrapedthumbnail = 'http://flnimg.frozen-layer.com/images/anime/'+codigo+'/portada.jpg'

		# Mete el código del anime en el argumento
		scrapedplot = codigo

		# Depuracion
		if DEBUG:
			logger.info("scrapedtitle="+scrapedtitle)
			logger.info("scrapedurl="+scrapedurl)
			logger.info("scrapedthumbnail="+scrapedthumbnail)
			logger.info("scrapedplot="+scrapedplot)

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# ------------------------------------------------------
	# Página siguiente
	# ------------------------------------------------------
	patron = '<a href="([^"]+)" class="next_page" rel="next">Siguiente >></a>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	if DEBUG:
		scrapertools.printMatches(matches)

	for match in matches:
		scrapedtitle = "Pagina siguiente"
		scrapedurl = urlparse.urljoin(url,match)
		scrapedthumbnail = ""
		scrapedplot = ""
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELNAME , "mainlist" , category , scrapedtitle , scrapedurl , scrapedthumbnail , scrapedplot )

	if config.getSetting("singlechannel")=="true":
		xbmctools.addSingleChannelOptions(params,url,category)

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def listvideos(params,url,category):
	logger.info("[frozenlayer.py] listvideos")

	#50=full list
	#xbmc.executebuiltin("Container.SetViewMode(50)")

	title = urllib.unquote_plus( params.get("title") )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	# Saca el código del anime del argumento
	codigo = urllib.unquote_plus( params.get("plot") )
	plot = ""

	# ------------------------------------------------------
	# Descarga la página de detalle
	# ------------------------------------------------------
	#http://www.frozen-layer.com/anime/1991/descargas/streaming#t
	url = 'http://www.frozen-layer.com/anime/'+codigo+'/descargas/streaming'
	data = scrapertools.cachePage(url)
	#logger.info(data)
	
	# ------------------------------------------------------
	# Extrae el argumento
	# ------------------------------------------------------
	patronvideos  = '<p class="desc " id="sinopsis">(.*?)</p>'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	if len(matches)>0:
		plot = matches[0].strip()
	logger.info("[frozenlayer.py] plot=%s" % plot)
	
	# ------------------------------------------------------
	# Enlaces a los vídeos
	# ------------------------------------------------------
	patronvideos  = '<tr  class=".*?">[^<]+'
	patronvideos += '<td><a href="([^"]+)".*?'
	patronvideos += '<td class="tit streaming"><a.*?>(.*?)</td>[^<]+'
	patronvideos += '<td class="flags">(.*?)</td>[^<]+'
	patronvideos += '<td>[^<]+</td>[^<]+'
	patronvideos += '<td>.*?</td>[^<]+'
	patronvideos += '<td colspan="2">([^<]+)</td>'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)		

	for match in matches:
		scrapedtitle = match[1]
		scrapedtitle = scrapedtitle.replace("</a>","")
		scrapedtitle = scrapedtitle.replace("\t"," ")
		
		scrapedurl = match[0]
		scrapedthumbnail = thumbnail
		scrapedplot = plot

		# Depuracion
		if DEBUG:
			logger.info("scrapedtitle="+scrapedtitle)
			logger.info("scrapedurl="+scrapedurl)
			logger.info("scrapedthumbnail="+scrapedthumbnail)
			logger.info("scrapedplot="+scrapedplot)

		# Añade al listado de XBMC
		server = ""
		if scrapedurl.startswith("http://www.megavideo.com"):
			server="Megavideo"
		elif scrapedurl.find("youku.com")<>-1:
			server="Youku"
		elif scrapedurl.find("tu.tv")<>-1:
			server="tu.tv"
		elif scrapedurl.find("veoh.com")<>-1:
			server="Veoh - NO SOPORTADO"
		elif scrapedurl.find("livevideo.com")<>-1:
			server="Livevideo - NO SOPORTADO"
		else:
			server="Desconocido"
		scrapedtitle = scrapedtitle + "(" + server + ")"
		
		xbmctools.addnewvideo( CHANNELNAME , "play" , category , server , scrapedtitle , scrapedurl , scrapedthumbnail , scrapedplot )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
		
	# Disable sorting...
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def play(params,url,category):
	logger.info("[frozenlayer.py] play")

	title = urllib.unquote_plus( params.get("title") )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = unicode( xbmc.getInfoLabel( "ListItem.Plot" ), "utf-8" )
	server = params["server"]

	# En tu.tv, la URL es la del detalle en el servidor
	if server=="tu.tv":
		data = scrapertools.cachePage(url)
		listavideos = servertools.findvideos(data)
		if len(listavideos)>0:
			url = listavideos[0][1]

	xbmctools.playvideo(CHANNELNAME,server,url,category,title,thumbnail,plot)
