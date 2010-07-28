# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para cine15
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

CHANNELNAME = "cine15"

# Esto permite su ejecución en modo emulado
try:
	pluginhandle = int( sys.argv[ 1 ] )
except:
	pluginhandle = ""

# Traza el inicio del canal
logger.info("[cine15.py] init")

DEBUG = True

def mainlist(params,url,category):
	logger.info("[cine15.py] mainlist")

	# Añade al listado de XBMC
	xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , "Películas - Novedades"            ,"http://www.cine15.com/","","")
	xbmctools.addnewfolder( CHANNELNAME , "peliscat"   , category , "Películas - Lista por categorías" ,"http://www.cine15.com/","","")
	xbmctools.addnewfolder( CHANNELNAME , "search"     , category , "Buscar"                           ,"","","")

	if config.getSetting("singlechannel")=="true":
		xbmctools.addSingleChannelOptions(params,url,category)

	# Propiedades
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def search(params,url,category):
	logger.info("[cine15.py] search")

	keyboard = xbmc.Keyboard('')
	keyboard.doModal()
	if (keyboard.isConfirmed()):
		tecleado = keyboard.getText()
		if len(tecleado)>0:
			#convert to HTML
			tecleado = tecleado.replace(" ", "+")
			searchUrl = "http://www.cine15.com/?s="+tecleado+"&x=0&y=0"
			listvideos(params,searchUrl,category)

def performsearch(texto):
	logger.info("[cine15.py] performsearch")
	url = "http://www.cine15.com/?s="+texto+"&x=0&y=0"

	# Descarga la página
	data = scrapertools.cachePage(url)

	# Extrae las entradas (carpetas)
	patronvideos  = '<div class="videoitem">[^<]+'
	patronvideos += '<div class="ratings">[^<]+'
	patronvideos += '<div id="post-ratings[^>]+><img[^>]+><img[^>]+><img[^>]+><img[^>]+><img[^>]+></div>[^<]+'
	patronvideos += '<div id="post-ratings[^>]+><img[^>]+>&nbsp;Loading ...</div>[^<]+'
	patronvideos += '</div>[^<]+'
	patronvideos += '<div class="comments">[^<]+</div>[^<]+'
	patronvideos += '<div class="thumbnail">[^<]+'
	patronvideos += '<a href="([^"]+)" title="([^"]+)"><img style="background: url\(([^\)]+)\)" [^>]+></a>[^<]+'
	patronvideos += '</div>[^<]+'
	patronvideos += '<h2 class="itemtitle"><a[^>]+>[^<]+</a></h2>[^<]+'
	patronvideos += '<p class="itemdesc">([^<]+)</p>[^<]+'
	patronvideos += '<small class="gallerydate">([^<]+)</small>'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	resultados = []

	for match in matches:
		scrapedtitle = match[1]
		scrapedurl = urlparse.urljoin(url,match[0])
		scrapedthumbnail = urlparse.urljoin(url,match[2])
		scrapedplot = match[3]

		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		resultados.append( [CHANNELNAME , "detail" , "buscador" , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot ] )
		
	return resultados

def peliscat(params,url,category):
	logger.info("[cine15.py] peliscat")

	# Descarga la página
	data = scrapertools.cachePage(url)

	# Extrae las entradas (carpetas)
	patronvideos  = '<li class="cat-item cat-item[^"]+"><a href="([^"]+)" title="[^"]+">([^<]+)</a>'
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

	# Propiedades
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def listvideos(params,url,category):
	logger.info("[cine15.py] listvideos")

	# Descarga la página
	data = scrapertools.cachePage(url)
	#logger.info(data)

	# Extrae las entradas (carpetas)
	'''
	<div class="thumbnail-div">
	<a href="http://www.cine15.com/peliculas/accion/zombieland/" title="Zombieland">  <img src="http://www.cine15.com/wp-content/themes/cine2.00/timthumb.php?src=http://www.cine15.com/wp-content/uploads/2010/05/x14z.jpg&amp;h=225&amp;w=141&amp;q=80&amp;zc=1" alt=""  style="border: none;" />   </a>
	<div  id="play">
	<ul class="playimg">
	<li><a href="http://www.cine15.com/peliculas/accion/zombieland/" class="boton"  ></a></li>
	</ul></div>
	<div class="post-info2">
	<h2><a href="http://www.cine15.com/peliculas/accion/zombieland/" class="post-info-title" title="Permanent Link to Zombieland">
	Zombieland...                        </a></h2>
	<p class="itemdesc">TÍTULO ORIGINAL:  Zombieland
	AÑO: 2009 	Ver trailer externo
	DURACIÓN: ...</p>
	'''
	patronvideos  = '<div class="thumbnail-div">[^<]+'
	patronvideos += '<a href="([^"]+)" title="([^"]+)">  <img src="([^"]+)"'
	
	matches = re.compile(patronvideos,re.DOTALL).findall(data)

	scrapertools.printMatches(matches)

	for match in matches:
		scrapedtitle = match[1]
		scrapedurl = urlparse.urljoin(url,match[0])
		scrapedthumbnail = urlparse.urljoin(url,match[2])
		scrapedplot = ""
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELNAME , "detail" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# Extrae la marca de siguiente página
	patronvideos = "<span class='current'>[^<]+</span><a href='([^']+)' class='page'>"
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	if len(matches)>0:
		scrapedtitle = "Página siguiente"
		scrapedurl = urlparse.urljoin(url,matches[0])
		scrapedthumbnail = ""
		scrapedplot = ""
		xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# Propiedades
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def detail(params,url,category):
	logger.info("[cine15.py] detail")

	title = urllib.unquote_plus( params.get("title") )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = urllib.unquote_plus( params.get("plot") )

	# Descarga la página
	data = scrapertools.cachePage(url)
	#logger.info(data)

	# ------------------------------------------------------------------------------------
	# Busca los enlaces a videos no megavideo (playlist xml)
	# ------------------------------------------------------------------------------------
	patronvideos  = 'flashvars[^f]+file=([^\&]+)\&amp'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)
	
	if len(matches)>0:
		if ("xml" in matches[0]):
			data2 = scrapertools.cachePage(matches[0])
			logger.info("data2="+data2)
			patronvideos  = '<track>[^<]+'
			patronvideos += '<title>([^<]+)</title>[^<]+'
			patronvideos += '<location>([^<]+)</location>[^<]+'
			patronvideos += '</track>'
			matches = re.compile(patronvideos,re.DOTALL).findall(data2)
			scrapertools.printMatches(matches)

			for match in matches:
				scrapedtitle = match[0]
				scrapedurl = match[1].strip()
				scrapedthumbnail = thumbnail
				scrapedplot = plot
				if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

				# Añade al listado de XBMC
				xbmctools.addnewvideo( CHANNELNAME , "play" , category , "Directo" , scrapedtitle + " [Directo]", scrapedurl , scrapedthumbnail, scrapedplot )
		else:
			# Añade al listado de XBMC
			xbmctools.addnewvideo( CHANNELNAME , "play" , category , "Directo" , title + " [Directo]", matches[0] , thumbnail, plot )
			
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

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
		
	# Disable sorting...
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def play(params,url,category):
	logger.info("[cine15.py] play")

	title = unicode( xbmc.getInfoLabel( "ListItem.Title" ), "utf-8" )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = unicode( xbmc.getInfoLabel( "ListItem.Plot" ), "utf-8" )
	server = params["server"]
	
	xbmctools.playvideo(CHANNELNAME,server,url,category,title,thumbnail,plot)
