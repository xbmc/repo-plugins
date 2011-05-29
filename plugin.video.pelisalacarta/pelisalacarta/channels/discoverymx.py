# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para discoverymx
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------
import urlparse,urllib2,urllib,re
import os
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
from servers import youtube

from pelisalacarta import buscador

CHANNELNAME = "discoverymx"

# Esto permite su ejecución en modo emulado
try:
    pluginhandle = int( sys.argv[ 1 ] )
except:
    pluginhandle = ""

# Traza el inicio del canal
logger.info("[discoverymx.py] init")

DEBUG = True

def mainlist(params,url,category):
    logger.info("[discoverymx.py] mainlist")

    # Añade al listado de XBMC
    xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , "Documentales - Novedades"            ,"http://discoverymx.blogspot.com/","","")
    #xbmctools.addnewfolder( CHANNELNAME , "DocuCat"    , category , "Documentales - Lista por categorías" ,"http://discoverymx.blogspot.com/","","")
    xbmctools.addnewfolder( CHANNELNAME , "DocuSeries" , category , "Documentales - Series Disponibles" ,"http://discoverymx.blogspot.com/","","")
    xbmctools.addnewfolder( CHANNELNAME , "DocuTag"    , category , "Documentales - Tag" ,"http://discoverymx.blogspot.com/","","")
    xbmctools.addnewfolder( CHANNELNAME , "DocuARCHIVO", category , "Documentales - Archivo" ,"http://discoverymx.blogspot.com/","","")
    #xbmctools.addnewfolder( CHANNELNAME , "search"     , category , "Buscar"                           ,"","","")

    # Propiedades
    xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
    xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def search(params,url,category):
    logger.info("[discoverymx.py] search")

    keyboard = xbmc.Keyboard('')
    keyboard.doModal()
    if (keyboard.isConfirmed()):
        tecleado = keyboard.getText()
        if len(tecleado)>0:
            #convert to HTML
            tecleado = tecleado.replace(" ", "+")
            searchUrl = "http://discoverymx.blogspot.com/index.php?s="+tecleado
            SearchResult(params,searchUrl,category)
            
def SearchResult(params,url,category):
    logger.info("[discoverymx.py] SearchResult")
    
    # Descarga la página
    data = scrapertools.cachePage(url)

    # Extrae las entradas (carpetas)
    patronvideos  = '<p class="entry-title"><[^>]+>[^<]+</span><a href="([^"]+)"[^>]+>([^<]+)</a></p>'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for match in matches:
        # Atributos
        scrapedurl = match[0]
        
        scrapedtitle =match[1]
        scrapedtitle = scrapedtitle.replace("&#8211;","-")
        scrapedtitle = scrapedtitle.replace("&nbsp;"," ")
        scrapedthumbnail = ""
        scrapedplot = ""
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        # Añade al listado de XBMC
        xbmctools.addnewfolder( CHANNELNAME , "detail" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

    # Propiedades
    xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
    xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )
        

def performsearch(texto):
    logger.info("[discoverymx.py] performsearch")
    url = "http://discoverymx.blogspot.com/index.php?s="+texto

    # Descarga la página
    data = scrapertools.cachePage(url)

    # Extrae las entradas (carpetas)
    patronvideos  = '<p class="entry-title"><[^>]+>[^<]+</span><a href="([^"]+)"[^>]+>([^<]+)</a></p>'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    resultados = []

    for match in matches:
        scrapedtitle = match[1]
        scrapedtitle = scrapedtitle.replace("&#8211;","-")
        scrapedtitle = scrapedtitle.replace("&nbsp;"," ")
        scrapedurl = match[0]
        scrapedthumbnail = ""
        scrapedplot = ""

        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        # Añade al listado de XBMC
        resultados.append( [CHANNELNAME , "detail" , "buscador" , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot ] )
        
    return resultados
def DocuSeries(params,url,category):
    logger.info("[discoverymx.py] DocuSeries")
    
    # Descarga la página
    data = scrapertools.cachePage(url)

    # Extrae las entradas (carpetas)
    patronvideos  = '<li><b><a href="([^"]+)" target="_blank">([^<]+)</a></b></li>'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for match in matches:
        # Atributos
        scrapedurl = match[0]
        
        scrapedtitle = match[1]
        
        scrapedthumbnail = ""
        scrapedplot = ""
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        # Añade al listado de XBMC
        xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

    # Propiedades
    xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
    xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )


def DocuTag(params,url,category):
    logger.info("[discoverymx.py] DocuSeries")
    
    # Descarga la página
    data = scrapertools.cachePage(url)

    # Extrae las entradas (carpetas)
    patronvideos  =    "<a dir='ltr' href='([^']+)'>([^<]+)</a>[^<]+<span class='label-count' dir='ltr'>(.+?)</span>"
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for match in matches:
        # Atributos
        scrapedurl = match[0]
        scrapedtitle = match[1] + " " + match[2]
        scrapedthumbnail = ""
        scrapedplot = ""
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        # Añade al listado de XBMC
        xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

    # Propiedades
    xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
    xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def DocuARCHIVO(params,url,category):
    logger.info("[discoverymx.py] DocuSeries")
    
    # Descarga la página
    data = scrapertools.cachePage(url)

    # Extrae las entradas (carpetas)
    patronvideos  =    "<a class='post-count-link' href='([^']+)'>([^<]+)</a>[^<]+"
    patronvideos +=    "<span class='post-count' dir='ltr'>(.+?)</span>"
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for match in matches:
        # Atributos
        scrapedurl = match[0]
        scrapedtitle = match[1] + " " + match[2]
        scrapedthumbnail = ""
        scrapedplot = ""
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        # Añade al listado de XBMC
        xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

    # Propiedades
    xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
    xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

    
def DocuCat(params,url,category):
    logger.info("[discoverymx.py] peliscat")

    # Descarga la página
    data = scrapertools.cachePage(url)

    # Extrae las entradas (carpetas)
    patronvideos  = '<li class="cat-item cat-item[^"]+"><a href="([^"]+)" title="[^"]+">([^<]+)</a>'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for match in matches:
        # Atributos
        scrapedtitle = match[1]
        scrapedurl = match[0]
        scrapedthumbnail = ""
        scrapedplot = ""
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        # Añade al listado de XBMC
        xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

    # Propiedades
    xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
    xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def listvideos(params,url,category):
    logger.info("[discoverymx.py] listvideos")
    
    scrapedthumbnail = ""
    scrapedplot = ""
    # Descarga la página
    data = scrapertools.cachePage(url)
    #logger.info(data)

    # Extrae las entradas (carpetas)
    patronvideos  = "<h3 class='post-title entry-title'>[^<]+"
    patronvideos += "<a href='([^']+)'>([^<]+)</a>.*?"
    patronvideos += "<div class='post-body entry-content'>(.*?)<div class='post-footer'>"
    
    
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for match in matches:
        scrapedtitle = match[1]
        scrapedtitle = re.sub("<[^>]+>"," ",scrapedtitle)
        scrapedtitle = scrapertools.unescape(scrapedtitle)
        scrapedurl = match[0]
        regexp = re.compile(r'src="(http[^"]+)"')
        matchthumb = regexp.search(match[2])
        if matchthumb is not None:
            scrapedthumbnail = matchthumb.group(1)
        matchplot = re.compile('<div align="center">(<img.*?)</span></div>',re.DOTALL).findall(match[2])
        if len(matchplot)>0:
            scrapedplot = matchplot[0]
            #print matchplot
        else:
            scrapedplot = ""
        scrapedplot = re.sub("<[^>]+>"," ",scrapedplot)
        scrapedplot = scrapertools.unescape(scrapedplot)


        #scrapedplot = scrapedplot.replace("â€¦","")
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        # Añade al listado de XBMC
        xbmctools.addnewfolder( CHANNELNAME , "detail" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

    # Extrae la marca de siguiente página
    patronvideos = "<a class='blog-pager-older-link' href='([^']+)'"
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    if len(matches)>0:
        scrapedtitle = "Página siguiente"
        scrapedurl = urlparse.urljoin(url,matches[0])
        scrapedthumbnail = ""
        scrapedplot = ""
        xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

    # Propiedades
    xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
    xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def detail(params,url,category):
    logger.info("[discoverymx.py] detail")

    title = urllib.unquote_plus( params.get("title") )
    thumbnail = urllib.unquote_plus( params.get("thumbnail") )
    plot = urllib.unquote_plus( params.get("plot") )

    # Descarga la página
    data = scrapertools.cachePage(url)
    #logger.info(data)

    # ------------------------------------------------------------------------------------
    # Busca los enlaces a videos no megavideo (youtube)
    # ------------------------------------------------------------------------------------
    patronyoutube = '<a href="http\:\/\/www.youtube.com/watch\?v=[^=]+=PlayList\&amp\;p=(.+?)&[^"]+"'
    matchyoutube  = re.compile(patronyoutube,re.DOTALL).findall(data)
    if len(matchyoutube)>0:
        for match in matchyoutube:
            listyoutubeurl = 'http://www.youtube.com/view_play_list?p='+match
            data1 = scrapertools.cachePage(listyoutubeurl)
            newpatronyoutube = '<a href="(.*?)".*?<img src="(.*?)".*?alt="([^"]+)"'
            matchnewyoutube  = re.compile(newpatronyoutube,re.DOTALL).findall(data1)
            if len(matchnewyoutube)>0:
                for match2 in matchnewyoutube:
                    scrapedthumbnail = match2[1]
                    scrapedtitle     = match2[2]
                    scrapedurl       = match2[0]
                    if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")
                    xbmctools.addnewvideo( CHANNELNAME , "play" , category , "youtube" , scrapedtitle +" - "+"(youtube) ", scrapedurl , scrapedthumbnail , plot )
                logger.info(" lista de links encontrados U "+str(len(matchnewyoutube)))
#-------------------------------------------------------------------------------
#<a href="http://www.youtube.com/watch?v=je-692ngMY0" target="_blank">parte 1</a>
    patronyoutube = '<a href="(http://www.youtube.com/watch\?v\=[^"]+)".*?>(.*?)</a>'
    matchyoutube  = re.compile(patronyoutube,re.DOTALL).findall(data)
    if len(matchyoutube)>0: 
        for match in matchyoutube:
            if "PlayList" not in match[0]:
                scrapedtitle = match[1]
                scrapedtitle = re.sub("<[^>]+>"," ",scrapedtitle)
                scrapedurl   = match[0]
                if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")
                xbmctools.addnewvideo( CHANNELNAME , "play" , category , "youtube" , scrapedtitle +" - "+"(youtube) ", scrapedurl , thumbnail , plot )
    else:
        patronyoutube = "<param name='movie' value='(http://www.youtube.com/v/[^']+)'"
        matchyoutube  = re.compile(patronyoutube,re.DOTALL).findall(data)
        parte = 0
        for match in matchyoutube:
            parte = parte + 1
            scrapedurl   = match
            scrapedtitle = title
            scrapedthumbnail = thumbnail
            re.compile(patronyoutube,re.DOTALL).findall(data)
            xbmctools.addnewvideo( CHANNELNAME , "play" , category , "youtube" , scrapedtitle +" - "+str(parte)+" (youtube) ", scrapedurl , scrapedthumbnail , plot )
    # ------------------------------------------------------------------------------------
    # Busca los enlaces a los videos
    # ------------------------------------------------------------------------------------
    listavideos = servertools.findvideos(data)

    for video in listavideos:
        videotitle = scrapertools.unescape(video[0])
        url = video[1]
        server = video[2]
        xbmctools.addnewvideo( CHANNELNAME , "play" , category , server , title.strip() + " - " + videotitle , url , thumbnail , plot )
    # ------------------------------------------------------------------------------------
    '''
    patronvideos = '(http://www.zshare.net/download/[^"]+)"'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    for match in matches:
        import zshare
        scrapedurl = zshare.geturl(match).replace(" ","%20")
        scrapedtitle = title
        re.compile(patronyoutube,re.DOTALL).findall(data)
        xbmctools.addnewvideo( CHANNELNAME , "play" , category , "Directo" , scrapedtitle +" - "+"(Zshare) ", scrapedurl , thumbnail , plot )
    '''
    # Label (top-right)...
    xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
        
    # Disable sorting...
    xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )

    # End of directory...
    xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def play(params,url,category):
    logger.info("[discoverymx.py] play")

    title = unicode( xbmc.getInfoLabel( "ListItem.Title" ), "utf-8" )
    thumbnail = urllib.unquote_plus( params.get("thumbnail") )
    plot = unicode( xbmc.getInfoLabel( "ListItem.Plot" ), "utf-8" )
    server = params["server"]
    
    xbmctools.playvideo(CHANNELNAME,server,url,category,title,thumbnail,plot)

def youtubeplay(params,url,category):
    logger.info("[dospuntocerovision.py] youtubeplay")
    if "www.youtube" not in url:
        url  = 'http://www.youtube.com'+url
 

    title = urllib.unquote_plus( params.get("title") )
    thumbnail = urllib.unquote_plus( params.get("thumbnail") )
    plot = "Ver Video"
    server = "Directo"
    id = youtube.Extract_id(url)
    videourl = youtube.geturl(id)
    
    if len(videourl)>0:
        logger.info("link directo de youtube : "+videourl)
        xbmctools.playvideo("Trailer",server,videourl,category,title,thumbnail,plot)
    
    return
