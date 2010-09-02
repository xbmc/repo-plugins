# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para dibujosanimadosgratis
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

CHANNELNAME = "dibujosanimadosgratis"

# Esto permite su ejecución en modo emulado
try:
	pluginhandle = int( sys.argv[ 1 ] )
except:
	pluginhandle = ""

# Traza el inicio del canal
logger.info("[dibujosanimadosgratis.py] init")

DEBUG = True

def mainlist(params,url,category):
	logger.info("[dibujosanimadosgratis.py] mainlist")
	xbmctools.addnewfolder( CHANNELNAME , "novedades" , CHANNELNAME , "Novedades" , "http://dibujosanimadosgratis.net/" , "", "" )
	xbmctools.addnewfolder( CHANNELNAME , "categorias" , CHANNELNAME , "Por categorías" , "http://dibujosanimadosgratis.net/" , "", "" )
	
	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def categorias(params,url,category):
	logger.info("[dibujosanimadosgratis.py] categorias")
	
	# Descarga la página
	data = scrapertools.cachePage(url)
	#logger.info(data)

	# Extrae las entradas
	patron  = '<li class="cat-item cat-item[^"]+"><a href="([^"]+)" title="[^"]+">([^"]+)</a>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	for match in matches:
		scrapedtitle = match[1]
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
	logger.info("[dibujosanimadosgratis.py] novedades")
	
	# Descarga la página
	data = scrapertools.cachePage(url)
	#logger.info(data)

	# Extrae las entradas
	'''
	<div class="post">
	<h2 class="postTitle"><a href="http://dibujosanimadosgratis.net/ranma/ranma-%c2%bd-episodio-141-13-audio-latino-dvdrip-hq.html">Ranma ½ Episodio 141 1/3 Audio Latino DVDRip HQ</a></h2>
	<div class="postMeta">
	<span class="date">May.08, 2010</span> en
	<span class="filed"><a href="http://dibujosanimadosgratis.net/category/ranma" title="Ver todas las entradas en Ranma" rel="category tag">Ranma</a></span>
	<span class="commentcount"><a href="http://dibujosanimadosgratis.net/ranma/ranma-%c2%bd-episodio-141-13-audio-latino-dvdrip-hq.html#respond" title="Comentarios en Ranma ½ Episodio 141 1/3 Audio Latino DVDRip HQ">Deja tu Comentario</a></span>
	</div>
	<div class="postContent"><p>				<img src="http://i4.ytimg.com/vi/sv4uf5Q0PO4/default.jpg" align="right" border="0" width="120" height="90" vspace="4" hspace="4" />
	</p>
	<p>					Author: <a href="http://youtube.com/profile?user=AlucardReturn08">AlucardReturn08</a><br/>					Keywords:  <br/>					Added: May 8, 2010<br/>				</p>
	<p><object width="425" height="350"><param name="movie" value="http://www.youtube.com/v/sv4uf5Q0PO4"></param><param name="wmode" value="transparent"></param><embed src="http://www.youtube.com/v/sv4uf5Q0PO4" type="application/x-shockwave-flash" wmode="transparent" width="425" height="350"></embed></object></p>
	</div>
	</div> <!-- Closes Post -->
	'''
	patron  = '<div class="post">[^<]+'
	patron += '<h2 class="postTitle"><a href="([^"]+)">([^<]+)</a></h2>(.*?)</div> <!-- Closes Post -->'
	matches = re.compile(patron,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	for match in matches:
		scrapedtitle = match[1]
		scrapedurl = urlparse.urljoin(url,match[0])
		scrapedthumbnail = ""
		patronthumb = '<img src="([^"]+)"'
		matchesthumb = re.compile(patronthumb,re.DOTALL).findall(match[2])
		if len(matchesthumb)>0:
			scrapedthumbnail = matchesthumb[0]
		scrapedplot = ""
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")
		xbmctools.addnewfolder( CHANNELNAME , "detail" , category , scrapedtitle , scrapedurl , scrapedthumbnail , scrapedplot )

	patron  = '<a href="([^"]+)">&laquo; videos anteriores</a>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)
	if len(matches)>0:
		scrapedtitle = "!Página siguiente"
		scrapedurl = urlparse.urljoin(url,matches[0])
		scrapedthumbnail = ""
		scrapedplot = ""
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")
		xbmctools.addnewfolder( CHANNELNAME , "novedades" , category , scrapedtitle , scrapedurl , scrapedthumbnail , scrapedplot )

	patron  = '<a href="([^"]+)">&laquo; previous entries</a>'
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
	logger.info("[dibujosanimadosgratis.py] detail")

	# Recupera los parámetros
	title = urllib.unquote_plus( params.get("title") )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = urllib.unquote_plus( params.get("plot") )

	# Descarga la página de detalle
	'''
	<div class="post">
	<h2 class="postTitle"><a href="http://dibujosanimadosgratis.net/ranma/ranma-%c2%bd-episodio-142-33-audio-latino-dvdrip-hq.html">Ranma ½ Episodio 142 3/3 Audio Latino DVDRip HQ</a></h2>
	<div class="postMeta">
	<span class="date">May.08, 2010</span> en
	<span class="filed"><a href="http://dibujosanimadosgratis.net/category/ranma" title="Ver todas las entradas en Ranma" rel="category tag">Ranma</a></span>
	</div>
	<div class="postContent"><p>				<img src="http://i4.ytimg.com/vi/3k4YsDCdfoA/default.jpg" align="right" border="0" width="120" height="90" vspace="4" hspace="4" />
	</p>
	<p>					Author: <a href="http://youtube.com/profile?user=AlucardReturn08">AlucardReturn08</a><br/>					Keywords:  <br/>					Added: May 8, 2010<br/>				</p>
	<p><object width="425" height="350"><param name="movie" value="http://www.youtube.com/v/3k4YsDCdfoA"></param><param name="wmode" value="transparent"></param><embed src="http://www.youtube.com/v/3k4YsDCdfoA" type="application/x-shockwave-flash" wmode="transparent" width="425" height="350"></embed></object></p>
	</div>
	'''
	data = scrapertools.cachePage(url)
	patron = '<div class="post">(.*?<div class="postMeta">.*?<div class="postContent">.*?)</div>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	if len(matches)>0:
		data = matches[0]
		logger.info(data)
		
		# Plot
		scrapedplot = scrapertools.htmlclean(data)
		scrapedplot = scrapedplot.replace("\n"," ")
		scrapedplot = scrapedplot.replace("\r"," ")
		
		# Thumbnail
		patron = '<img src="([^"]+)"'
		matches = re.compile(patron,re.DOTALL).findall(data)
		scrapedthumbnail = ""
		if len(matches)>0:
			scrapedthumbnail = matches[0]
		
		# ------------------------------------------------------------------------------------
		# Busca los enlaces a los videos conocidos en el iframe
		# ------------------------------------------------------------------------------------
		listavideos = servertools.findvideos(data)

		for video in listavideos:
			videotitle = video[0]
			url = video[1]
			server = video[2]
			xbmctools.addnewvideo( CHANNELNAME , "play" , category , server , title.strip() + " - " + videotitle , url , scrapedthumbnail , scrapedplot )
		# ------------------------------------------------------------------------------------

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def play(params,url,category):
	logger.info("[dibujosanimadosgratis.py] play")

	title = unicode( xbmc.getInfoLabel( "ListItem.Title" ), "utf-8" )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = unicode( xbmc.getInfoLabel( "ListItem.Plot" ), "utf-8" )
	server = params["server"]
	
	xbmctools.playvideo(CHANNELNAME,server,url,category,title,thumbnail,plot)
