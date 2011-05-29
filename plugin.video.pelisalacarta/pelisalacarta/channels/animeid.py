# -*- coding: utf-8 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para animeid
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------
import urlparse,urllib2,urllib,re
import os, sys

try:
    from core import logger
    from core import config
    from core import scrapertools
    from core.item import Item
    from servers import servertools
except:
    # En Plex Media server lo anterior no funciona...
    from Code.core import logger
    from Code.core import config
    from Code.core import scrapertools
    from Code.core.item import Item

CHANNELNAME = "animeid"
DEBUG = True

def isGeneric():
    return True

def mainlist(item):
    logger.info("[animeid.py] mainlist")
    
    itemlist = []
    itemlist.append( Item(channel=CHANNELNAME, action="destacados" , title="Destacados"               , url="http://animeid.com/" ))
    
    itemlist.append( Item(channel=CHANNELNAME, action="newlist"   , title="Últimas series agregadas" , url="http://animeid.com/" ))
    itemlist.append( Item(channel=CHANNELNAME, action="chaplist"  , title="Últimos capítulos"        , url="http://animeid.com/" ))
    itemlist.append( Item(channel=CHANNELNAME, action="animelist" , title="Últimos animes agregados" , url="http://animeid.com/" ))
    itemlist.append( Item(channel=CHANNELNAME, action="airlist"   , title="Series en emisión"        , url="http://animeid.com/" ))
    itemlist.append( Item(channel=CHANNELNAME, action="fulllist"  , title="Lista completa de animes" , url="http://animeid.com/" ))
    #itemlist.append( Item(channel=CHANNELNAME, action="genrelist" , title="Listado por genero"       , url="http://animeid.com/" ))
    #itemlist.append( Item(channel=CHANNELNAME, action="alphalist" , title="Listado alfabetico"       , url="http://animeid.com/" ))

    return itemlist

def fulllist(item):
    logger.info("[animeid.py] airlist")

    if config.get_setting("forceview")=="true" and config.get_platform()=="xbmcdharma":
        logger.info("Forzando vista")
        import xbmc
        # Confluence: 50,51,550,560,500,501,508,505
        #xbmc.executebuiltin("Container.SetViewMode(550)")  #53=mediainfo

    # Descarga la pagina
    data = scrapertools.cache_page(item.url)

    # Extrae las entradas (carpetas)  <a class="accion linkFader" href="../accion-1.html"></a>
    #<div class="dt">Ultimos Animes Agregados</div> <div class="dm"> <ul> <li><a href="/anime/mobile-suit-gundam-wing.html" title="Mobile Suit Gundam Wing" class="anime">Mobile Suit Gundam
    patronvideos  = '<div class="dt">Lista completa de animes</div> <div class="dm"(.*?)</div>'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    if len(matches)>0:
        data = matches[0]
        patronvideos = '<li><a href="([^"]+)" title="([^"]+)"'
        matches = re.compile(patronvideos,re.DOTALL).findall(data)
    
    itemlist = []
    
    for match in matches:
        scrapedtitle = match[1]
        scrapedurl = urlparse.urljoin(item.url,match[0])
        scrapedthumbnail = ""
        scrapedplot = ""
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        itemlist.append( Item(channel=CHANNELNAME, action="serie" , title=scrapedtitle , url=scrapedurl, thumbnail=scrapedthumbnail, plot=scrapedplot))

    return itemlist

def airlist(item):
    logger.info("[animeid.py] airlist")

    if config.get_setting("forceview")=="true" and config.get_platform()=="xbmcdharma":
        logger.info("Forzando vista")
        import xbmc
        # Confluence: 50,51,550,560,500,501,508,505
        #xbmc.executebuiltin("Container.SetViewMode(550)")  #53=mediainfo

    # Descarga la pagina
    data = scrapertools.cache_page(item.url)

    # Extrae las entradas (carpetas)  <a class="accion linkFader" href="../accion-1.html"></a>
    #<div class="dt">Ultimos Animes Agregados</div> <div class="dm"> <ul> <li><a href="/anime/mobile-suit-gundam-wing.html" title="Mobile Suit Gundam Wing" class="anime">Mobile Suit Gundam
    patronvideos  = '<div class="dt">Series en Emisi\&oacute\;n</div> <div class="dm">(.*?)</div>'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    if len(matches)>0:
        data = matches[0]
        patronvideos = '<li><a href="([^"]+)" title="([^"]+)"'
        matches = re.compile(patronvideos,re.DOTALL).findall(data)
    
    itemlist = []
    
    for match in matches:
        scrapedtitle = match[1]
        scrapedurl = urlparse.urljoin(item.url,match[0])
        scrapedthumbnail = ""
        scrapedplot = ""
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        itemlist.append( Item(channel=CHANNELNAME, action="serie" , title=scrapedtitle , url=scrapedurl, thumbnail=scrapedthumbnail, plot=scrapedplot))

    return itemlist

def animelist(item):
    logger.info("[animeid.py] animelist")

    if config.get_setting("forceview")=="true" and config.get_platform()=="xbmcdharma":
        logger.info("Forzando vista")
        import xbmc
        # Confluence: 50,51,550,560,500,501,508,505
        #xbmc.executebuiltin("Container.SetViewMode(550)")  #53=mediainfo

    # Descarga la pagina
    data = scrapertools.cache_page(item.url)

    # Extrae las entradas (carpetas)  <a class="accion linkFader" href="../accion-1.html"></a>
    #<div class="dt">Ultimos Animes Agregados</div> <div class="dm"> <ul> <li><a href="/anime/mobile-suit-gundam-wing.html" title="Mobile Suit Gundam Wing" class="anime">Mobile Suit Gundam
    patronvideos  = '<div class="dt">Ultimos Animes Agregados</div> <div class="dm">(.*?)</div>'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    if len(matches)>0:
        data = matches[0]
        patronvideos = '<li><a href="([^"]+)" title="([^"]+)"'
        matches = re.compile(patronvideos,re.DOTALL).findall(data)
    
    itemlist = []
    
    for match in matches:
        scrapedtitle = match[1]
        scrapedurl = urlparse.urljoin(item.url,match[0])
        scrapedthumbnail = ""
        scrapedplot = ""
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        itemlist.append( Item(channel=CHANNELNAME, action="serie" , title=scrapedtitle , url=scrapedurl, thumbnail=scrapedthumbnail, plot=scrapedplot))

    return itemlist

def chaplist(item):
    logger.info("[animeid.py] chaplist")

    if config.get_setting("forceview")=="true" and config.get_platform()=="xbmcdharma":
        logger.info("Forzando vista")
        import xbmc
        # Confluence: 50,51,550,560,500,501,508,505
        #xbmc.executebuiltin("Container.SetViewMode(550)")  #53=mediainfo

    # Descarga la pagina
    data = scrapertools.cache_page(item.url)

    # Extrae las entradas (carpetas)  <a class="accion linkFader" href="../accion-1.html"></a>
    #<div class="a"> <a href="/ver/dragon-ball-kai-94.html" title="Dragon Ball Kai 94"><img src="http://img.animeid.com/dbk.jpg" alt="Dragon Ball Kai" width="49" height="71" border="0" /></a> <div class="at"><a href="/ver/dragon-ball-kai-94.html" title="Dragon Ball Kai 94">Dragon Ball Kai 94</a></div> <div class="at" style="margin-top:0px"><span>Publicado: 21/02/2011</span></div> <div class="ad">Despu�s de los rumores que llevaban tiempo apuntando a que se realizar�a una nueva serie de Dra&hellip;</div> </div>
    patronvideos  = '<div class="a"> <a href="([^"]+)" title="([^"]+)"><img src="([^"]+)"'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    itemlist = []
    
    for match in matches:
        scrapedtitle = match[1]
        scrapedurl = urlparse.urljoin(item.url,match[0])
        scrapedthumbnail = match[2]
        scrapedplot = ""
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        itemlist.append( Item(channel=CHANNELNAME, action="findvideos" , title=scrapedtitle , url=scrapedurl, thumbnail=scrapedthumbnail, plot=scrapedplot))

    return itemlist


def newlist(item):
    logger.info("[animeid.py] newlist")

    if config.get_setting("forceview")=="true" and config.get_platform()=="xbmcdharma":
        logger.info("Forzando vista")
        import xbmc
        # Confluence: 50,51,550,560,500,501,508,505
        #xbmc.executebuiltin("Container.SetViewMode(550)")  #53=mediainfo

    # Descarga la pagina
    data = scrapertools.cache_page(item.url)

    # Extrae las entradas (carpetas)  <a class="accion linkFader" href="../accion-1.html"></a>
    # <div class="bl"> <a href="/anime/mobile-suit-gundam-wing.html" title="Mobile Suit Gundam Wing"><img src="http://img.animeid.com/mobilesuitgundam.gif" alt="Mobile Suit Gundam Wing" width="166" height="250" border="0" class="im" /></a> <div class="tt"> <h1><a href="/anime/mobile-suit-gundam-wing.html" title="Mobile Suit Gundam Wing">Mobile Suit Gundam Win&hellip;</a></h1></div> </div>
    patronvideos  = '<div class="bl"> <a href="([^"]+)" title="([^"]+)"><img src="([^"]+)"'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    itemlist = []
    
    for match in matches:
        scrapedtitle = match[1]
        scrapedurl = urlparse.urljoin(item.url,match[0])
        scrapedthumbnail = match[2]
        scrapedplot = ""
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        itemlist.append( Item(channel=CHANNELNAME, action="serie" , title=scrapedtitle , url=scrapedurl, thumbnail=scrapedthumbnail, plot=scrapedplot))

    return itemlist

def destacados(item):
    logger.info("[animeid.py] destacados")

    if config.get_setting("forceview")=="true" and config.get_platform()=="xbmcdharma":
        logger.info("Forzando vista")
        import xbmc
        # Confluence: 50,51,550,560,500,501,508,505
        #xbmc.executebuiltin("Container.SetViewMode(550)")  #53=mediainfo

    # Descarga la pagina
    data = scrapertools.cache_page(item.url)

    # Extrae las entradas (carpetas)  <a class="accion linkFader" href="../accion-1.html"></a>
    patronvideos  = "\$\('w_fss'\).slideshow \= new FeaturedSlideshow\(\[(.*?)\]\)\;"
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    
    if len(matches)>0:
        data = matches[0]

        patronvideos  = '\{"series_name"\:"([^"]+)"\,"media_name"\:"([^"]+)"\,"description"\:"([^"]+)"\,"image"\:"([^"]+)","url":"([^"]+)".*?\}'
        scrapertools.printMatches(matches)
        matches = re.compile(patronvideos,re.DOTALL).findall(data)

    itemlist = []
    
    for match in matches:
        scrapedtitle = match[0]+" "+match[1]
        scrapedurl = urlparse.urljoin(item.url,match[4])
        scrapedthumbnail = match[3].replace("\\/","/")
        scrapedplot = match[2]
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        itemlist.append( Item(channel=CHANNELNAME, action="serie" , title=scrapedtitle , url=scrapedurl, thumbnail=scrapedthumbnail, plot=scrapedplot))

    return itemlist

def serie(item):
    logger.info("[animeid.py] serie")

    # Descarga la pagina
    data = scrapertools.cache_page(item.url)

    # Saca el argumento
    patronvideos  = '<div class="sinop">(.*?)</div>'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    
    if len(matches)>0:
        scrapedplot = scrapertools.htmlclean( matches[0] )
    
    # Saca enlaces a los episodios
    patronvideos  = '<li class="lcc"><a href="([^"]+)" class="lcc">([^<]+)</a></li>'
    scrapertools.printMatches(matches)
    matches = re.compile(patronvideos,re.DOTALL).findall(data)

    itemlist = []
    
    for match in matches:
        scrapedtitle = scrapertools.entityunescape( match[1] )
        scrapedurl = urlparse.urljoin(item.url,match[0])
        scrapedthumbnail = item.thumbnail
        #scrapedplot = match[2]
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        itemlist.append( Item(channel=CHANNELNAME, action="findvideos" , title=scrapedtitle , url=scrapedurl, thumbnail=scrapedthumbnail, plot=scrapedplot))

    return itemlist
