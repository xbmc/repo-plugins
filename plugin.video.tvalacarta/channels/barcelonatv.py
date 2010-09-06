# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# tvalacarta - XBMC Plugin
# Canal para barcelonatv
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

xbmc.output("[barcelonatv.py] init")

DEBUG = True
CHANNELNAME = "Barcelona TV"
CHANNELCODE = "barcelonatv"

def mainlist(params,url,category):
	xbmc.output("[barcelonatv.py] mainlist")

	# --------------------------------------------------------
	# Descarga la página
	# --------------------------------------------------------
	data = scrapertools.cachePage("http://www.barcelonatv.cat/alacarta/default.php")
	#xbmc.output(data)

	# --------------------------------------------------------
	# Extrae los programas
	# --------------------------------------------------------
	patron = '<option value=\'(\d+)\'\W*>([^<]+)</option>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	if DEBUG:
		scrapertools.printMatches(matches)

	for match in matches:
		scrapedtitle = match[1]
		scrapedurl = "http://www.barcelonatv.cat/alacarta/cerca.php?cercaProgrames=%s&txt_fInici=01/01/2004&txt_fFin=31/12/2035&Cercar_x=17&Cercar_y=18" % match[0]
		scrapedthumbnail = ""
		scrapedplot = ""

		# Depuracion
		if (DEBUG):
			xbmc.output("scrapedtitle="+scrapedtitle)
			xbmc.output("scrapedurl="+scrapedurl)
			xbmc.output("scrapedthumbnail="+scrapedthumbnail)

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
	xbmc.output("[barcelonatv.py] videolist")

	# --------------------------------------------------------
	# Descarga la página
	# --------------------------------------------------------
	data = scrapertools.cachePage(url)
	#xbmc.output(data)

	# --------------------------------------------------------
	# Extrae los videos
	# --------------------------------------------------------
	patron  = '<li>[^<]+'
	patron += '<div class="pro"><strong>[^<]+</strong>[^<]+'
	patron += '<a href="([^"]+)" title="([^"]+)">[^<]+'
	patron += '<img src="([^"]+)"[^>]+>[^<]+'
	patron += '</a>[^<]+'
	patron += '<h4>[^<]+</h4><span>([^<]+)</span></div>[^<]+'
	patron += '<div class="desc"><p>([^<]+)</p>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	if DEBUG:
		scrapertools.printMatches(matches)

	for match in matches:
		# Titulo
		scrapedtitle = match[1]+" ("+match[3]+")"
		try:
			scrapedtitle = unicode( scrapedtitle, "utf-8" ).encode("iso-8859-1")
		except:
			pass

		# URL
		scrapedurl = "http://www.barcelonatv.cat/alacarta/%s" % match[0]
		
		# Thumbnail
		scrapedthumbnail = match[2]
		
		# procesa el resto
		scrapedplot = match[4]
		try:
			scrapedplot = unicode( scrapedplot, "utf-8" ).encode("iso-8859-1")
		except:
			pass

		if (DEBUG): xbmc.output("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		#addvideo( scrapedtitle , scrapedurl , category )
		xbmctools.addnewvideo( CHANNELCODE , "play" , CHANNELNAME , "" , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# --------------------------------------------------------
	# Extrae el enlace a la siguiente página
	# --------------------------------------------------------
	patron  = "<a href='([^']+)'><img src='([^']+)' alt='Mes' title='Mes' id='botomes' /></a>"
	matches = re.compile(patron,re.DOTALL).findall(data)
	if DEBUG: scrapertools.printMatches(matches)

	for match in matches:
		scrapedtitle = "Página siguiente"
		scrapedurl = urlparse.urljoin(url,match[0])
		scrapedthumbnail = urlparse.urljoin(url,match[1])
		scrapedplot = ""
		if (DEBUG): xbmc.output("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELCODE , "videolist" , CHANNELNAME , scrapedtitle , scrapedurl , scrapedthumbnail , scrapedplot )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def play(params,url,category):
	xbmc.output("[barcelonatv.py] play")

	title = urllib.unquote_plus( params.get("title") )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = urllib.unquote_plus( params.get("plot") )
	xbmc.output("[barcelonatv.py] thumbnail="+thumbnail)

	# Abre dialogo
	dialogWait = xbmcgui.DialogProgress()
	dialogWait.create( 'Descargando datos del vídeo...', title )

	# --------------------------------------------------------
	# Averigua la URL y la descripcion
	# --------------------------------------------------------
	data = scrapertools.cachePage(url)
	patron = '<PARAM NAME="url" VALUE="([^"]+)">'
	matches = re.compile(patron,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)
	try:
		url = matches[0]
	except:
		url = ""

	patron = 'so.addVariable\("sinopsis", "([^"]+)"'
	matches = re.compile(patron,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)
	try:
		scrapedplot = matches[0]
	except:
		scrapedplot = ""

	# --------------------------------------------------------
	# Descarga el .ASX
	# --------------------------------------------------------
	data = scrapertools.cachePage(url)
	patron = 'href="([^"]+)"'
	matches = re.compile(patron,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)
	
	try:
		url = matches[len(matches)-1]
	except:
		url = ""
	
	xbmc.output("[barcelonatv.py] scrapedplot="+scrapedplot)

	# Playlist vacia
	playlist = xbmc.PlayList( xbmc.PLAYLIST_VIDEO )
	playlist.clear()

	# Crea la entrada y la añade al playlist
	listitem = xbmcgui.ListItem( title, iconImage="DefaultVideo.png", thumbnailImage=thumbnail )
	listitem.setInfo( "video", { "Title": title, "Plot" : scrapedplot , "Studio" : CHANNELNAME , "Genre" : category } )
	playlist.add( url, listitem )
	#xbmc.Player(xbmc.PLAYER_CORE_DVDPLAYER).play("rtmp://aialanetfs.fplive.net/aialanet?slist=Jardineria/palmera-roebelen.flv", nuevoitem)

	# Cierra dialogo
	dialogWait.close()
	del dialogWait

	# Reproduce
	xbmcPlayer = xbmc.Player( xbmc.PLAYER_CORE_AUTO )
	xbmcPlayer.play(playlist)   
