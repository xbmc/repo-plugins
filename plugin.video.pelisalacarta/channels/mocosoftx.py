# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para mocosoftx
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

CHANNELNAME = "mocosoftx"



# Esto permite su ejecución en modo emulado
try:
   pluginhandle = int( sys.argv[ 1 ] )
except:
   pluginhandle = ""

# Traza el inicio del canal
logger.info("[mocosoftx.py] init")

DEBUG = True
def mainlist(params,url,category):
	logger.info("[mocosoftx.py] mainlist")

	# Añade al listado de XBMC
	xbmctools.addnewfolder( CHANNELNAME , "Novedades" , category , "Novedades"            ,"http://mocosoftx.com/foro/index.php","","")
	xbmctools.addnewfolder( CHANNELNAME , "FullList"   , category , "Listado Completo" ,"http://www.mocosoftx.com/foro/index.php?action=.xml;type=rss2;limit=500;board=14","","")

	if config.getSetting("singlechannel")=="true":
		xbmctools.addSingleChannelOptions(params,url,category)

	# Propiedades
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )
	
def Novedades(params,url,category):
	logger.info("[mocosoftx.py] Novedades")

	# Descarga la página
	data = scrapertools.cachePage(url)
	#logger.info(data)
	
	# Extrae las entradas (carpetas)
	patron  = '<td class="sp_middle sp_regular_padding sp_fullwidth">'
	patron += '<a href="(http://mocosoftx.com/foro/peliculas-xxx-online-\(completas\)/[^/]+/)[^"]+"'
	patron += '>([^<]+)</a>'
	patron += '.*?<img src="([^"]+)" alt="'
	matches = re.compile(patron,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)
	for match in matches:
		# Atributos
		scrapedtitle = match[1]
		scrapedurl = match[0]
		scrapedthumbnail = match[2]
		scrapedplot = ""
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELNAME , "detail" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )
	# Extrae la marca de siguiente página
	patronvideos = '\[<b>[^<]+</b>\] <a class="navPages" href="([^"]+)">'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	if len(matches)>0:
		scrapedtitle = "Página siguiente"
		scrapedurl = urlparse.urljoin(url,matches[0])
		scrapedthumbnail = ""
		scrapedplot = ""
		xbmctools.addnewfolder( CHANNELNAME , "Novedades" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )  
   
	# Propiedades
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

	
	
def FullList(params,url,category):
   logger.info("[mocosoftx.py] FullList")
   

   if url=="":
      url = "http://www.mocosoftx.com/foro/index.php?action=.xml;type=rss2;limit=500;board=14"

   # Descarga la página
   data = scrapertools.cachePage(url)
   #logger.info(data)

   # Extrae las entradas (carpetas)
   patron      = '<item>(.*?)</item>'
   matchesITEM = re.compile(patron,re.DOTALL).findall(data)
   #scrapertools.printMatches(matchesITEM[0])
	
   patronvideos = '<title>(.*?)</title>.*?'
   patronvideos += '<\!\[CDATA\[<a href="[^"]+" target="_blank"><img src="([^"]+)".*?'
   for match in matchesITEM:
	matches = re.compile(patronvideos,re.DOTALL).findall(match)
	scrapertools.printMatches(matches)

	for match2 in matches:
		# Titulo
		scrapedtitle = match2[0]
		scrapedtitle = scrapedtitle.replace("<![CDATA[","")
		scrapedtitle = scrapedtitle.replace("]]>","")
		# URL
		scrapedurl = match
		# Thumbnail
      
		scrapedthumbnail = match2[1] 
     
		# Argumento
		scrapedplot = ""

		# Depuracion
		if (DEBUG):
			logger.info("scrapedtitle="+scrapedtitle)
			logger.info("scrapedurl="+scrapedurl)
			logger.info("scrapedthumbnail="+scrapedthumbnail)

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELNAME , "detail" , category , scrapedtitle , scrapedurl , scrapedthumbnail , scrapedplot)

   

   if config.getSetting("singlechannel")=="true":
      xbmctools.addSingleChannelOptions(params,url,category)

   # Label (top-right)...
   xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )

   # Disable sorting...
   xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )

   # End of directory...
   xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def detail(params,url,category):
   logger.info("[mocosoftx.py] detail")
   	
   title = urllib.unquote_plus( params.get("title") )
   thumbnail = urllib.unquote_plus( params.get("thumbnail") )
   plot = unicode( xbmc.getInfoLabel( "ListItem.Plot" ), "utf-8" )
   if "CDATA" in url:
	data = url
	patronthumb = '<img src="([^"]+)"'
	matches = re.compile(patronthumb,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)	
   else:
    #Descarga la página
    data = scrapertools.cachePage(url)
    patronthumb = '<img src="([^"]+)" alt="" border="0" />[</a>|<br />]+'
    matches = re.compile(patronthumb,re.DOTALL).findall(data)
    scrapertools.printMatches(matches) 
   #logger.info(data)
#addnewvideo( canal , accion , category , server , title , url , thumbnail, plot ):
   # ------------------------------------------------------------------------------------
   # Busca los enlaces a los videos
   # ------------------------------------------------------------------------------------
   listavideos = servertools.findvideos(data)
   c=0
   for video in listavideos:
	c=c+1
	try:
		imagen = matches[c]
	except:
		imagen = thumbnail
	xbmctools.addnewvideo( CHANNELNAME ,"play",category,video[2], title+" - ["+video[2]+"]" , video[1] , imagen, plot )
   # ------------------------------------------------------------------------------------

   # Label (top-right)...
   xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
     
   # Disable sorting...
   xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )

   # End of directory...
   xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def play(params,url,category):
   logger.info("[mocosoftx.py] play")

   title = ""#unicode( xbmc.getInfoLabel( "ListItem.Title" ), "utf-8" )
   thumbnail = ""#urllib.unquote_plus( params.get("thumbnail") )
   plot = "" #unicode( xbmc.getInfoLabel( "ListItem.Plot" ), "utf-8" )
   server = params["server"]
   
   
   xbmctools.playvideo(CHANNELNAME,server,url,category,title,thumbnail,plot)
   


