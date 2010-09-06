# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# Canal para kideos
# http://blog.tvalacarta.info/plugin-xbmc/tvalacarta/
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

CHANNELNAME = "kideos"

# Esto permite su ejecución en modo emulado
try:
	pluginhandle = int( sys.argv[ 1 ] )
except:
	pluginhandle = ""

# Traza el inicio del canal
xbmc.output("[kideos.py] init")

DEBUG = True

def mainlist(params,url,category):
	xbmc.output("[kideos.py] ageslist")

	urltail = ""
	if category=="vistos-dia":
		urltail = "?sort_type=day"
	elif category=="vistos-semana":
		urltail = "?sort_type=week"
	elif category=="vistos-mes":
		urltail = "?sort_type=month"
	
	titlehead = ""
	if category=="vistos-dia":
		titlehead = xbmc.getLocalizedString( 30700 ) + " - "
	elif category=="vistos-semana":
		titlehead = xbmc.getLocalizedString( 30701 ) + " - "
	elif category=="vistos-mes":
		titlehead = xbmc.getLocalizedString( 30702 ) + " - "
	
	xbmc.output("[kideos.py] urltail="+urltail)
	# Añade al listado de XBMC
	xbmctools.addnewfolder( CHANNELNAME , "videolist" , category , titlehead+xbmc.getLocalizedString( 30801 ) , "http://kideos.com/videos-for-kids/0-2"+urltail , "", "" )
	xbmctools.addnewfolder( CHANNELNAME , "videolist" , category , titlehead+xbmc.getLocalizedString( 30802 ) , "http://kideos.com/videos-for-kids/3-4"+urltail , "", "" )
	xbmctools.addnewfolder( CHANNELNAME , "videolist" , category , titlehead+xbmc.getLocalizedString( 30803 ) , "http://kideos.com/videos-for-kids/5-6"+urltail , "", "" )
	xbmctools.addnewfolder( CHANNELNAME , "videolist" , category , titlehead+xbmc.getLocalizedString( 30804 ) , "http://kideos.com/videos-for-kids/7-8"+urltail , "", "" )
	xbmctools.addnewfolder( CHANNELNAME , "videolist" , category , titlehead+xbmc.getLocalizedString( 30805 ) , "http://kideos.com/videos-for-kids/9-10"+urltail , "", "" )
	xbmctools.addnewfolder( CHANNELNAME , "videolist" , category , titlehead+xbmc.getLocalizedString( 30806 ) , "http://kideos.com/videos-for-kids/all"+urltail , "", "" )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )

	# Disable sorting...
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def userlist(params,url,category):
	xbmc.output("[kideos.py] ageslist")

	# Añade al listado de XBMC
	xbmctools.addnewfolder( CHANNELNAME , "ageslist" , "vistos-dia" , xbmc.getLocalizedString( 30700 ) , "" , "", "" )
	xbmctools.addnewfolder( CHANNELNAME , "ageslist" , "vistos-semana" , xbmc.getLocalizedString( 30701 ) , "" , "", "" )
	xbmctools.addnewfolder( CHANNELNAME , "ageslist" , "vistos-mes" , xbmc.getLocalizedString( 30702 ) , "" , "", "" )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )

	# Disable sorting...
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def categorylist(params,url,category):
	xbmc.output("[kideos.py] categorylist")

	# Carga la página actual
	data = scrapertools.cachePage("http://www.kideos.com/")
	
	# Pone el enlace para continuar con la siguiente página
	patron = '<a href="(http://kideos.com/category/[^"]+)"><h1>([^<]+)</h1></a>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)		

	for match in matches:
		# Titulo
		scrapedtitle = match[1]
		# URL
		scrapedurl = urlparse.urljoin(url,match[0])
		# Thumbnail
		scrapedthumbnail = ""
		# Argumento
		scrapedplot = ""

		# Depuracion
		if (DEBUG):
			xbmc.output("scrapedtitle="+scrapedtitle)
			xbmc.output("scrapedurl="+scrapedurl)
			xbmc.output("scrapedthumbnail="+scrapedthumbnail)

		# Añade al listado de XBMC
		xbmctools.addthumbnailfolder( CHANNELNAME , scrapedtitle , scrapedurl , scrapedthumbnail, "videolist" )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )

	# Disable sorting...
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def videolist(params,url,category):
	xbmc.output("[kideos.py] videolist")

	# Carga la página actual
	data = scrapertools.cachePage(url)
	addvideopage(data,params,url,category)

	# Obtiene el enlace a la página siguiente
	patron = '<div id="next">[^<]+<a href="([^"]+)">'
	matches = re.compile(patron,re.DOTALL).findall(data)
	
	if len(matches)>0:
		url = urlparse.urljoin(url,matches[0])
		xbmc.output("url siguiente="+url)

	# Carga la página siguiente
	data = scrapertools.cachePage(url)
	addvideopage(data,params,url,category)

	# Obtiene el enlace a la página siguiente
	patron = '<div id="next">[^<]+<a href="([^"]+)">'
	matches = re.compile(patron,re.DOTALL).findall(data)
	
	if len(matches)>0:
		url = urlparse.urljoin(url,matches[0])
		xbmc.output("url siguiente="+url)

	# Carga la página siguiente
	data = scrapertools.cachePage(url)
	addvideopage(data,params,url,category)

	# Pone el enlace para continuar con la siguiente página
	patron = '<div id="next">[^<]+<a href="([^"]+)">'
	matches = re.compile(patron,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)		

	for match in matches:
		# Titulo
		scrapedtitle = xbmc.getLocalizedString( 30900 )
		# URL
		scrapedurl = urlparse.urljoin(url,match)
		# Thumbnail
		scrapedthumbnail = ""
		# Argumento
		scrapedplot = ""

		# Depuracion
		if (DEBUG):
			try:
				xbmc.output("scrapedtitle="+scrapedtitle)
			except:
				xbmc.output("scrapedtitle=<unicode>")
		xbmc.output("scrapedurl="+scrapedurl)
		xbmc.output("scrapedthumbnail="+scrapedthumbnail)

		# Añade al listado de XBMC
		xbmctools.addthumbnailfolder( CHANNELNAME , scrapedtitle , scrapedurl , scrapedthumbnail, "videolist" )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
		
	# Disable sorting...
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def addvideopage(data,params,url,category):

	# Extrae los vídeos
	patron =  '<div id="VideoClip">.*?'
	patron += '<div id="SearchThumbnail">[^<]+<a href="([^"]+)">.*?'
	patron += '<img src=([^\ ]+) .*?'
	patron += '<span class="VideoTitles"><h1>([^<]+)</h1>.*?'
	patron += '<span class="VideoDesc">([^<]+)</span>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	if DEBUG:
		scrapertools.printMatches(matches)		

	# Los añade al directorio
	for match in matches:
		# Titulo
		scrapedtitle = match[2]
		# URL
		scrapedurl = urlparse.urljoin(url,match[0])
		# Thumbnail
		scrapedthumbnail = urlparse.urljoin(url,match[1])
		# Argumento
		scrapedplot = match[3]

		# Depuracion
		if (DEBUG):
			xbmc.output("scrapedtitle="+scrapedtitle)
			xbmc.output("scrapedurl="+scrapedurl)
			xbmc.output("scrapedthumbnail="+scrapedthumbnail)

		# Añade al listado de XBMC
		xbmctools.addnewvideo( CHANNELNAME , "play" , category , "youtube" , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

def play(params,url,category):
	xbmc.output("[kideos.py] play")

	title = urllib.unquote_plus( params.get("title") )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	xbmc.output("[kideos.py] play thumbnail="+thumbnail)
	plot = urllib.unquote_plus( params.get("plot") )
	server = urllib.unquote_plus( params.get("server") )

	# Abre dialogo
	dialogWait = xbmcgui.DialogProgress()
	dialogWait.create( xbmc.getLocalizedString( 30901 ), title , plot )

	# Carga la página de detalle
	data = scrapertools.cachePage(url)
	addvideopage(data,params,url,category)

	# Busca el id del vídeo
	patron = '<param name\="flashVars" value\="videoId\=([^"]+)"'
	matches = re.compile(patron,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)		

	if len(matches)>0:
		video_id = matches[0]
		url = youtube.geturl(video_id)
		listitem = xbmcgui.ListItem( title, iconImage="DefaultVideo.png", thumbnailImage=thumbnail )
		listitem.setInfo( "video", { "Title": title, "Plot": plot } )

	# Cierra dialogo
	dialogWait.close()
	del dialogWait

	# Play video with the proper core
	xbmc.Player().play( url, listitem )
	#xbmctools.playvideo(CHANNELNAME,server,url,category,title,thumbnail,plot)
