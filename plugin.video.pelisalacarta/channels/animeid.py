# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para animeid
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

CHANNELNAME = "animeid"

# Esto permite su ejecución en modo emulado
try:
	pluginhandle = int( sys.argv[ 1 ] )
except:
	pluginhandle = ""

# Traza el inicio del canal
logger.info("[animeid.py] init")

DEBUG = True

def mainlist(params,url,category):
	logger.info("[animeid.py] mainlist")
	xbmctools.addnewfolder( CHANNELNAME , "newlist"  , CHANNELNAME , "Novedades"              , "http://animeid.com/" , "", "" )
	xbmctools.addnewfolder( CHANNELNAME , "fulllist" , CHANNELNAME , "Listado completo"       , "http://animeid.com/" , "", "" )
	xbmctools.addnewfolder( CHANNELNAME , "catlist"  , CHANNELNAME , "Listado por categorias" , "http://animeid.com/anime/amagami-ss.html" , "", "" )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def catlist(params,url,category):

	# Descarga la página
	data = scrapertools.downloadpageGzip(url)
	#logger.info(data)

	# Extrae las entradas (carpetas)  <a class="accion linkFader" href="../accion-1.html"></a>
	patronvideos  = '<a class="([^"]+)" href="([^"]+)"></a>'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	for match in matches:
		scrapedtitle = match[0].replace("linkFader","").strip()
		scrapedurl = urlparse.urljoin(url,match[1])
		scrapedthumbnail = ""
		scrapeddescription = ""
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		xbmctools.addthumbnailfolder( CHANNELNAME , scrapedtitle , scrapedurl , scrapedthumbnail, "newlist" )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def fulllist(params,url,category):

	# Descarga la página
	data = scrapertools.downloadpageGzip(url)
	#logger.info(data)

	# Extrae las entradas (carpetas)
	patronvideos  = '<li><a href="([^"]+)"><span>([^<]+)</span></a></li>'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	for match in matches:
		scrapedtitle = match[1]
		scrapedurl = urlparse.urljoin(url,match[0])
		scrapedthumbnail = ""
		scrapeddescription = ""
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		xbmctools.addthumbnailfolder( CHANNELNAME , scrapedtitle , scrapedurl , scrapedthumbnail, "detail" )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def newlist(params,url,category):

	# Descarga la página
	data = scrapertools.downloadpageGzip(url)
	#logger.info(data)

	# Extrae las entradas (carpetas)
	patronvideos  = '<div class="item">.*?<a href="([^"]+)"[^<]+<img src="([^"]+)".*?<div class="cover boxcaption">[^<]+<h1>([^<]+)</h1>'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	for match in matches:
		scrapedtitle = match[2]
		scrapedurl = urlparse.urljoin(url,match[0])
		scrapedthumbnail = urlparse.urljoin(url,match[1])
		scrapeddescription = ""
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		xbmctools.addthumbnailfolder( CHANNELNAME , scrapedtitle , scrapedurl , scrapedthumbnail, "detail" )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def detail(params,url,category):
	logger.info("[animeid.py] detail")

	title = urllib.unquote_plus( params.get("title") )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )

	# Descarga la página
	data = scrapertools.downloadpageGzip(url)
	
	#logger.info(data)
	
	# Extrae el argumento
	patronvideos = '<div class="contenido">.*<p>([^<]+)<'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)
	plot = ""
	if len(matches)>0:
		plot=matches[0]

	# Extrae las entradas (capítulos)
	patronvideos  = '<div class="contenido-titulo">[^<]+'
	patronvideos += '<h2>Lista de Capitulos de [^<]+</h2>[^<]+'
	patronvideos += '</div>[^<]+'
	patronvideos += '<div class="contenido">(.*?)</div>'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)
	if len(matches)>0:
		data = matches[0]

	patronvideos = '<a href="([^"]+)"[^>]+>([^<]+)</a>'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	for match in matches:
		scrapedtitle = match[1]
		scrapedurl = urlparse.urljoin(url,match[0])
		scrapedthumbnail = thumbnail
		scrapedplot = plot
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELNAME , "detail2" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	patronvideos = "<a href='([^']+)' target='_blank'>([^<]+)</a>"
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	for match in matches:
		scrapedtitle = match[1]
		scrapedurl = urlparse.urljoin(url,match[0])
		scrapedthumbnail = thumbnail
		scrapedplot = plot
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		#xbmctools.addnewvideo( CHANNELNAME , "play" , category , "Directo" , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )
		xbmctools.addnewfolder( CHANNELNAME , "detail2" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# Extrae las entradas (capítulos)
	patronvideos = '<param name="flashvars" value="file=([^\&]+)&'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)
	if len(matches)>0:
		scrapedurl = matches[0]
		xbmctools.addnewvideo( CHANNELNAME , "playdirecto" , category , "Directo" , title , scrapedurl , thumbnail, plot )

	# Extrae las entradas (capítulos)
	'''
	patronvideos = '<div align="center"><a href="([^"]+)" target="_blank"><img src="([^"]+)" border="0">'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	for match in matches:
		# Titulo
		scrapedtitle = match[0]
		# URL
		scrapedurl = urlparse.urljoin(url,match[0])
		# Thumbnail
		scrapedthumbnail = urlparse.urljoin(url,match[1])
		# Argumento
		scrapedplot = ""

		# Depuracion
		if (DEBUG):
			logger.info("scrapedtitle="+scrapedtitle)
			logger.info("scrapedurl="+scrapedurl)
			logger.info("scrapedthumbnail="+scrapedthumbnail)

		# Añade al listado de XBMC
		xbmctools.addnewvideo( CHANNELNAME , "playmega" , category , "Megavideo" , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )
	'''

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def play(params,url,category):
	logger.info("[animeid.py] play")

	title = urllib.unquote_plus( params.get("title") )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = unicode( xbmc.getInfoLabel( "ListItem.Plot" ), "utf-8" )
	server = params["server"]

	scrapedurl = ""
	# Lee la página con el player
	data = scrapertools.downloadpageGzip(url)
	#logger.info(data)

	# Extrae las entradas (capítulos
	#patronvideos  = 'SWFObject\(\'http\:\/\/www\.SeriesID\.com\/player\.swf\'.*?\&file\=([^\&]+)&'
	patronvideos  = "so.addParam\('flashvars','\&file=([^\&]+)\&"
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	if len(matches)>0:
		scrapedurl = matches[0]
		server = "Directo"
	else:
		patronvideos  = '<param name="flashvars" value="file=([^\&]+)&'
		matches = re.compile(patronvideos,re.DOTALL).findall(data)
		if len(matches)>0:
			scrapedurl = matches[0]
			server= "Directo"
	xbmctools.playvideo(CHANNELNAME,server,scrapedurl,category,title,thumbnail,plot)

def playmega(params,url,category):
	logger.info("[animeid.py] play")

	title = urllib.unquote_plus( params.get("title") )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = unicode( xbmc.getInfoLabel( "ListItem.Plot" ), "utf-8" )
	server = params["server"]

	# Lee la página con el player
	logger.info("[animeid.py] url="+url)
	if url.startswith("http://www.animeid.com"):
		url = "http://animeid.com" + url[22:]
	logger.info("[animeid.py] url="+url)
	data = scrapertools.downloadpageGzip(url)
	#logger.info(data)

	# Extrae las entradas (videos)
	listavideos = servertools.findvideos(data)

	if len(listavideos)>0:
		video = listavideos[0]
		xbmctools.playvideo(CHANNELNAME,video[2],video[1],category,title,thumbnail,plot)

def playdirecto(params,url,category):
	logger.info("[animeid.py] playdirecto")

	title = urllib.unquote_plus( params.get("title") )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = unicode( xbmc.getInfoLabel( "ListItem.Plot" ), "utf-8" )
	server = params["server"]

	# Abre dialogo
	dialogWait = xbmcgui.DialogProgress()
	dialogWait.create( 'Accediendo al video...', title , plot )

	logger.info("url="+url)

	# Cierra dialogo
	dialogWait.close()
	del dialogWait

	xbmctools.playvideo(CHANNELNAME,server,url,category,title,thumbnail,plot)


def detail2(params,url,category):
	logger.info("[animeid.py] detail2")

	title = urllib.unquote_plus( params.get("title") )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot =  xbmc.getInfoLabel( "ListItem.Plot" )
	
	scrapedurl = ""
	# Lee la página con el player
	data = scrapertools.downloadpageGzip(url)
	#logger.info(data)
	
	patronvideos = 'file=([^\&]+)\&'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	if len(matches)>0:
		c= 0
		for match in matches:
			c += 1
			scrapedurl = match
			server = 'Directo'
		
			if (DEBUG): logger.info("title=["+title+"], url=["+scrapedurl+"], thumbnail=["+thumbnail+"]")
			xbmctools.addnewvideo( CHANNELNAME , "play2" , category , server , title + " - parte %d [%s]" %(c,server) , scrapedurl , thumbnail, plot )
	patronvideos = 'http://[^\.]+.megavideo.com[^\?]+\?v=([A-Z0-9a-z]{8})'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	if len(matches)>0:
		scrapedurl = matches[0]
		server = 'Megavideo'
		
		if (DEBUG): logger.info("title=["+title+"], url=["+scrapedurl+"], thumbnail=["+thumbnail+"]")
		xbmctools.addnewvideo( CHANNELNAME , "play2" , category , server , title + " - [%s]" %server , scrapedurl , thumbnail, plot )
		
	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def play2(params,url,category):
	logger.info("[animeid.py] play2")

	title = urllib.unquote_plus( params.get("title") )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = unicode( xbmc.getInfoLabel( "ListItem.Plot" ), "utf-8" )
	server = params["server"]

	xbmctools.playvideo(CHANNELNAME,server,url,category,title,thumbnail,plot)