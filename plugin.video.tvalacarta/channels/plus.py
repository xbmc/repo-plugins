# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# tvalacarta - XBMC Plugin
# Canal para Plus TV
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

xbmc.output("[plus.py] init")

DEBUG = True
CHANNELNAME = "Plus TV"
CHANNELCODE = "plus"

def mainlist(params,url,category):
	xbmc.output("[plus.py] mainlist")

	url = "http://www.plus.es/tv/canales.html"

	# --------------------------------------------------------
	# Descarga la página
	# --------------------------------------------------------
	data = scrapertools.cachePage(url)
	#xbmc.output(data)

	# --------------------------------------------------------
	# Extrae los programas
	# --------------------------------------------------------
	'''
	<li class="canales estirar">
	<h2><a href="index.html?idlist=PLTVCN">Cine </a></h2>
	<a href="index.html?idlist=PLTVCN"><img alt="imagen Cine " src="/images/plustv/categorias/PLTVCN.jpg"/></a>
	<ul>
		<li><span><a title="Taller Canal+: Jaume Balagueró y Paco Plaza" href="index.html?idlist=PLTVCN&amp;idvid=834262&amp;pos=0">Taller Canal+: Jaume Balagueró y Paco Plaza</a></span></li><li><span><a title="Canal+ en Hollywood: globos de oro 2009" href="index.html?idlist=PLTVCN&amp;idvid=817622&amp;pos=1">Canal+ en Hollywood: globos de oro 2009</a></span></li>
		<li class="sinPlay"><a title="ver mas" href="emisiones.html?id=PLTVCN">Más ...</a></li>
	</ul>
	'''
	patron  = '<li class="canales estirar[^"]*">[^<]+'
	patron += '<h2><a href="([^"]+)">([^<]+)</a></h2>[^<]+'
	patron += '<a href="[^"]+"><img alt="[^"]+" src="([^"]+)"/></a>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	if DEBUG: scrapertools.printMatches(matches)

	for match in matches:
		scrapedtitle = match[1]
		try:
			scrapedtitle = unicode( scrapedtitle, "utf-8" ).encode("iso-8859-1")
		except:
			pass
		scrapedurl = urlparse.urljoin( url, match[0]).replace("index.html?idlist","emisiones.html?id")
		scrapedthumbnail = urlparse.urljoin(url,match[2])
		scrapedplot = ""
		if (DEBUG): xbmc.output("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		#addfolder( scrapedtitle , scrapedurl , "videolist" )
		xbmctools.addnewfolder( CHANNELCODE , "videolist" , CHANNELNAME , scrapedtitle , scrapedurl , scrapedthumbnail , scrapedplot )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )

	# Disable sorting...
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def videolist(params,url,category):
	xbmc.output("[plus.py] videolist")

	# --------------------------------------------------------
	# Descarga la página
	# --------------------------------------------------------
	data = scrapertools.cachePage(url)
	#xbmc.output(data)

	# --------------------------------------------------------
	# Extrae los vídeos de la página
	# --------------------------------------------------------
	'''
	<li class="video estirar">
	<div class="imagen">
		<a title="Estrellas de Canal+: Heath Ledger" href="index.html?idlist=PLTVCN&amp;idvid=537147&amp;pos=3">
			<img alt="" src="http://www.plus.es/plustv/images/fotogramas/plustv/PO805296.jpg">
			<span>Play</span>
		</a>
	</div>
	<div class="tooltip" title="Programa que repasa la trayectoria de las caras más conocidas del cine.">
		<div class="textos">

			<p class="titulo"><a href="index.html?idlist=PLTVCN&amp;idvid=537147&amp;pos=3">Estrellas de Canal+: Heath Ledger</a></p>
		</div>
		<a class="addmiplustv show" href="miplustv.html?id=537147&amp;action=add" rel="nofollow">Añadir a Mi PLUSTV</a>
		<span>Añadido a Mi PlusTV</span>
	</div>
	</li>
	'''
	patron  = '<li class="video estirar">[^<]+'
	patron += '<div class="imagen">[^<]+'
	patron += '<a title="([^"]+)" href="([^"]+)">[^<]+'
	patron += '<img alt="[^"]*" src="([^"]+)">.*?'
	patron += '<div class="tooltip" title="([^"]+)"'
	matches = re.compile(patron,re.DOTALL).findall(data)
	if DEBUG: scrapertools.printMatches(matches)

	for match in matches:
		# Datos
		scrapedtitle = match[0]
		scrapedurl = urlparse.urljoin( url , match[1] )
		scrapedthumbnail = urlparse.urljoin( url , match[2] )
		scrapedplot = match[3]
		if (DEBUG): xbmc.output("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		#addvideo( scrapedtitle , scrapedurl , category )
		xbmctools.addnewvideo( CHANNELCODE , "play" , CHANNELNAME , "" , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# --------------------------------------------------------
	# Extrae el enlace a la siguiente página
	# --------------------------------------------------------
	patron = '<li class="siguiente"><a href="([^"]+)">siguiente \&gt\;</a></li>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	if DEBUG: scrapertools.printMatches(matches)

	for match in matches:
		# Datos
		scrapedtitle = "Página siguiente"
		scrapedurl = "http://www.plus.es/plustv/emisiones.html"+match
		scrapedthumbnail = ""
		scrapedplot = ""
		if (DEBUG): xbmc.output("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		#addvideo( scrapedtitle , scrapedurl , category )
		xbmctools.addnewfolder( CHANNELCODE , "videolist" , CHANNELNAME , scrapedtitle , scrapedurl , scrapedthumbnail , scrapedplot )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )

	# Disable sorting...
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def play(params,url,category):
	xbmc.output("[plus.py] play")

	title = urllib.unquote_plus( params.get("title") )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = urllib.unquote_plus( params.get("plot") )
	xbmc.output("[plus.py] thumbnail="+thumbnail)

	# Abre dialogo
	dialogWait = xbmcgui.DialogProgress()
	dialogWait.create( 'Descargando datos del vídeo...', title )

	# --------------------------------------------------------
	# Descarga pagina detalle
	# --------------------------------------------------------
	# Averigua la URL
	# URL Detalle: http://www.plus.es/tv/index.html?idList=PLTVDO&amp;idVid=725903&amp;pos=0
	# URL XML vídeo: http://www.plus.es/tv/bloques.html?id=0&idList=PLTVDO&idVid=725903
	#<?xml version="1.0" encoding="iso-8859-1"?>
	#<bloque modo="U">
	#<video tipo="P" url="http://canalplus.ondemand.flumotion.com/canalplus/ondemand/plustv/GF755806.flv" title=""></video>
	#<video tipo="T" url="http://canalplus.ondemand.flumotion.com/canalplus/ondemand/plustv/NF754356.flv" title="Encuentros en el fin del mundo"></video>
	#</bloque>
	idCategoria = re.compile("idlist=([^&]+)&",re.DOTALL).findall(url)
	xbmc.output('idCategoria='+idCategoria[0])
	idVideo = re.compile("idvid=(\d+)",re.DOTALL).findall(url)
	xbmc.output('idVideo='+idVideo[0])
	urldetalle = "http://www.plus.es/tv/bloques.html?id=0&idList=" + idCategoria[0] + "&idVid=" + idVideo[0]
	bodydetalle = scrapertools.cachePage(urldetalle)
	xbmc.output(bodydetalle)
	enlacevideo = re.compile('<video tipo="T" url="([^"]+)"',re.DOTALL).findall(bodydetalle)
	xbmc.output("enlacevideo="+enlacevideo[0])
	#enlacevideo = 
	url = enlacevideo[0]
	
	# Playlist vacia
	playlist = xbmc.PlayList( xbmc.PLAYLIST_VIDEO )
	playlist.clear()

	# Crea la entrada y la añade al playlist

	if url.endswith(".flv"):
		#rtmp://od.flash.plus.es/ondemand/14314/plus/plustv/PO778395.flv
		
		cabecera = url[:32]
		xbmc.output("cabecera="+cabecera)
		finplaypath = url.rfind(".")
		playpath = url[33:finplaypath]
		xbmc.output("playpath="+playpath)
		
		#url = "rtmp://od.flash.plus.es/ondemand"
		url = cabecera
		listitem = xbmcgui.ListItem( title, iconImage="DefaultVideo.png", thumbnailImage=thumbnail )
		listitem.setProperty("SWFPlayer", "http://www.plus.es/plustv/carcasa.swf")
		#listitem.setProperty("Playpath","14314/plus/plustv/PO778395")
		listitem.setProperty("Playpath",playpath)
		listitem.setProperty("Hostname","od.flash.plus.es")
		listitem.setProperty("Port","1935")
		#listitem.setProperty("tcUrl","rtmp://od.flash.plus.es/ondemand")
		listitem.setProperty("tcUrl",cabecera)
		listitem.setProperty("app","ondemand")
		listitem.setProperty("flashVer","LNX 9,0,124,0")
		listitem.setProperty("pageUrl","LNX 9,0,124,0")
	
	else:
		#rtmp://od.flash.plus.es/ondemand/mp4:14314/plus/plustv/NF805546.f4v
		'''
		DEBUG: Parsing...
		DEBUG: Parsed protocol: 0
		DEBUG: Parsed host    : od.flash.plus.es
		DEBUG: Parsed app     : ondemand
		DEBUG: Parsed playpath: mp4:14314/plus/plustv/NF805546.f4v
		DEBUG: Setting buffer time to: 36000000ms
		Connecting ...
		DEBUG: Protocol : RTMP
		DEBUG: Hostname : od.flash.plus.es
		DEBUG: Port     : 1935
		DEBUG: Playpath : mp4:14314/plus/plustv/NF805546.f4v
		DEBUG: tcUrl    : rtmp://od.flash.plus.es:1935/ondemand
		DEBUG: app      : ondemand
		DEBUG: flashVer : LNX 9,0,124,0
		DEBUG: live     : no
		DEBUG: timeout  : 300 sec
		DEBUG: Connect, ... connected, handshaking
		DEBUG: HandShake: Type Answer   : 03
		DEBUG: HandShake: Server Uptime : 1699356683
		DEBUG: HandShake: FMS Version   : 3.5.1.1
		DEBUG: Connect, handshaked
		Connected...
		'''
		# cabecera = "rtmp://od.flash.plus.es/ondemand"
		cabecera = url[:32]
		xbmc.output("cabecera="+cabecera)
		
		# playpath = mp4:14314/plus/plustv/NF805546.f4v
		finplaypath = url.rfind(".")
		playpath = url[33:]
		xbmc.output("playpath="+playpath)
		
		#url = "rtmp://od.flash.plus.es/ondemand"
		url = cabecera
		listitem = xbmcgui.ListItem( title, iconImage="DefaultVideo.png", thumbnailImage=thumbnail )
		listitem.setProperty("SWFPlayer", "http://www.plus.es/plustv/carcasa.swf")
		listitem.setProperty("Playpath",playpath)
		listitem.setProperty("Hostname","od.flash.plus.es")
		listitem.setProperty("Port","1935")
		#listitem.setProperty("tcUrl","rtmp://od.flash.plus.es/ondemand")
		listitem.setProperty("tcUrl",cabecera)
		listitem.setProperty("app","ondemand")
		listitem.setProperty("flashVer","LNX 9,0,124,0")
		listitem.setProperty("pageUrl","LNX 9,0,124,0")

	listitem.setInfo( "video", { "Title": title, "Plot" : plot , "Studio" : CHANNELNAME , "Genre" : category } )
	playlist.add( url, listitem )

	#url= rtmp://od.flash.plus.es/ondemand/14314/plus/plustv/PO778395.flv
	#DEBUG: Protocol : RTMP
	#DEBUG: Playpath : 14314/plus/plustv/PO778395
	#DEBUG: Hostname : od.flash.plus.es
	#DEBUG: Port     : 1935
	#DEBUG: tcUrl    : rtmp://od.flash.plus.es:1935/ondemand
	#DEBUG: app      : ondemand
	#DEBUG: flashVer : LNX 9,0,124,0
	#DEBUG: live     : no
	#DEBUG: timeout  : 300 sec

	# Cierra dialogo
	dialogWait.close()
	del dialogWait

	# Reproduce
	xbmcPlayer = xbmc.Player( xbmc.PLAYER_CORE_AUTO )
	xbmcPlayer.play(playlist)   
