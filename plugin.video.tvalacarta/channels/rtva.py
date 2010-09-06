# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# tvalacarta - XBMC Plugin
# Canal para RTVA
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

logger.info("[rtva.py] init")

DEBUG = False
CHANNELNAME = "Andalucia TV"
CHANNELCODE = "rtva"

def mainlist(params,url,category):
	logger.info("[rtva.py] mainlist")

	url = "http://www.radiotelevisionandalucia.es/tvcarta/impe/web/portada"

	# --------------------------------------------------------
	# Descarga la página
	# --------------------------------------------------------
	data = scrapertools.cachePage(url)
	#logger.info(data)

	# --------------------------------------------------------
	# Extrae los programas
	# --------------------------------------------------------
	patron = '<div class="infoPrograma"><h3 class="h3TituloProgramaCarta"><a href="([^"]+)" title="[^"]+">([^<]+)</a></h3><p>([^<]+)</p>(?:<p>([^<]+)</p>)?(?:<p>([^<]+)</p>)?(?:<p>([^<]+)</p>)?</div><div class="enlacePrograma"><a href="[^"]+" title="[^"]+"><img class="imgLista" src="([^"]+)"'
	matches = re.compile(patron,re.DOTALL).findall(data)
	if DEBUG:
		scrapertools.printMatches(matches)

	dictionaryurl = {}

	for match in matches:
		titulo = match[1].replace("á","Á")
		titulo = titulo.replace("é","É")
		titulo = titulo.replace("í","Í")
		titulo = titulo.replace("ó","Ó")
		titulo = titulo.replace("ú","Ú")
		titulo = titulo.replace("ñ","Ñ")
		titulo = titulo.replace('&Aacute;','Á')
		titulo = titulo.replace('&Eacute;','É')
		titulo = titulo.replace('&Iacute;','Í')
		titulo = titulo.replace('&Oacute;','Ó')
		titulo = titulo.replace('&Uacute;','Ú')
		titulo = titulo.replace('&ntilde;','ñ')
		titulo = titulo.replace('&Ntilde;','Ñ')
		scrapedtitle = titulo
		scrapedurl = 'http://www.radiotelevisionandalucia.es/tvcarta/impe/web/portada'
		scrapedthumbnail = ""
		scrapedplot = ""

		# Depuracion
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		#addfolder( scrapedtitle , scrapedurl , "videolist" )
		if dictionaryurl.has_key(scrapedtitle):
			if DEBUG: logger.info("%s ya existe" % scrapedtitle)
		else:
			xbmctools.addnewfolder( CHANNELCODE , "videolist" , CHANNELNAME , scrapedtitle , scrapedurl , scrapedthumbnail , scrapedplot )
			dictionaryurl[scrapedtitle] = True

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	#xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_TITLE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def videolist(params,url,category):
	logger.info("[rtva.py] videolist")

	title = urllib.unquote_plus( params.get("title") )

	# --------------------------------------------------------
	# Descarga la página
	# --------------------------------------------------------
	data = scrapertools.cachePage(url)
	#logger.info(data)

	# --------------------------------------------------------
	# Extrae los programas
	# --------------------------------------------------------
	patron  = '<div class="infoPrograma"><h3 class="h3TituloProgramaCarta"><a href="([^"]+)" title="[^"]+">([^<]+)</a></h3><p>([^<]+)</p>(?:<p>([^<]+)</p>)?(?:<p>([^<]+)</p>)?(?:<p>([^<]+)</p>)?</div><div class="enlacePrograma"><a href="[^"]+" title="[^"]+"><img class="imgLista" src="([^"]+)"'
	matches = re.compile(patron,re.DOTALL).findall(data)
	if DEBUG:
		scrapertools.printMatches(matches)

	for match in matches:
		# Datos
		titulo = match[1].replace("á","Á")
		titulo = titulo.replace("é","É")
		titulo = titulo.replace("í","Í")
		titulo = titulo.replace("ó","Ó")
		titulo = titulo.replace("ú","Ú")
		titulo = titulo.replace("ñ","Ñ")
		titulo = titulo.replace('&Aacute;','Á')
		titulo = titulo.replace('&Eacute;','É')
		titulo = titulo.replace('&Iacute;','Í')
		titulo = titulo.replace('&Oacute;','Ó')
		titulo = titulo.replace('&Uacute;','Ú')
		titulo = titulo.replace('&ntilde;','ñ')
		titulo = titulo.replace('&Ntilde;','Ñ')
		scrapedtitle = titulo
		scrapedurl = urlparse.urljoin(url, match[0])
		scrapedthumbnail = match[6].replace(' ','%20')
		titulocapitulo =  ( "%s %s %s %s" % (match[2],match[3],match[4],match[5]))
		titulocapitulo = titulocapitulo.replace('&Aacute;','Á')
		titulocapitulo = titulocapitulo.replace('&Eacute;','É')
		titulocapitulo = titulocapitulo.replace('&Iacute;','Í')
		titulocapitulo = titulocapitulo.replace('&Oacute;','Ó')
		titulocapitulo = titulocapitulo.replace('&Uacute;','Ú')
		titulocapitulo = titulocapitulo.replace('&ntilde;','ñ')
		titulocapitulo = titulocapitulo.replace('&Ntilde;','Ñ')
		titulocapitulo = titulocapitulo.replace('&aacute;','á')
		titulocapitulo = titulocapitulo.replace('&eacute;','é')
		titulocapitulo = titulocapitulo.replace('&iacute;','í')
		titulocapitulo = titulocapitulo.replace('&oacute;','ó')
		titulocapitulo = titulocapitulo.replace('&uacute;','ú')
		scrapedplot = titulocapitulo

		# Depuracion
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		if scrapedtitle == title:
			xbmctools.addnewvideo( CHANNELCODE , "play" , CHANNELNAME , "" , scrapedtitle + " " + scrapedplot , scrapedurl , scrapedthumbnail, scrapedplot )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	#xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def play(params,url,category):
	logger.info("[rtva.py] play")

	title = urllib.unquote_plus( params.get("title") )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = urllib.unquote_plus( params.get("plot") )
	logger.info("[rtva.py] thumbnail="+thumbnail)

	# Abre dialogo
	dialogWait = xbmcgui.DialogProgress()
	dialogWait.create( 'Descargando datos del vídeo...', title )

	# --------------------------------------------------------
	# Descarga pagina detalle
	# --------------------------------------------------------
	data = scrapertools.cachePage(url)
	patron = '<param name="flashvars" value="&amp;video=(http://[^"]+)"'
	matches = re.compile(patron,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)
	try:
		url = matches[0].replace(' ','%20')
	except:
		url = ""
	logger.info("[rtva.py] url="+url)
	if url.find("&") != -1:
		url = url.split("&")[0]
		logger.info("[rtva.py] url="+url)

	# --------------------------------------------------------
	# Argumento detallado
	# --------------------------------------------------------
	patron = '<div class="zonaContenido"><p>([^<]+)</p>(?:<p>([^<]+)</p>)?(?:<p>([^<]+)</p>)?(?:<p>([^<]+)</p>)?</div>'
	argumento = re.compile(patron,re.DOTALL).findall(data)
	scrapertools.printMatches(argumento)
	argumentofull = ""
	if len(argumento) > 0:
		if len(argumento[0]) >= 4:
			argumentofull = ("%s\n%s\n%s\n%s\n%s" % (title , argumento[0][0] , argumento[0][1] , argumento[0][2] , argumento[0][3] ))
		elif len(argumento[0]) >= 3:
			argumentofull = ("%s\n%s\n%s\n%s" % (title , argumento[0][0] , argumento[0][1] , argumento[0][2] ))
		elif len(argumento[0]) >= 2:
			argumentofull = ("%s\n%s\n%s" % (title , argumento[0][0] , argumento[0][1] ))
		elif len(argumento[0]) >= 1:
			argumentofull = ("%s\n%s" % (title , argumento[0][0] ))
	#argumentofull = ("%s\n%s" % (item.description , argumento[0][0] ))
	argumentofull = argumentofull.replace('&Aacute;','Á')
	argumentofull = argumentofull.replace('&Eacute;','É')
	argumentofull = argumentofull.replace('&Iacute;','Í')
	argumentofull = argumentofull.replace('&Oacute;','Ó')
	argumentofull = argumentofull.replace('&Uacute;','Ú')
	argumentofull = argumentofull.replace('&aacute;','á')
	argumentofull = argumentofull.replace('&eacute;','é')
	argumentofull = argumentofull.replace('&iacute;','í')
	argumentofull = argumentofull.replace('&oacute;','ó')
	argumentofull = argumentofull.replace('&uacute;','ú')
	argumentofull = argumentofull.replace('&ntilde;','ñ')
	argumentofull = argumentofull.replace('&Ntilde;','Ñ')
	plot = argumentofull

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
