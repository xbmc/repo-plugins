# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para ovasid
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

CHANNELNAME = "ovasid"

# Esto permite su ejecución en modo emulado
try:
    pluginhandle = int( sys.argv[ 1 ] )
except:
    pluginhandle = ""

# Traza el inicio del canal
logger.info("[ovasid.py] init")

DEBUG = True

def mainlist(params,url,category):
    logger.info("[ovasid.py] mainlist")
    
    if url=="":
        url="http://www.ovasid.com/"
    
    # Descarga la página
    data = scrapertools.cachePage(url)
    #logger.info(data)

    # Extrae las entradas (carpetas)
    patron  = '<div class="item">[^<]+'
    patron += '<div class="background"></div>[^<]+'
    patron += '<a href="([^"]+)" ><img class="imgl" src="([^"]+)"/></a>[^<]+'
    patron += '<div class="content">[^<]+'
    patron += '<h1>([^<]+)</h1>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for match in matches:
        scrapedtitle = match[2]
        scrapedurl = urlparse.urljoin(url,match[0])
        scrapedthumbnail = urlparse.urljoin(url,match[1])
        scrapedplot = ""
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        # Añade al listado de XBMC
        xbmctools.addnewfolder( CHANNELNAME , "detail" , category , scrapedtitle , scrapedurl , scrapedthumbnail , scrapedplot )

    # Label (top-right)...
    xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
    xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
    xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def detail(params,url,category):
    logger.info("[ovasid.py] detail")

    title = urllib.unquote_plus( params.get("title") )
    thumbnail = urllib.unquote_plus( params.get("thumbnail") )

    # Descarga la página
    data = scrapertools.cachePage(url)
    #logger.info(data)
    
    # Extrae las entradas (capítulos)
    patronvideos = '<param name="flashvars" value="file=([^\&]+)\&amp'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for match in matches:
        scrapedurl = urlparse.urljoin(url,match)
        if scrapedurl.endswith(".xml"):
            scrapedtitle = title
        else:
            scrapedtitle = title + " - [Directo]"
        scrapedthumbnail = thumbnail
        scrapedplot = ""

        # Depuracion
        if (DEBUG):
            logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        # Añade al listado de XBMC
        if scrapedurl.endswith(".xml"):
            xbmctools.addnewfolder( CHANNELNAME , "playlist" , category , scrapedtitle , scrapedurl , scrapedthumbnail , scrapedplot )
        else:
            xbmctools.addnewvideo( CHANNELNAME , "play" , category , "Directo" , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

    # Label (top-right)...
    xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
    xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
    xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def playlist(params,url,category):
    logger.info("[ovasid.py] playlist")

    title = urllib.unquote_plus( params.get("title") )
    thumbnail = urllib.unquote_plus( params.get("thumbnail") )

    # Descarga la página
    data = scrapertools.cachePage(url)
    #logger.info(data)
    
    # Extrae las entradas (capítulos)
    patronvideos = '<location>([^<]+)</location>'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for match in matches:
        # Titulo
        scrapedtitle = title + " - [Directo]"
        # URL
        scrapedurl = match
        # Thumbnail
        scrapedthumbnail = thumbnail
        # Argumento
        scrapedplot = ""

        # Depuracion
        if (DEBUG):
            logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        # Añade al listado de XBMC
        xbmctools.addnewvideo( CHANNELNAME , "play" , category , "Directo" , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

    # Label (top-right)...
    xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
        
    # Disable sorting...
    xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )

    # End of directory...
    xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def play(params,url,category):
    logger.info("[ovasid.py] play")

    title = unicode( xbmc.getInfoLabel( "ListItem.Title" ), "utf-8" )
    thumbnail = urllib.unquote_plus( params.get("thumbnail") )
    plot = unicode( xbmc.getInfoLabel( "ListItem.Plot" ), "utf-8" )
    server = params["server"]
    
    xbmctools.playvideo(CHANNELNAME,server,url,category,title,thumbnail,plot)
