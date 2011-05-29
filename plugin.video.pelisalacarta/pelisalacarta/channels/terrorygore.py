# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para pintadibujos
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------
import urlparse, urllib2,urllib,re
import sys
import xbmc
import xbmcgui
import xbmcplugin

from core import scrapertools
from core import config
from core import logger
from core import xbmctools
from core.item import Item
from servers import servertools

CHANNELNAME = "terrorygore"

# Traza el inicio del canal
logger.info("[terrorygore.py] init")

DEBUG = True

def mainlist(params,url,category):
    logger.info("[terrorygore.py] mainlist")

    xbmctools.addnewfolder( CHANNELNAME , "movielist" , CHANNELNAME , "Películas de Terror" , "http://www.terrorygore.com/feeds/posts/default?start-index=1&max-results=50" , "", "" )
    xbmctools.addnewfolder( CHANNELNAME , "movielist" , CHANNELNAME , "Película de Terror Asiáticas (VOSEng)" , "http://asianmovielink.blogspot.com/feeds/posts/default/-/Horror?start-index=1&max-results=50" , "", "" )

    # Label (top-right)...
    xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )

    # Disable sorting...
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )

    # End of directory...
    xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def movielist(params,url,category):
    logger.info("[terrorygore.py] mainlist")

    # Descarga la página
    data = scrapertools.cachePage(url)
    
    start_index = "1"
    start_index_re = "start-index=(.*)&"
    url_params = url.split("?",1)
    url_limpia = url_params[0]
    matches = re.compile(start_index_re,re.DOTALL).findall(url)

    if len(matches)>0:
        start_index = matches[0]
        new_start = int(start_index) + 50

    #Para evitar problemas cuando el XML no esta completo o bien estructurado (que por desgracia pasa)
    entrada_blog_re = "<entry>(.*?)</entry>"

    # Expresion Regular para extraer la info
    patronvideos  = "<title.*?>(.*?)</title>.*?"
    patronvideos += "<summary type=['\"]text['\"]>(.*?)</summary>.*?"
    patronvideos += "<link rel=['\"]alternate['\"].*?href=['\"](.*?)['\"].*?"
    patronvideos += "<media:thumbnail.*?url=['\"](.*?)['\"]"
    
    matches = re.compile(entrada_blog_re,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    #Procesamos cada coincidencia 
    for match in matches:
        entrada_blog = match
        matches_entradas = re.compile(patronvideos,re.DOTALL).findall(entrada_blog)
        for match2 in matches_entradas:

            # Titulo
            scrapedtitle = match2[0]

            # URL
            scrapedurl = match2[2]
        
            # Thumbnail
        
            scrapedthumbnail = match2[3]
            
            #Queremos la caratula con una calida mejor. Este cambio devuelve una imagen de 200px en vez de 72px
            scrapedthumbnail = scrapedthumbnail.replace("s72-c","s200")
            # Argumento
            scrapedplot = match2[1]

            # Depuracion
            if (DEBUG):
                logger.info("scrapedtitle="+scrapedtitle)
                logger.info("scrapedurl="+scrapedurl)
                logger.info("scrapedthumbnail="+scrapedthumbnail)

            # Añade al listado de XBMC
            xbmctools.addnewfolder( CHANNELNAME , "detail" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )
        
    if len(matches)>45:
        scrapedurl = url_limpia+"?start-index="+str(new_start)+"&max-results=50" 
        xbmctools.addnewfolder( CHANNELNAME , "movielist" , CHANNELNAME , "Página Siguiente" , scrapedurl , "", "" )

    # Label (top-right)...
    xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )

    # Disable sorting...
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )

    # End of directory...
    xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def detail(params,url,category):
    logger.info("[terrorygore.py] detail")

    title = urllib.unquote_plus( params.get("title") )
    thumbnail = urllib.unquote_plus( params.get("thumbnail") )

    # Descarga la página
    data = scrapertools.cachePage(url)
    #logger.info(data)

    # ------------------------------------------------------------------------------------
    # Busca los enlaces a los videos
    # ------------------------------------------------------------------------------------
    listavideos = servertools.findvideos(data)

    for video in listavideos:
        xbmctools.addnewvideo( CHANNELNAME , "play" , category , video[2] , title + " - " + video[0] , video[1] , thumbnail , "" )
    # ------------------------------------------------------------------------------------

    # Label (top-right)...
    xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
        
    # Disable sorting...
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )

    # End of directory...
    xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def play(params,url,category):
    logger.info("[terrorygore.py] play")

    title = urllib.unquote_plus( params.get("title") )
    thumbnail = urllib.unquote_plus( params.get("thumbnail") )
    plot = urllib.unquote_plus( params.get("plot") )
    server = params["server"]

    xbmctools.playvideo(CHANNELNAME,server,url,category,title,thumbnail,plot)

