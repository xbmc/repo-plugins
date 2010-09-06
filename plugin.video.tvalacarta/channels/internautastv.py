# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# tvalacarta - XBMC Plugin
# Canal para InternautasTV
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
import logger

try:
	pluginhandle = int( sys.argv[ 1 ] )
except:
	pluginhandle = ""

logger.info("[internautastv.py] init")

DEBUG = True
CHANNELNAME = "internautastv"
CHANNELCODE = "internautastv"

def mainlist(params,url,category):
	logger.info("[internautastv.py] mainlist")

	# Añade al listado de XBMC
	xbmctools.addnewfolder( CHANNELCODE , "ultimosvideos"   , CHANNELNAME , "Últimos vídeos"     , "http://www.internautas.tv/backend/mp4.xml" , "" , "" )
	xbmctools.addnewfolder( CHANNELCODE , "archivo"         , CHANNELNAME , "Archivo"            , "http://www.internautas.tv/" , "" , "" )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def ultimosvideos(params,url,category):
	logger.info("[internautastv.py] ultimosvideos")

	# Descarga la página
	data = scrapertools.cachePage(url)
	#logger.info(data)

	# Vídeos del RSS
	'''
	<item>
	<title>Polémicas declaraciones de Enrique Urbizu</title>
	<link>http://www.internautas.tv/programa/706.html</link>
	<description>No ha dejado a nadie indiferente las declaraciones del presidente de DAMA en la que le parece incluso que la polemica ley de los 3 avisos es insuficiente  </description>
	<enclosure url="http://serv2.internautas.tv/videos/m4v/20091229_1.m4v" type="video/m4v" />
	<pubDate>Tue, 29 Dec 2009 07:00:00 GMT</pubDate>
	<guid isPermaLink="true">http://www.internautas.tv/programa/706.html</guid>
	</item>
	'''
	patron  = '<item>[^<]+'
	patron += '<title>([^<]+)</title>[^<]+'
	patron += '<link>[^<]+</link>[^<]+'
	patron += '<description>([^<]+)</description>[^<]+'
	patron += '<enclosure url="([^"]+)"[^>]+>[^<]+'
	patron += '<pubDate>([^<]+)</pubDate>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	for match in matches:
		# Atributos del vídeo
		scrapedtitle = match[0].strip()+" ("+match[3].strip()+")"
		scrapedurl = urlparse.urljoin(url,match[2])
		scrapedthumbnail = ""
		scrapedplot = match[1].strip()
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		xbmctools.addnewvideo( CHANNELCODE , "play" , category , "Directo" , scrapedtitle , scrapedurl , scrapedthumbnail , scrapedplot )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def archivo(params,url,category):
	logger.info("[internautastv.py] archivo")

	# Descarga la página
	data = scrapertools.cachePage(url)
	#logger.info(data)

	# Busca la URL del archivo
	patron  = '<div class="barraopcion"><a href="([^"]+)">Archivo</a></div>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)
	if len(matches)==0:
		xbmctools.alerterrorpagina()
		return
	
	url = urlparse.urljoin(url,matches[0])

	videosmes(params,url,category)

def videosmes(params,url,category):
	logger.info("[internautastv.py] videosmes")

	# Descarga la página
	data = scrapertools.cachePage(url)
	#logger.info(data)

	# Busca los videos del mes
	patron  = '<div class="cx7">([^<]+)<div class="ie"><a href="([^"]+)" title="([^"]+)" alt=""><img src="([^"]+)"'
	matches = re.compile(patron,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	for match in matches:
		# Atributos del vídeo
		scrapedtitle = "Día "+match[0]+" - "+match[2].strip()
		scrapedurl = urlparse.urljoin(url,match[1])
		scrapedthumbnail = urlparse.urljoin(url,match[3])
		scrapedplot = scrapedtitle
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELCODE , "detail" , CHANNELNAME , scrapedtitle , scrapedurl , scrapedthumbnail , scrapedplot )

	# Busca los videos del mes
	patron  = '<div class="cx8">([^<]+)<div class="ie"><a href="([^"]+)" title="([^"]+)" alt=""><img src="([^"]+)"'
	matches = re.compile(patron,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	for match in matches:
		# Atributos del vídeo
		scrapedtitle = "Día "+match[0]+" - "+match[2].strip()
		scrapedurl = urlparse.urljoin(url,match[1])
		scrapedthumbnail = urlparse.urljoin(url,match[3])
		scrapedplot = scrapedtitle
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELCODE , "detail" , CHANNELNAME , scrapedtitle , scrapedurl , scrapedthumbnail , scrapedplot )

	# Busca el enlace al mes anterior
	patron  = '<a href="([^"]+)">&lt;&lt;&lt;&nbsp;([^<]+)</a>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	for match in matches:
		# Atributos del vídeo
		scrapedtitle = "<< "+match[1].strip()
		scrapedurl = urlparse.urljoin(url,match[0])
		scrapedthumbnail = ""
		scrapedplot = ""
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELCODE , "videosmes" , CHANNELNAME , scrapedtitle , scrapedurl , scrapedthumbnail , scrapedplot )

	# Busca el enlace al mes siguiente
	patron  = '<a href="([^"]+)">([^\&]+)&nbsp;&gt;&gt;&gt;</a>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	for match in matches:
		# Atributos del vídeo
		scrapedtitle = ">> "+match[1].strip()
		scrapedurl = urlparse.urljoin(url,match[0])
		scrapedthumbnail = ""
		scrapedplot = ""
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELCODE , "videosmes" , CHANNELNAME , scrapedtitle , scrapedurl , scrapedthumbnail , scrapedplot )
	
	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def detail(params,url,category):
	logger.info("[internautastv.py] detail")

	title = urllib.unquote_plus( params.get("title") )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )

	# Descarga la página
	data = scrapertools.cachePage(url)
	#logger.info(data)

	# Busca los videos del mes
	patron  = '<div class="c">.*?<span class="t2">([^<]+)</span>.*?'
	patron += '<div class="v1"><a href="([^"]+)"><img src="\/graficos\/lmp4\.jpg"'
	matches = re.compile(patron,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	for match in matches:
		# Atributos del vídeo
		scrapedtitle = title
		scrapedurl = match[1]
		scrapedthumbnail = thumbnail
		scrapedplot = match[0]
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		xbmctools.addnewvideo( CHANNELCODE , "play" , category , "Directo" , scrapedtitle , scrapedurl , scrapedthumbnail , scrapedplot )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def play(params,url,category):
	logger.info("[internautastv.py] play")

	title = unicode( xbmc.getInfoLabel( "ListItem.Title" ), "utf-8" )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = unicode( xbmc.getInfoLabel( "ListItem.Plot" ), "utf-8" )
	server = "Directo"

	xbmctools.playvideo(CHANNELCODE,server,url,category,title,thumbnail,plot)
