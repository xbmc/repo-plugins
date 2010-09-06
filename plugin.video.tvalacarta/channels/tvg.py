# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# tvalacarta - XBMC Plugin
# Canal para TVG
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

try:
	pluginhandle = int( sys.argv[ 1 ] )
except:
	pluginhandle = ""

xbmc.output("[tvg.py] init")

DEBUG = True
CHANNELNAME = "TVG"
CHANNELCODE = "tvg"

def mainlist(params,url,category):
	xbmc.output("[tvg.py] mainlist")

	url = "http://www.crtvg.es/TVGacarta/"

	# --------------------------------------------------------
	# Descarga la página
	# --------------------------------------------------------
	data = scrapertools.cachePage(url)
	#xbmc.output(data)

	# --------------------------------------------------------
	# Extrae las categorias (carpetas)
	# --------------------------------------------------------
	patron = '<option>(.*?)\\n'
	matches = re.compile(patron,re.DOTALL).findall(data)
	if DEBUG:
		scrapertools.printMatches(matches)

	for match in matches:
		scrapedtitle = match.rstrip()
		if scrapedtitle.startswith("<I>"):
			scrapedtitle = scrapedtitle[3:-4]
		scrapedurl = "http://www.crtvg.es/tvgacarta/index.asp?tipo=" + scrapedtitle.replace(" ","+") + "&procura="
		scrapedthumbnail = ""
		scrapedplot = ""

		# Depuracion
		if (DEBUG):
			xbmc.output("scrapedtitle="+scrapedtitle)
			xbmc.output("scrapedurl="+scrapedurl)
			xbmc.output("scrapedthumbnail="+scrapedthumbnail)

		# Añade al listado de XBMC
		#addvideo( scrapedtitle , scrapedurl , category )
		xbmctools.addnewfolder( CHANNELCODE , "categorylist" , scrapedtitle , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )

	# Disable sorting...
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def categorylist(params,url,category):
	xbmc.output("[tvg.py] categorylist")

	# --------------------------------------------------------
	# Descarga la página
	# --------------------------------------------------------
	posturl = url[:39]
	postdata = url[40:]
	xbmc.output("posturl="+posturl)
	xbmc.output("postdata="+postdata)
	data = scrapertools.cachePagePost(posturl,postdata)
	#xbmc.output(data)

	# --------------------------------------------------------
	# Extrae las carpetas
	# --------------------------------------------------------
	patron = '<table align="center" id="prog_front">[^<]+<tr>[^<]+<th class="cab">[^<]+<strong>([^<]+)</strong>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	if DEBUG:
		scrapertools.printMatches(matches)

	for match in matches:
		scrapedtitle = match.rstrip()
		scrapedurl = "http://www.crtvg.es/tvgacarta/index.asp?tipo=" + category.replace(" ","+") + "&procura=" + match.replace(" ","+")
		scrapedthumbnail = ""
		scrapedplot = ""

		# Depuracion
		if (DEBUG):
			xbmc.output("scrapedtitle="+scrapedtitle)
			xbmc.output("scrapedurl="+scrapedurl)
			xbmc.output("scrapedthumbnail="+scrapedthumbnail)

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELCODE , "videolist" , scrapedtitle , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )

	# Disable sorting...
	#xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def videolist(params,url,category):
	xbmc.output("[tvg.py] videolist")

	# --------------------------------------------------------
	# Descarga la página
	# --------------------------------------------------------
	posturl = url[:39]
	postdata = url[40:]
	xbmc.output("posturl="+posturl)
	xbmc.output("postdata="+postdata)
	data = scrapertools.cachePagePost(posturl,postdata)
	#xbmc.output(data)

	# --------------------------------------------------------
	# Extrae los videos
	# --------------------------------------------------------
	patron = '[^<]+<table class="video" onmouseover="[^"]+" onmouseout="[^"]+" onclick="javascript:AbreReproductor\(\'([^\']+)\'[^"]+" >[^<]+<tr>[^<]+<td rowspan="2" class="foto"><img src="([^"]+)"></td>[^<]+<td class="texto">(.*?)</td>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	if DEBUG:
		scrapertools.printMatches(matches)

	for match in matches:
		patron2 = "programa=([^&]+)&"
		matches2 = re.compile(patron2,re.DOTALL).findall(match[0])
		scrapedtitle = matches2[0]

		patron2 = "fecha=([^&]+)&"
		matches2 = re.compile(patron2,re.DOTALL).findall(match[0])
		scrapedtitle = scrapedtitle + " (" + matches2[0] + ")"

		scrapedurl = "http://www.crtvg.es" + match[0].replace("&amp;","&").replace(" ","%20")
		scrapedthumbnail = "http://www.crtvg.es"+match[1]
		scrapedplot = match[2]

		# Depuracion
		if (DEBUG):
			xbmc.output("scrapedtitle="+scrapedtitle)
			xbmc.output("scrapedurl="+scrapedurl)
			xbmc.output("scrapedthumbnail="+scrapedthumbnail)

		# Añade al listado de XBMC
		xbmctools.addnewvideo( CHANNELCODE , "play" , CHANNELNAME , "" , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )

	# Disable sorting...
	#xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def play(params,url,category):
	xbmc.output("[tvg.py] play")

	title = urllib.unquote_plus( params.get("title") )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = urllib.unquote_plus( params.get("plot") )
	xbmc.output("[tvg.py] thumbnail="+thumbnail)

	# Abre dialogo
	dialogWait = xbmcgui.DialogProgress()
	dialogWait.create( 'Descargando datos del vídeo...', title )

	# --------------------------------------------------------
	# Descarga pagina detalle
	# --------------------------------------------------------
	xbmc.output("[tvg.py] descarga "+url)
	data = scrapertools.cachePage(url)

	# Primer frame
	#<frame src="laterali.asp?canal=tele&amp;arquivo=1&amp;Programa=ALALÁ&amp;hora=09/02/2009 21:35:16&amp;fecha=03/02/2009&amp;id_Programa=7" name="pantalla" frameborder="0" scrolling="NO" noresize>
	patron = '<frame src="(laterali.asp[^"]+)"'
	matches = re.compile(patron,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	url = matches[0].replace("&amp;","&")
	url = url.replace(" ","%20")
	url = "http://www.crtvg.es/reproductor/"+url

	# Segundo frame
	#<frame src="ipantalla.asp?canal=tele&amp;arquivo=1&amp;Programa=ALALÁ&amp;hora=09/02/2009 21:35:16&amp;fecha=03/02/2009&amp;opcion=pantalla&amp;id_Programa=7" name="pantalla" frameborder="0" scrolling="NO" noresize>
	xbmc.output("[tvg.py] descarga "+url)
	data = scrapertools.cachePage(url)
	patron = '<frame src="(ipantalla.asp[^"]+)"'
	matches = re.compile(patron,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	url = matches[0].replace("&amp;","&")
	url = url.replace(" ","%20")
	url = "http://www.crtvg.es/reproductor/"+url

	# Video
	#<param name='url' value='http://www.crtvg.es/asfroot/acarta_tvg/ALALA_20090203.asx' />
	#<PARAM NAME="URL" value="http://www.crtvg.es/asfroot/acarta_tvg/ALALA_20090203.asx" />
	xbmc.output("[tvg.py] descarga "+url)
	data = scrapertools.cachePage(url)
	patron = '<PARAM NAME="URL" value="([^"]+)"'
	matches = re.compile(patron,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	if len(matches) == 0:
		logFile.info("probando e.r. alternativa")
		patron = "<param name='url' value='([^']+)'"
		matches = re.compile(patron,re.DOTALL).findall(data)
		scrapertools.printMatches(matches)
	url = matches[0]
	
	#<ASX VERSION="3.0"><TITLE>Televisi¾n de Galicia - ALAL-</TITLE><ENTRY><REF HREF="mms://media2.crtvg.es/videos_f/0007/0007_20090203.wmv"/><STARTTIME VALUE="0:00:00" />
	xbmc.output("[tvg.py] descarga "+url)
	data = scrapertools.cachePage(url)
	patron = 'HREF="([^"]+)"'
	matches = re.compile(patron,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	url = matches[0]
	xbmc.output("url="+url)

	# Playlist vacia
	playlist = xbmc.PlayList( xbmc.PLAYLIST_VIDEO )
	playlist.clear()

	# Crea la entrada y la añade al playlist
	listitem = xbmcgui.ListItem( title, iconImage="DefaultVideo.png", thumbnailImage=thumbnail )
	listitem.setInfo( "video", { "Title": title, "Plot" : plot , "Studio" : CHANNELNAME , "Genre" : category } )
	playlist.add( url, listitem )

	# Cierra dialogo
	dialogWait.close()
	del dialogWait

	# Reproduce
	xbmcPlayer = xbmc.Player( xbmc.PLAYER_CORE_MPLAYER )
	xbmcPlayer.play(playlist)   
