# -*- coding: utf-8 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para seriesonline
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

CHANNELNAME = "seriesonline"

# Esto permite su ejecución en modo emulado
try:
    pluginhandle = int( sys.argv[ 1 ] )
except:
    pluginhandle = ""

logger.info("[seriesonline.py] init")

DEBUG = True

def mainlist(params,url,category):
    logger.info("[seriesonline.py] mainlist")

    import base64
    #decodeBase64('yFA/B6/fgVeTEKXqJsWqmGZuCQaVby9i6umE94Eies2OznsWeVCs9iEzpRfuZfK2xoF8Vj8TAGkbHv4IprauDzwV488pJoEzbndTne34hSMjMH8Apc4Z4Dssl3f8tD98StY3zGjGfkD53ErHTRELz9qcBamiKr+CDcs4ZB6d20rTKi6lseNyfMWKVw7EdLqCozywFTGwmzUQN2iCGyqEQoB2KDPdE8NNDaMn86jGKI8MhRxVNU+iwiSI6JwljACen0BIqzWRJwUIflaLfyQtgcVNnsstw3RbQIBDLxH8TBsn6eBLfIwqeNfHfywQiyw=')
    code = "yFA/B6/fgVeTEKXqJsWqmGZuCQaVby9i6umE94Eies2OznsWeVCs9iEzpRfuZfK2xoF8Vj8TAGkbHv4IprauDzwV488pJoEzbndTne34hSMjMH8Apc4Z4Dssl3f8tD98StY3zGjGfkD53ErHTRELz9qcBamiKr+CDcs4ZB6d20rTKi6lseNyfMWKVw7EdLqCozywFTGwmzUQN2iCGyqEQoB2KDPdE8NNDaMn86jGKI8MhRxVNU+iwiSI6JwljACen0BIqzWRJwUIflaLfyQtgcVNnsstw3RbQIBDLxH8TBsn6eBLfIwqeNfHfywQiyw="
    result = base64.b64decode(code)
    print "%s" % result

    # Añade al listado de XBMC
    xbmctools.addnewfolder( CHANNELNAME , "novedadeslist"      , "" , "Novedades","http://www.seriesonlinetv.com/","","")

    # Cierra el directorio
    xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
    xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def novedadeslist(params,url,category):
    logger.info("[seriesonline.py] mainlist")

    # Descarga la página
    data = scrapertools.cachePage(url)
    #logger.info(data)

    # Extrae las entradas (carpetas)
    patronvideos  = '<table class="titulo" id="naranja" cellpadding="0" cellspacing="0">[^<]+'
    patronvideos += '<tr>[^<]+'
    patronvideos += '<td width="7"><img src="/imagenes/menu_s_iz.gif" width="100." height="20" alt="" /></td>[^<]+'
    patronvideos += '<td class="tit">([^<]+)</td>[^<]+'
    patronvideos += '<td width="7"><img src="/imagenes/menu_s_de.gif" width="100." height="20" alt="" /></td>[^<]+'
    patronvideos += '</tr>[^<]+'
    patronvideos += '</table>[^<]+'
    patronvideos += '<table class="titulo" id="naranja" cellpadding="0" cellspacing="0">[^<]+'
    patronvideos += '<tr>[^<]+'
    patronvideos += '<td class="contenido"> <div style="min-height. 150px."><a href="([^"]+)">[^<]+'
    patronvideos += '<a href="([^"]+)"><img src="([^"]+)'
            
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for match in matches:
        scrapedtitle = match[0].strip()
        scrapedurl = urlparse.urljoin(url,match[1])
        scrapedthumbnail = urlparse.urljoin(url,match[3])
        scrapeddescription = ""
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        # Añade al listado de XBMC
        xbmctools.addnewfolder( CHANNELNAME , "list" , CHANNELNAME , scrapedtitle , scrapedurl , scrapedthumbnail , scrapeddescription )

    # Paginación
    patron = '<a href="([^"]+)" class="paginacion"[^>]+>\&gt\;\&gt\;</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    if len(matches)>0:
        scrapedurl = urlparse.urljoin(url,matches[0])
        xbmctools.addnewfolder( CHANNELNAME , "novedadeslist" , CHANNELNAME , "Página siguiente" , scrapedurl , "" , "" )

    # Label (top-right)...
    xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
    xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def list(params,url,category):
    logger.info("[seriesonline.py] list")

    title = urllib.unquote_plus( params.get("title") )
    thumbnail = urllib.unquote_plus( params.get("thumbnail") )

    # Descarga la página
    data = scrapertools.cachePage(url)
    #logger.info(data)

    # Extrae las entradas
    patronvideos  = '<a.*?href="(/serie-divx/[^"]+)"'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for match in matches:
        scrapedtitle = title + "(Ver online)"
        scrapedurl = urlparse.urljoin( url , match )
        scrapedthumbnail = thumbnail
        scrapeddescription = ""
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        # Añade al listado de XBMC
        xbmctools.addnewfolder( CHANNELNAME , "detail" , CHANNELNAME , scrapedtitle , scrapedurl , scrapedthumbnail , scrapeddescription )

    # Extrae las entradas
    patronvideos  = '<a.*?href="(/descarga-directa/[^"]+)"'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for match in matches:
        scrapedtitle = title + "(Descarga directa)"
        scrapedurl = urlparse.urljoin( url , match )
        scrapedthumbnail = thumbnail
        scrapeddescription = ""
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        # Añade al listado de XBMC
        xbmctools.addnewfolder( CHANNELNAME , "detail" , CHANNELNAME , scrapedtitle , scrapedurl , scrapedthumbnail , scrapeddescription )

    # Label (top-right)...
    xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
    xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def detail(params,url,category):
    logger.info("[seriesonline.py] detail")

    title = urllib.unquote_plus( params.get("title") )
    thumbnail = urllib.unquote_plus( params.get("thumbnail") )

    # Descarga la página
    data = scrapertools.cachePage(url)
    #logger.info(data)

    # ------------------------------------------------------------------------------------
    # Busca los enlaces a los mirrors, o a los capítulos de las series...
    # ------------------------------------------------------------------------------------

    logger.info("Busca el enlace de página siguiente...")
    try:
        # La siguiente página
        patronvideos  = '<a href="([^"]+)">Sigu'
        matches = re.compile(patronvideos,re.DOTALL).findall(data)
        for match in matches:
            addfolder("#Siguiente",urlparse.urljoin(url,match),"list")
    except:
        logger.info("No encuentro la pagina...")

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
    logger.info("[seriesonline.py] play")

    title = unicode( xbmc.getInfoLabel( "ListItem.Title" ), "utf-8" )
    thumbnail = xbmc.getInfoImage( "ListItem.Thumb" )
    plot = unicode( xbmc.getInfoLabel( "ListItem.Plot" ), "utf-8" )
    server = params["server"]
    logger.info("[seriesonline.py] thumbnail="+thumbnail)
    logger.info("[seriesonline.py] server="+server)
    
    xbmctools.playvideo(CHANNELNAME,server,url,category,title,thumbnail,plot)

def addfolder(nombre,url,accion):
    logger.info('[seriesonline.py] addfolder( "'+nombre+'" , "' + url + '" , "'+accion+'")"')
    listitem = xbmcgui.ListItem( nombre , iconImage="DefaultFolder.png")
    itemurl = '%s?channel=seriesonline&action=%s&category=%s&url=%s' % ( sys.argv[ 0 ] , accion , urllib.quote_plus(nombre) , urllib.quote_plus(url) )
    xbmcplugin.addDirectoryItem( handle = int(sys.argv[ 1 ]), url = itemurl , listitem=listitem, isFolder=True)

def addvideo(nombre,url,category,server):
    logger.info('[seriesonline.py] addvideo( "'+nombre+'" , "' + url + '" , "'+server+'")"')
    listitem = xbmcgui.ListItem( nombre, iconImage="DefaultVideo.png" )
    listitem.setInfo( "video", { "Title" : nombre, "Plot" : nombre } )
    itemurl = '%s?channel=seriesonline&action=play&category=%s&url=%s&server=%s' % ( sys.argv[ 0 ] , category , urllib.quote_plus(url) , server )
    xbmcplugin.addDirectoryItem( handle=int(sys.argv[ 1 ]), url=itemurl, listitem=listitem, isFolder=False)

def addthumbnailfolder( scrapedtitle , scrapedurl , scrapedthumbnail , accion ):
    logger.info('[seriesonline.py] addthumbnailfolder( "'+scrapedtitle+'" , "' + scrapedurl + '" , "'+scrapedthumbnail+'" , "'+accion+'")"')
    listitem = xbmcgui.ListItem( scrapedtitle, iconImage="DefaultFolder.png", thumbnailImage=scrapedthumbnail )
    itemurl = '%s?channel=seriesonline&action=%s&category=%s&url=%s' % ( sys.argv[ 0 ] , accion , urllib.quote_plus( scrapedtitle ) , urllib.quote_plus( scrapedurl ) )
    xbmcplugin.addDirectoryItem( handle = int(sys.argv[ 1 ]), url = itemurl , listitem=listitem, isFolder=True)
