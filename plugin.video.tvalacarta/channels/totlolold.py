# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# totlol - XBMC Plugin
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
import savedsearch
import youtube

CHANNELNAME = "totlol"

# Esto permite su ejecución en modo emulado
try:
	pluginhandle = int( sys.argv[ 1 ] )
except:
	pluginhandle = ""

# Traza el inicio del canal
xbmc.output("[totlol.py] init")

DEBUG = True

def mainlist(params,url,category):
	xbmc.output("[totlol.py] search")

	xbmctools.addnewfolder( CHANNELNAME , "search" , CHANNELNAME , xbmc.getLocalizedString( 30501 ) , "" , "", "" )

	'''
	lines = savedsearch.readsavedsearches("totlol")
	for line in lines:
		xbmctools.addnewfolder( CHANNELNAME , "videolist" , CHANNELNAME , xbmc.getLocalizedString( 30501 )+' "'+line.strip()+'"' , 'http://www.totlol.com/search?search_id='+line.strip() , "", "" )
	'''

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def search(params,url,category):
	xbmc.output("[totlol.py] search")

	keyboard = xbmc.Keyboard('')
	keyboard.doModal()
	if (keyboard.isConfirmed()):
		tecleado = keyboard.getText()
		if len(tecleado)>0:
			#convert to HTML
			tecleado = tecleado.replace(" ", "+")
			searchUrl = 'http://www.totlol.com/search?search_id='+tecleado
			savedsearch.addsavedsearch(tecleado)
			videolist(params,searchUrl,category)

def videolist(params,url,category):
	xbmc.output("[totlol.py] videolist")

	# Carga la página actual
	data = scrapertools.cachePage(url)
	addvideopage(data,params,url,category)

	# Obtiene el enlace a la página siguiente
	#http://www.totlol.com/search?&amp;page=2&amp;u=&amp;c=&amp;search_id=pocoyo
	patron = '<a class="paging-pagelink" href="([^"]+)">Next \&gt\;</a>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	
	if len(matches)>0:
		url = urlparse.urljoin(url,matches[0].replace("&amp;","&"))
		xbmc.output("url siguiente="+url)

	# Carga la página siguiente
	data = scrapertools.cachePage(url)
	addvideopage(data,params,url,category)

	# Obtiene el enlace a la página siguiente
	patron = '<a class="paging-pagelink" href="([^"]+)">Next \&gt\;</a>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	
	if len(matches)>0:
		url = urlparse.urljoin(url,matches[0].replace("&amp;","&"))
		xbmc.output("url siguiente="+url)

	# Carga la página siguiente
	data = scrapertools.cachePage(url)
	addvideopage(data,params,url,category)

	# Pone el enlace para continuar con la siguiente página
	patron = '<a class="paging-pagelink" href="([^"]+)">Next \&gt\;</a>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)		

	for match in matches:
		# Titulo
		scrapedtitle = xbmc.getLocalizedString( 30701 )
		# URL
		scrapedurl = urlparse.urljoin(url,match.replace("&amp;","&"))
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
	# Pone el enlace para continuar con la siguiente página
	# La URL tiene el id de vídeo de youtube: http://www.totlol.com/watch/Bxu3jfqpItE/Pocoyo-Dance/0/
	patron  = '<table id="videoitem[^"]+" class="videoitem basic"><tr>[^<]+'
	patron += '<td class="thumb">[^<]+'
	patron += '<div class="videothumb smallthumb">[^<]+'
	patron += '<a href="([^"]+)"><img.*?src="([^"]+)".*?'
	patron += '<div class="title"><a.*?>([^<]+)</a></div>[^<]+'
	patron += '<span class="info">Runtime\:</span>([^<]+)<.*?'
	patron += '<span class="info">Language\:</span>([^<]+)<'
	matches = re.compile(patron,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)		

	for match in matches:
		# Titulo
		scrapedtitle = match[2]+' ('+match[3].strip()+') ('+match[4].strip()+')'
		# URL
		scrapedurl = urlparse.urljoin(url,match[0])
		# Thumbnail
		scrapedthumbnail = urlparse.urljoin(url,match[1])
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
		xbmctools.addnewvideo( CHANNELNAME , "play" , category , "youtube" , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

def play(params,url,category):
	xbmc.output("[totlol.py] play")

	title = urllib.unquote_plus( params.get("title") )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = urllib.unquote_plus( params.get("plot") )
	server = urllib.unquote_plus( params.get("server") )

	# Abre dialogo
	dialogWait = xbmcgui.DialogProgress()
	dialogWait.create( xbmc.getLocalizedString( 30702 ), title , plot )

	# Busca el id del vídeo
	# La URL tiene el id de vídeo de youtube: http://www.totlol.com/watch/Bxu3jfqpItE/Pocoyo-Dance/0/
	patron = 'http\:\/\/www.totlol.com\/watch\/([^\/]+)/'
	matches = re.compile(patron,re.DOTALL).findall(url)
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
