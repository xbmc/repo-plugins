# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para veranime
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

CHANNELNAME = "veranime"

# Esto permite su ejecución en modo emulado
try:
	pluginhandle = int( sys.argv[ 1 ] )
except:
	pluginhandle = ""

# Traza el inicio del canal
logger.info("[veranime.py] init")

DEBUG = True

def mainlist(params,url,category):
	logger.info("[veranime.py] mainlist")

	# Menu principal
	xbmctools.addnewfolder( CHANNELNAME , "newlist" , CHANNELNAME , "Novedades" , "http://ver-anime.net/" , "", "" )
	xbmctools.addnewfolder( CHANNELNAME , "fulllist" , CHANNELNAME , "Listado completo" , "http://ver-anime.net/" , "", "" )

	# Asigna el título, desactiva la ordenación, y cierra el directorio
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def fulllist(params,url,category):
	logger.info("[veranime.py] fulllist")

	# Descarga la página
	data = scrapertools.cachePage(url)
	#logger.info(data)

	# Patron de las entradas
	#<li><a href="http://ver-anime.net/07-ghost/"><span>07 Ghost</span></a></li>
	#patron = '<li><a title="[^"]+" href="([^"]+)">([^<]+)</a></li>'
	patron = '<li><a href="(http://ver-anime.net/[^"]+)"><span>([^<]+)</span></a></li>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	# Añade las entradas encontradas
	for match in matches:
		# Atributos
		scrapedtitle = match[1]
		scrapedurl = urlparse.urljoin(url,match[0])
		scrapedthumbnail = ""
		scrapedplot = ""
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELNAME , "listmirrors" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# Asigna el título, desactiva la ordenación, y cierra el directorio
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def newlist(params,url,category):
	logger.info("[veranime.py] listmirrors")

	# Descarga la página
	data = scrapertools.cachePage(url)
	#logger.info(data)

	# Extrae las entradas (carpetas)
	'''
	<div class="item"><div class="boxgrid captionfull"><a href="http://ver-anime.net/demonbane/" title="Demonbane"><img src="http://ver-anime.net/images/Demonbane.gif"
	
	<div class="item">
	<div class="boxgrid captionfull"><a href="http://ver-anime.net/suzuka/" title="Suzuka"><img src="http://ver-anime.net/images/Suzuka.gif" alt="Suzuka" width="164" height="250" border="0"/></a>
	<div class="cover boxcaption"><h1><a href="http://ver-anime.net/suzuka/" title="Suzuka">Suzuka</a></h1></div>
	</div>
	</div>
	'''
	#patron  = '<td style="width.25."><div class="fondoimg"><div class="background"><a href="([^"]+)" title="([^"]+)">'
	#patron += '<strong><h3>[^<]+</h3></strong></a><br/><div class="borde-interior2"><a href="[^"]+" title="[^"]+">[^<]+'
	#patron += '<img src="([^"]+)" alt="[^"]+"/></a></div></div></div></td>'

	patron   = '<div class="item">[^<]*'
	patron  += '<div class="boxgrid captionfull"><a href="([^"]+)" title="([^"]+)"><img src="([^"]+)"' # alt="Suzuka" width="164" height="250" border="0"/></a>[^<]+'
	#patron  += '<div class="cover boxcaption"><h1><a href="http://ver-anime.net/suzuka/" title="Suzuka">Suzuka</a></h1></div>[^<]+'
	#patron  += '</div>[^<]+'
	#patron  += '</div>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	for match in matches:
		scrapedtitle = match[1]
		scrapedurl = urlparse.urljoin(url,match[0])
		scrapedthumbnail = urlparse.urljoin(url,match[2]).replace(" ","%20")
		scrapedplot = ""
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELNAME , "listmirrors" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# Asigna el título, desactiva la ordenación, y cierra el directorio
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def listmirrors(params,url,category):
	logger.info("[veranime.py] listmirrors")

	title = urllib.unquote_plus( params.get("title") )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = urllib.unquote_plus( params.get("plot") )

	# Descarga la página
	data = scrapertools.cachePage(url)
	#logger.info(data)

	# Extrae la sinopsis
	patron  = '<div class="contenido">[^<]+'
	patron += '<div class="caratula"><img src="[^"]+"[^>]+></div>[^<]+'
	patron += '<p>([^<]+)<'

	matches = re.compile(patron,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)
	if len(matches)>0:
		plot = matches[0].strip()
		logger.info(plot)

	patron = '<a title="[^"]+" href="([^"]+)">([^<]+)</a>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	for match in matches:
		scrapedtitle = match[1]
		scrapedurl = urlparse.urljoin(url,match[0])
		scrapedthumbnail = thumbnail
		scrapedplot = plot
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELNAME , "detail" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# Asigna el título, desactiva la ordenación, y cierra el directorio
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def detail(params,url,category):
	logger.info("[veranime.py] detail")

	title = urllib.unquote_plus( params.get("title") )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = urllib.unquote_plus( params.get("plot") )

	# Descarga la página
	data = scrapertools.cachePage(url)
	#logger.info(data)

	patron  = '<div id="listacapdd"><div class="listddserie">[^<]+'
	patron += '<a title="[^"]+" href="([^"]+)"><strong>[^<]+</strong></a>[^<]+'
	patron += '</div>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	if len(matches)>0:
		url = matches[0]
		data = scrapertools.cachePage(url)

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

	# Asigna el título, desactiva la ordenación, y cierra el directorio
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def play(params,url,category):
	logger.info("[veranime.py] play")

	title = unicode( xbmc.getInfoLabel( "ListItem.Title" ), "utf-8" )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = unicode( xbmc.getInfoLabel( "ListItem.Plot" ), "utf-8" )
	server = params["server"]
	
	xbmctools.playvideo(CHANNELNAME,server,url,category,title,thumbnail,plot)
