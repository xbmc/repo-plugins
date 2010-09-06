# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# tvalacarta - XBMC Plugin
# Canal para Turbonick
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

xbmc.output("[turbonick.py] init")

DEBUG = True
CHANNELNAME = "Turbonick"
CHANNELCODE = "turbonick"

def mainlist(params,url,category):
	xbmc.output("[turbonick.py] mainlist")

	url = 'http://es.turbonick.nick.com/dynamo/turbonick/locale/common/xml/dyn/getGateways.jhtml'

	# --------------------------------------------------------
	# Descarga la página
	# --------------------------------------------------------
	data = scrapertools.cachePage(url)
	#xbmc.output(data)

	# --------------------------------------------------------
	# Extrae las categorias (carpetas)
	# --------------------------------------------------------
	patron = '<gateway cmsid="([^"]+)"\s+title="([^"]+)"\s+urlAlias="[^"]+"\s+iconurl="[^"]+"\s+iconurljpg="([^"]+)"'
	matches = re.compile(patron,re.DOTALL).findall(data)
	if DEBUG:
		scrapertools.printMatches(matches)

	for match in matches:
		scrapedtitle = match[1]
		scrapedurl = 'http://es.turbonick.nick.com/dynamo/turbonick/xml/dyn/getIntlGatewayByID.jhtml?id='+match[0]
		scrapedthumbnail = ""
		scrapedplot = ""

		# Depuracion
		if (DEBUG):
			xbmc.output("scrapedtitle="+scrapedtitle)
			xbmc.output("scrapedurl="+scrapedurl)
			xbmc.output("scrapedthumbnail="+scrapedthumbnail)

		# Añade al listado de XBMC
		if scrapedtitle=="EPISODIOS":
			xbmctools.addnewfolder( CHANNELCODE , "programslist" , CHANNELNAME , "EPISODIOS (AGRUPADOS POR SERIES)" , scrapedurl , scrapedthumbnail, scrapedplot )
			xbmctools.addnewfolder( CHANNELCODE , "videolist" , CHANNELNAME , "EPISODIOS (TODOS)" , scrapedurl , scrapedthumbnail, scrapedplot )
		else:
			xbmctools.addnewfolder( CHANNELCODE , "videolist" , CHANNELNAME , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )
		
	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )

	# Disable sorting...
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def videolist(params,url,category):
	xbmc.output("[turbonick.py] videolist")

	# --------------------------------------------------------
	# Descarga la página
	# --------------------------------------------------------
	data = scrapertools.cachePage(url)
	#xbmc.output(data)

	# --------------------------------------------------------
	# Extrae los vídeos
	# --------------------------------------------------------
	patron  = '<content.*?'
	patron += 'cmsid="([^"]+)"'
	patron += '(?:\s+iconurl="([^"]+)")?.*?'
	patron += '<title>([^<]+)</title>.*?'
	patron += '<description>([^<]+)</description>.*?'
	patron += '(?:<iconurl>([^<]+)</iconurl>)?'
	matches = re.compile(patron,re.DOTALL).findall(data)
	if DEBUG:
		scrapertools.printMatches(matches)

	dictionaryurl = {}

	for match in matches:
		try:
			scrapedtitle = unicode( match[2] + " - " + match[3], "utf-8" ).encode("iso-8859-1")
		except:
			scrapedtitle = match[2] + " - " + match[3]
		scrapedurl = 'http://es.turbonick.nick.com/dynamo/turbonick/xml/dyn/flvgenPT.jhtml?vid='+match[0]+'&hiLoPref=hi'
		scrapedthumbnail = match[1]
		if scrapedthumbnail == "":
			scrapedthumbnail = match[4]
		scrapedplot = ""

		# Depuracion
		if (DEBUG):
			xbmc.output("scrapedtitle="+scrapedtitle)
			xbmc.output("scrapedurl="+scrapedurl)
			xbmc.output("scrapedthumbnail="+scrapedthumbnail)

		# Añade al listado de XBMC
		if dictionaryurl.has_key(scrapedurl):
			xbmc.output("repetido")
		else:
			xbmctools.addnewvideo( CHANNELCODE , "play" , CHANNELNAME , "" , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )
			dictionaryurl[scrapedurl] = True

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )

	# Disable sorting...
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def programslist(params,url,category):
	xbmc.output("[turbonick.py] programslist")

	# --------------------------------------------------------
	# Descarga la página
	# --------------------------------------------------------
	data = scrapertools.cachePage(url)
	#xbmc.output(data)

	# --------------------------------------------------------
	# Extrae los vídeos
	# --------------------------------------------------------
	patron  = '<content.*?'
	patron += 'cmsid="([^"]+)"'
	patron += '(?:\s+iconurl="([^"]+)")?.*?'
	patron += '<title>([^<]+)</title>.*?'
	patron += '<description>([^<]+)</description>.*?'
	patron += '(?:<iconurl>([^<]+)</iconurl>)?'
	matches = re.compile(patron,re.DOTALL).findall(data)
	if DEBUG:
		scrapertools.printMatches(matches)

	encontrados = set()

	for match in matches:
		# Lee el título (nombre de la serie o del episodio con ":")
		try:
			scrapedtitle = unicode( match[2] , "utf-8" ).encode("iso-8859-1")
		except:
			scrapedtitle = match[2] 

		# Parte en el signo ":"
		patrontitulo = '(.*?):'
		matchestitulo = re.compile(patrontitulo,re.DOTALL).findall(scrapedtitle)
		
		if len(matchestitulo)>0:
			scrapedtitle = matchestitulo[0].strip()

		# Agrupa por el nombre de la serie
		if scrapedtitle not in encontrados:
			xbmc.output("[turbonick.py] programslist   nueva serie "+scrapedtitle)
			encontrados.add(scrapedtitle)
			
			scrapedthumbnail = match[1]
			if scrapedthumbnail == "":
				scrapedthumbnail = match[4]
			scrapedplot = ""

			# Depuracion
			if (DEBUG):
				xbmc.output("scrapedtitle="+scrapedtitle)
				xbmc.output("scrapedurl="+url)
				xbmc.output("scrapedthumbnail="+scrapedthumbnail)

			# Añade al listado de XBMC
			xbmctools.addnewvideo( CHANNELCODE , "pvideolist" , CHANNELNAME , "" , scrapedtitle , url , scrapedthumbnail, scrapedplot )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )

	# Disable sorting...
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def pvideolist(params,url,category):
	xbmc.output("[turbonick.py] programsvideolist")

	# El título es el de la serie
	title = urllib.unquote_plus( params.get("title") )
	xbmc.output("[turbonick.py] programsvideolist title="+title)

	# --------------------------------------------------------
	# Descarga la página
	# --------------------------------------------------------
	data = scrapertools.cachePage(url)
	#xbmc.output(data)

	# --------------------------------------------------------
	# Extrae los vídeos
	# --------------------------------------------------------
	patron  = '<content.*?'
	patron += 'cmsid="([^"]+)"'
	patron += '(?:\s+iconurl="([^"]+)")?.*?'
	patron += '<title>([^<]+)</title>.*?'
	patron += '<description>([^<]+)</description>.*?'
	patron += '(?:<iconurl>([^<]+)</iconurl>)?'
	matches = re.compile(patron,re.DOTALL).findall(data)
	if DEBUG:
		scrapertools.printMatches(matches)

	dictionaryurl = {}

	for match in matches:
		try:
			scrapedtitle = unicode( match[2] + " - " + match[3], "utf-8" ).encode("iso-8859-1")
		except:
			scrapedtitle = match[2] + " - " + match[3]
		scrapedurl = 'http://es.turbonick.nick.com/dynamo/turbonick/xml/dyn/flvgenPT.jhtml?vid='+match[0]+'&hiLoPref=hi'
		scrapedthumbnail = match[1]
		if scrapedthumbnail == "":
			scrapedthumbnail = match[4]
		scrapedplot = ""

		# Añade al listado de XBMC
		if dictionaryurl.has_key(scrapedurl):
			xbmc.output("repetido")
		else:
			# Sólo añade los de la serie elegida
			if scrapedtitle.startswith(title):
				# Depuracion
				if (DEBUG):
					xbmc.output("scrapedtitle="+scrapedtitle)
					xbmc.output("scrapedurl="+scrapedurl)
					xbmc.output("scrapedthumbnail="+scrapedthumbnail)

				xbmctools.addnewvideo( CHANNELCODE , "play" , CHANNELNAME , "" , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )
				dictionaryurl[scrapedurl] = True

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )

	# Disable sorting...
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def play(params,url,category):
	xbmc.output("[turbonick.py] play")

	title = urllib.unquote_plus( params.get("title") )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = urllib.unquote_plus( params.get("plot") )
	xbmc.output("[turbonick.py] thumbnail="+thumbnail)

	# Abre dialogo
	dialogWait = xbmcgui.DialogProgress()
	dialogWait.create( 'Descargando datos del vídeo...', title )

	# --------------------------------------------------------
	# Descarga pagina detalle
	# --------------------------------------------------------
	data = scrapertools.cachePage(url)
	patron = '<src>([^<]+)</src>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)
	url = matches[0]
	#rtmp://cp35019.edgefcs.net/ondemand/mtviestor/_!/intlnick/es/AVATAR/AVATAR1A_OD_640.flv
	#DEBUG: Protocol : RTMP
	#DEBUG: Hostname : cp35019.edgefcs.net
	#DEBUG: Port     : 1935
	#DEBUG: Playpath : mtviestor/_!/intlnick/es/AVATAR/AVATAR1A_OD_640
	#DEBUG: tcUrl    : rtmp://cp35019.edgefcs.net:1935/ondemand
	#DEBUG: app      : ondemand
	#DEBUG: flashVer : LNX 9,0,124,0
	#DEBUG: live     : no
	#DEBUG: timeout  : 300 sec
	cabecera = url[:35]
	xbmc.output("cabecera="+cabecera)
	finplaypath = url.rfind(".")
	playpath = url[35:finplaypath]
	xbmc.output("playpath="+playpath)

	xbmc.output("url="+url)

	# Playlist vacia
	playlist = xbmc.PlayList( xbmc.PLAYLIST_VIDEO )
	playlist.clear()

	# Crea la entrada y la añade al playlist
	url = cabecera
	listitem = xbmcgui.ListItem( title, iconImage="DefaultVideo.png", thumbnailImage=thumbnail )
	listitem.setProperty("SWFPlayer", "http://es.turbonick.nick.com/global/apps/broadband/swf/bb_flv_player.swf")
	#listitem.setProperty("Playpath","14314/plus/plustv/PO778395")
	listitem.setProperty("Playpath",playpath)
	listitem.setProperty("Hostname","cp35019.edgefcs.net")
	listitem.setProperty("Port","1935")
	#listitem.setProperty("tcUrl","rtmp://od.flash.plus.es/ondemand")
	listitem.setProperty("tcUrl",cabecera)
	listitem.setProperty("app","ondemand")
	listitem.setProperty("flashVer","LNX 9,0,124,0")
	#listitem.setProperty("pageUrl","LNX 9,0,124,0")
	
	listitem.setInfo( "video", { "Title": title, "Plot" : plot , "Studio" : CHANNELNAME , "Genre" : category } )
	playlist.add( url, listitem )

	# Cierra dialogo
	dialogWait.close()
	del dialogWait

	# Reproduce
	xbmcPlayer = xbmc.Player( xbmc.PLAYER_CORE_AUTO )
	xbmcPlayer.play(playlist)   
