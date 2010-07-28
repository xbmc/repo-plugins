# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para descargacineclasico
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
# contribución de ermanitu
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
import anotador
import config
import logger

CHANNELNAME = "descargacineclasico"

# Esto permite su ejecución en modo emulado
try:
	pluginhandle = int( sys.argv[ 1 ] )
except:
	pluginhandle = ""

# Traza el inicio del canal
logger.info("[descargacineclasico.py] init")

DEBUG = True
Generate = False # poner a true para generar listas de peliculas
LoadThumbnails = True # indica si cargar los carteles

def mainlist(params,url,category):
	logger.info("[descargacineclasico.py] mainlist")

	xbmctools.addnewfolder( CHANNELNAME , "movielist" , CHANNELNAME , "Aventuras" , "http://descargacineclasico.blogspot.com/search/label/Aventuras?updated-max=&max-results=1000" , "", "" )
	xbmctools.addnewfolder( CHANNELNAME , "movielist" , CHANNELNAME , "Ciencia Ficción" , "http://descargacineclasico.blogspot.com/search/label/Ciencia%20Ficcion?updated-max=&max-results=1000" , "", "" )
	xbmctools.addnewfolder( CHANNELNAME , "movielist" , CHANNELNAME , "Comedias" , "http://descargacineclasico.blogspot.com/search/label/Comedias?updated-max=&max-results=1000" , "", "" )
	xbmctools.addnewfolder( CHANNELNAME , "movielist" , CHANNELNAME , "Drama" , "http://descargacineclasico.blogspot.com/search/label/Drama?updated-max=&max-results=1000" , "", "" )
	xbmctools.addnewfolder( CHANNELNAME , "movielist" , CHANNELNAME , "Intriga" , "http://descargacineclasico.blogspot.com/search/label/Intriga?updated-max=&max-results=1000" , "", "" )
	xbmctools.addnewfolder( CHANNELNAME , "movielist" , CHANNELNAME , "Románticas" , "http://descargacineclasico.blogspot.com/search/label/Romanticas?updated-max=&max-results=1000" , "", "" )
	xbmctools.addnewfolder( CHANNELNAME , "movielist" , CHANNELNAME , "Series" , "http://descargacineclasico.blogspot.com/search/label/Series?updated-max=&max-results=1000" , "", "" )
	xbmctools.addnewfolder( CHANNELNAME , "movielist" , CHANNELNAME , "Western" , "http://descargacineclasico.blogspot.com/search/label/Wester?updated-max=&max-results=1000" , "", "" )
	xbmctools.addnewfolder( CHANNELNAME , "movielist" , CHANNELNAME , "Novedades" , "http://descargacineclasico.blogspot.com/" , "", "" )
	xbmctools.addnewfolder( CHANNELNAME , "movielist" , CHANNELNAME , "Todas" , "http://descargacineclasico.blogspot.com/search?updated-max=&max-results=1000" , "", "" )

	if config.getSetting("singlechannel")=="true":
		xbmctools.addSingleChannelOptions(params,url,category)

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )

	# Disable sorting...
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def movielist(params,url,category):
	logger.info("[descargacineclasico.py] mainlist")

	# Descarga la página
	data = scrapertools.cachePage(url)
	#logger.info(data)

	# Extrae las entradas (carpetas)
	patronvideos  = "<h3>\n<a href='([^']+)'>(.*?)</a>"
	patronvideos += '.*?<a onblur=.*?src="(.*?)"' # cartel
#	patronvideos += ".*?SINOPSIS:(.*?)(PUBLICADO POR" # sinopsis
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	#scrapertools.printMatches(matches)

	if (Generate):
		f = open(config.DATA_PATH + '/films.tab', 'w') # fichero para obtener las notas

	for match in matches:
		# Titulo
		scrapedtitle = match[1]
		scrapedtitle = scrapedtitle.replace('&#161;','') # ¡
		scrapedtitle = scrapedtitle.replace('&#191;','') # ¿
		logger.info(scrapedtitle)
	#	if (not Generate):
	#		score = anotador.getscore(match[1])
	#		if (score != ""):
	#		scrapedtitle += " " + score
	
		# URL
		scrapedurl = urlparse.urljoin(url,match[0]) # url de la ficha descargacineclasico
	
		# Thumbnail
	#	scrapedthumbnail = urlparse.urljoin(url,match[2])
		scrapedthumbnail = ""
		if LoadThumbnails:
			scrapedthumbnail = match[2].replace("s200","s1600")
	
		# procesa el resto
	#	scrapeddescription = match[3]
		scrapeddescription = ""
	
		# Depuracion
		if (DEBUG):
			logger.info("scrapedtitle="+scrapedtitle)
			logger.info("scrapedurl="+scrapedurl)
			logger.info("scrapedthumbnail="+scrapedthumbnail)
	
		if (Generate):
			sanio = re.search('(.*?)\((.*?)\)',scrapedtitle)
			if (sanio): # si hay anio
				fareg = sanio.group(1) + "\t" + sanio.group(2) + "\t" + scrapedtitle
			else:
				fareg = scrapedtitle + "\t\t" + scrapedtitle
			f.write(fareg+"\n")
	
		# Añade al listado de XBMC
		xbmctools.addthumbnailfolder( CHANNELNAME , scrapedtitle , scrapedurl , scrapedthumbnail, "detail" )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )

	# Disable sorting...
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

	if (Generate):
		f.close()

def detail(params,url,category):
	logger.info("[descargacineclasico.py] detail")

	title = urllib.unquote_plus( params.get("title") )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	logger.info("[descargacineclasico.py] title="+title)
	logger.info("[descargacineclasico.py] thumbnail="+thumbnail)

	# Descarga la página
	data = scrapertools.cachePage(url)
	#logger.info(data)

	# ------------------------------------------------------------------------------------
	# Busca los enlaces a los videos
	# ------------------------------------------------------------------------------------
	listavideos = servertools.findvideos(data)

	for video in listavideos:
		xbmctools.addvideo( CHANNELNAME , title+" - "+video[0] , video[1] , category , video[2] )
	# ------------------------------------------------------------------------------------

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )

	# Disable sorting...
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def play(params,url,category):
	logger.info("[descargacineclasico.py] play")

	title = unicode( xbmc.getInfoLabel( "ListItem.Title" ), "utf-8" )
	thumbnail = xbmc.getInfoImage( "ListItem.Thumb" )
	plot = unicode( xbmc.getInfoLabel( "ListItem.Plot" ), "utf-8" )
	server = params["server"]
	logger.info("[descargacineclasico.py] thumbnail="+thumbnail)
	logger.info("[descargacineclasico.py] server="+server)

	xbmctools.playvideo(CHANNELNAME,server,url,category,title,thumbnail,plot)

#mainlist(None,"","mainlist")
#detail(None,"http://impresionante.tv/ponyo.html","play")











