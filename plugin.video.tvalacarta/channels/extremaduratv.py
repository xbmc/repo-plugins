# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# tvalacarta - XBMC Plugin
# Canal para Extremadura TV
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

logger.info("[extremaduratv.py] init")

DEBUG = True
CHANNELNAME = "Extremadura TV"
CHANNELCODE = "extremaduratv"

def mainlist(params,url,category):
	logger.info("[extremaduratv.py] channel")

	# Anade al listado de XBMC
	xbmctools.addnewfolder( CHANNELCODE , "categorias" , CHANNELNAME , "Por categorías" , "http://extremaduratv.canalextremadura.es/tv-a-la-carta" , "" , "" )
	xbmctools.addnewfolder( CHANNELCODE , "programas"  , CHANNELNAME , "Por programas"  , "http://extremaduratv.canalextremadura.es/tv-a-la-carta" , "" , "" )

	# Cierra el directorio
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def categorias(params,url,category):
	logger.info("[extremaduratv.py] categorias")

	# --------------------------------------------------------
	# Descarga la página
	# --------------------------------------------------------
	data = scrapertools.cachePage(url)
	#logger.info(data)

	# --------------------------------------------------------
	# Extrae los programas
	# --------------------------------------------------------
	patron = '<select name="categoria"(.*?)</select>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	data = matches[0]
	patron = '<option value="(\d+)">([^<]+)</option>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	if DEBUG: scrapertools.printMatches(matches)

	for match in matches:
		scrapedtitle = match[1]
		try:
			scrapedtitle = unicode( scrapedtitle, "utf-8" ).encode("iso-8859-1")
		except:
			pass
		scrapedurl = "http://extremaduratv.canalextremadura.es/search/videos/programa%3A" + match[0] + "+categoria%3A0"
		scrapedthumbnail = ""
		scrapedplot = ""
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELCODE , "videolist" , CHANNELNAME , scrapedtitle , scrapedurl , scrapedthumbnail , scrapedplot )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def programas(params,url,category):
	logger.info("[extremaduratv.py] programas")

	# --------------------------------------------------------
	# Descarga la página
	# --------------------------------------------------------
	data = scrapertools.cachePage(url)
	#logger.info(data)

	# --------------------------------------------------------
	# Extrae los programas
	# --------------------------------------------------------
	patron = ' <select name="programa"(.*?)</select>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	data = matches[0]
	patron = '<option value="(\d+)">([^<]+)</option>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	if DEBUG: scrapertools.printMatches(matches)

	for match in matches:
		scrapedtitle = match[1]
		try:
			scrapedtitle = unicode( scrapedtitle, "utf-8" ).encode("iso-8859-1")
		except:
			pass
		scrapedurl = "http://extremaduratv.canalextremadura.es/search/videos/programa%3A" + match[0] + "+categoria%3A0"
		scrapedthumbnail = ""
		scrapedplot = ""
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELCODE , "videolist" , CHANNELNAME , scrapedtitle , scrapedurl , scrapedthumbnail , scrapedplot )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def videolist(params,url,category):
	logger.info("[extremaduratv.py] videolist")

	# --------------------------------------------------------
	# Descarga la página
	# --------------------------------------------------------
	data = scrapertools.cachePage(url)
	#logger.info(data)

	# --------------------------------------------------------
	# Extrae los programas
	# --------------------------------------------------------
	patron  = '<div class="item_busqueda">\W*<div class="foto">\W*<img src="([^"]+)" alt="" title=""\W*/>\W*</div>\W*<div class="datos">\W*<div class="titulo"><a href="([^"]+)">(.*?)</a>.*?-->(.*?)</div>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	if DEBUG:
		scrapertools.printMatches(matches)

	for match in matches:
		# Datos
		#'<span class="color_1">extremadura</span><span class="miniespacio"> </span><span class="color_2">desde</span><span class="miniespacio"> </span><span class="color_3">el</span><span class="miniespacio"> </span><span class="color_1">aire:</span><span class="miniespacio"> </span><span class="color_2">llega</span><span class="miniespacio"> </span><span class="color_1">aire</span><span class="miniespacio"> </span><span class="color_3">con</span><span class="miniespacio"> </span><span class="color_1">olores</span><span class="miniespacio"> </span><span class="color_2">portugueses</span><span class="miniespacio"> </span>'
		#'extremadura desde el aire: llega aire con olores portugueses '
		scrapedtitle = match[2]
		scrapedtitle = scrapedtitle.replace('<span class="color_1">','')
		scrapedtitle = scrapedtitle.replace('<span class="color_2">','')
		scrapedtitle = scrapedtitle.replace('<span class="color_3">','')
		scrapedtitle = scrapedtitle.replace('</span>','')
		scrapedtitle = scrapedtitle.replace('<span class="miniespacio">','')
		scrapedurl = "http://tv.canalextremadura.es%s" % match[1]
		scrapedurl = scrapedurl.replace("#","%")
		scrapedthumbnail = match[0].replace(" ","%20")
		#'\n\t  \n\t\tApenas\xc2\xa0 30 kil\xc3\xb3metros en l\xc3\xadnea recta separan la...\t\t\n\t\t<div>\n\t\td\xc3\xada de emisi\xc3\xb3n_<span class="date-display-single">11Mayo09</span>\t\t')
		#Apenas\xc2\xa0 30 kil\xc3\xb3metros en l\xc3\xadnea recta separan la...\t\t\n\t\t<div>\n\t\td\xc3\xada de emisi\xc3\xb3n_<span class="date-display-single">11Mayo09</span>')
		scrapedplot = match[3].strip()

		# Depuracion
		if (DEBUG):
			logger.info("scrapedtitle="+scrapedtitle)
			logger.info("scrapedurl="+scrapedurl)
			logger.info("scrapedthumbnail="+scrapedthumbnail)

		# Añade al listado de XBMC
		#addvideo( scrapedtitle , scrapedurl , category )
		xbmctools.addnewvideo( CHANNELCODE , "play" , CHANNELNAME , "" , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def play(params,url,category):
	logger.info("[extremaduratv.py] play")

	title = urllib.unquote_plus( params.get("title") )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = urllib.unquote_plus( params.get("plot") )
	logger.info("[extremaduratv.py] thumbnail="+thumbnail)

	# Abre dialogo
	dialogWait = xbmcgui.DialogProgress()
	dialogWait.create( 'Descargando datos del vídeo...', title )

	# --------------------------------------------------------
	# Descarga pagina detalle
	# --------------------------------------------------------
	data = scrapertools.cachePage(url)
	patron = 'fluURL\: "([^"]+)"'
	matches = re.compile(patron,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)
	try:
		url = matches[0].replace(' ','%20')
	except:
		url = ""
	logger.info("[extremaduratv.py] play url="+url)
	
	# Construye un plot más completo
	matches = re.compile("<div class=\"view-field view-data-title\">([^<]+)<",re.DOTALL).findall(data)
	descripcion1 = matches[0]
	matches = re.compile("<div class=\"view-field view-data-body\">([^<]+)<",re.DOTALL).findall(data)
	descripcion2 = matches[0]
	matches = re.compile("<div class=\"view-field view-data-created\">([^<]+)<",re.DOTALL).findall(data)
	descripcion3 = matches[0]
	matches = re.compile("<div class=\"view-field view-data-duracion\">([^<]+)<",re.DOTALL).findall(data)
	descripcion4 = matches[0]
	descripcioncompleta = descripcion1[0].strip() + " " + descripcion2[0].strip() + " " + descripcion3[0].strip() + " " + descripcion4[0].strip()
	descripcioncompleta = descripcioncompleta.replace("\t","");
	descripcioncompleta = unicode( descripcioncompleta, "utf-8" ).encode("iso-8859-1")
	plot = descripcioncompleta

	# Playlist vacia
	playlist = xbmc.PlayList( xbmc.PLAYLIST_VIDEO )
	playlist.clear()

	# Crea la entrada y la añade al playlist
	listitem = xbmcgui.ListItem( title, iconImage="DefaultVideo.png", thumbnailImage=thumbnail )
	listitem.setInfo( "video", { "Title": title, "Plot" : plot , "Studio" : CHANNELNAME , "Genre" : category } )
	playlist.add( url, listitem )
	#xbmc.Player(xbmc.PLAYER_CORE_DVDPLAYER).play("rtmp://aialanetfs.fplive.net/aialanet?slist=Jardineria/palmera-roebelen.flv", nuevoitem)

	# Cierra dialogo
	dialogWait.close()
	del dialogWait

	# Reproduce
	xbmcPlayer = xbmc.Player( xbmc.PLAYER_CORE_AUTO )
	xbmcPlayer.play(playlist)   
