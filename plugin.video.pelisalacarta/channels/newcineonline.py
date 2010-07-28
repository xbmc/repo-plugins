# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para newcineonline
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

CHANNELNAME = "newcineonline"

# Esto permite su ejecución en modo emulado
try:
	pluginhandle = int( sys.argv[ 1 ] )
except:
	pluginhandle = ""

logger.info("[newcineonline.py] init")

DEBUG = True

def mainlist(params,url,category):
	logger.info("[newcineonline.py] mainlist")

	# Añade al listado de XBMC
	addfolder("Novedades", "http://www.newcineonline.com/" ,"list")
	addfolder("Estrenos", "http://www.newcineonline.com/index.php?do=cat&category=estrenos" ,"list")
	addfolder("Peliculas", "http://www.newcineonline.com/index.php?do=cat&category=peliculas" ,"list")
	addfolder("Documentales", "http://www.newcineonline.com/index.php?do=cat&category=documentales" ,"list")
	addfolder("Peliculas VOS", "http://www.newcineonline.com/index.php?do=cat&category=peliculas-vos" ,"list")
	addfolder("Dibujos", "http://www.newcineonline.com/index.php?do=cat&category=dibujos" ,"list")
	addfolder("Series", "http://www.newcineonline.com/index.php?do=cat&category=series" ,"list")

	if config.getSetting("singlechannel")=="true":
		xbmctools.addSingleChannelOptions(params,url,category)

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
		
	# Disable sorting...
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def list(params,url,category):
	logger.info("[newcineonline.py] list")

	# Descarga la página
	data = scrapertools.cachePage(url)
	#logger.info(data)

	# Extrae las entradas (carpetas)
	patronvideos  = '<div id="post-info-mid">[^<]+<div class="post-title"><a href="([^"]+)">([^<]+)</a></div>'
	patronvideos += '.*?<td class="post-story">.*?<tbody>.*?<img src="([^"]+)"[^>]+>(.*?)</tbody>'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	for match in matches:
		# Titulo
		scrapedtitle = match[1]

		# URL
		scrapedurl = urlparse.urljoin(url,match[0])
		
		# Thumbnail
		scrapedthumbnail = urlparse.urljoin(url,match[2])
		
		# procesa el resto
		scrapeddescription = match[3]
		scrapeddescription = scrapertools.htmlclean(scrapeddescription)
		scrapeddescription = scrapeddescription.replace("<!--colorstart:#589BB9-->","")
		scrapeddescription = scrapeddescription.replace("<!--colorend-->","")
		scrapeddescription = scrapeddescription.replace("<!--/colorend-->","")
		scrapeddescription = scrapeddescription.replace("<!--/colorstart-->","")
		scrapeddescription = scrapeddescription.strip()

		# Depuracion
		if (DEBUG):
			logger.info("scrapedtitle="+scrapedtitle)
			logger.info("scrapedurl="+scrapedurl)
			logger.info("scrapedthumbnail="+scrapedthumbnail)

		# Añade al listado de XBMC
		#addfolder( scrapedtitle , scrapedurl , "detail" )
		xbmctools.addnewfolder( CHANNELNAME , "detail" , CHANNELNAME , scrapedtitle , scrapedurl , scrapedthumbnail , scrapeddescription )

	# ------------------------------------------------------------------------------------
	# Busca los enlaces a los mirrors, o a los capítulos de las series...
	# ------------------------------------------------------------------------------------
	logger.info("Busca el enlace de página siguiente...")
	try:
		# La siguiente página
		patronvideos  = '<a href\="([^"]+)"><span class\="navigation"[^>]+>Sigu'
		matches = re.compile(patronvideos,re.DOTALL).findall(data)
		
		url = matches[0]
		addfolder("!Siguiente",url,"list")
	except:
		logger.info("No encuentro la pagina...")

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )

	# Disable sorting...
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def detail(params,url,category):
	logger.info("[newcineonline.py] detail")

	title = urllib.unquote_plus( params.get("title") )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )

	# Descarga la página
	data = scrapertools.cachePage(url)
	#logger.info(data)
	
	# La siguiente página
	patronvideos  = '<embed src\="http\:\/\/wwwstatic.megavideo.com\/mv\_player\.swf\?image=[^\&]+\&amp\;v\=([^"]+)"'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)
	if len(matches)>0:
		xbmctools.addnewvideo( CHANNELNAME , "play" , category , "Megavideo" , title + " - [Megavideo]" , matches[0], thumbnail , "" )

	# ------------------------------------------------------------------------------------
	# Busca los enlaces a los videos
	# ------------------------------------------------------------------------------------
	listavideos = servertools.findvideos(data)
	
	for video in listavideos:
		xbmctools.addnewvideo( CHANNELNAME , "play" , category , video[2] , title +" - "+video[0], video[1], thumbnail , "" )
	# ------------------------------------------------------------------------------------

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
		
	# Disable sorting...
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def play(params,url,category):
	logger.info("[newcineonline.py] play")

	title = unicode( xbmc.getInfoLabel( "ListItem.Title" ), "utf-8" )
	thumbnail = xbmc.getInfoImage( "ListItem.Thumb" )
	plot = unicode( xbmc.getInfoLabel( "ListItem.Plot" ), "utf-8" )
	server = params["server"]
	logger.info("[newcineonline.py] thumbnail="+thumbnail)
	logger.info("[newcineonline.py] server="+server)
	
	xbmctools.playvideo(CHANNELNAME,server,url,category,title,thumbnail,plot)

def addfolder(nombre,url,accion):
	logger.info('[newcineonline.py] addfolder( "'+nombre+'" , "' + url + '" , "'+accion+'")"')
	listitem = xbmcgui.ListItem( nombre , iconImage="DefaultFolder.png")
	itemurl = '%s?channel=newcineonline&action=%s&category=%s&url=%s' % ( sys.argv[ 0 ] , accion , urllib.quote_plus(nombre) , urllib.quote_plus(url) )
	xbmcplugin.addDirectoryItem( handle = int(sys.argv[ 1 ]), url = itemurl , listitem=listitem, isFolder=True)

def addvideo(nombre,url,category,server):
	logger.info('[newcineonline.py] addvideo( "'+nombre+'" , "' + url + '" , "'+server+'")"')
	listitem = xbmcgui.ListItem( nombre, iconImage="DefaultVideo.png" )
	listitem.setInfo( "video", { "Title" : nombre, "Plot" : nombre } )
	itemurl = '%s?channel=newcineonline&action=play&category=%s&url=%s&server=%s' % ( sys.argv[ 0 ] , category , urllib.quote_plus(url) , server )
	xbmcplugin.addDirectoryItem( handle=int(sys.argv[ 1 ]), url=itemurl, listitem=listitem, isFolder=False)

def addthumbnailfolder( scrapedtitle , scrapedurl , scrapedthumbnail , accion ):
	logger.info('[newcineonline.py] addthumbnailfolder( "'+scrapedtitle+'" , "' + scrapedurl + '" , "'+scrapedthumbnail+'" , "'+accion+'")"')
	listitem = xbmcgui.ListItem( scrapedtitle, iconImage="DefaultFolder.png", thumbnailImage=scrapedthumbnail )
	itemurl = '%s?channel=newcineonline&action=%s&category=%s&url=%s' % ( sys.argv[ 0 ] , accion , urllib.quote_plus( scrapedtitle ) , urllib.quote_plus( scrapedurl ) )
	xbmcplugin.addDirectoryItem( handle = int(sys.argv[ 1 ]), url = itemurl , listitem=listitem, isFolder=True)
