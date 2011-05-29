# -*- coding: utf-8 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para serieonline.net
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

CHANNELNAME = "serieonline"
DEBUG = True

def isGeneric():
    return True

def mainlist(item):
    logger.info("[serieonline.py] mainlist")

    itemlist = []
    itemlist.append( Item(channel=CHANNELNAME, title="Novedades"    , action="novedades", url="http://www.serieonline.net/"))
    itemlist.append( Item(channel=CHANNELNAME, title="Series"       , action="series"   , url="http://www.serieonline.net/series/"))
    itemlist.append( Item(channel=CHANNELNAME, title="Películas"    , action="peliculas", url="http://www.serieonline.net/peliculas/"))
    itemlist.append( Item(channel=CHANNELNAME, title="Documentales" , action="peliculas", url="http://www.serieonline.net/documentales/"))
    
    return itemlist

def novedades(item):
    logger.info("[serieonline.py] novedades")

    # Descarga la página
    data = scrapertools.cachePage(item.url)

    # Extrae las entradas
    patronvideos  = '<a href="([^"]+)" title="([^"]+)"><img src="([^"]+)" alt="([^"]+)" class="captify" /></a>'

    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    if DEBUG: scrapertools.printMatches(matches)

    itemlist = []
    for match in matches:
        scrapedtitle = match[1] + " " + match[3]
        scrapedplot = ""
        scrapedurl = urlparse.urljoin(item.url,match[0])
        scrapedthumbnail = urlparse.urljoin(item.url,match[2])
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        # Añade al listado de XBMC
        itemlist.append( Item(channel=CHANNELNAME, action="findvideos", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

    # Extrae el paginador
    patronvideos  = '<div class="paginacion-num"><a href="([^"]+)">'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    if len(matches)>0:
        scrapedtitle = "Página siguiente"
        scrapedurl = urlparse.urljoin(item.url,matches[0])
        itemlist.append( Item(channel=CHANNELNAME, action="novedades", title=scrapedtitle , url=scrapedurl , folder=True) )

    return itemlist

def peliculas(item):
    logger.info("[serieonline.py] peliculas")

    # Descarga la página
    data = scrapertools.cachePage(item.url)

    # Extrae las entradas
    '''
    <div class="capitulo"><div class="imagen-text"><a href="http://www.serieonline.net/drama/el-retrato-de-dorian-gray-2009/"><img src="http://www.serieonline.net/imagenes/portada/pelis/elretratodedoriangray2009.jpg" width="150" height="230" alt="El retrato de Dorian Gray (2009)" /></a></div>
    '''
    patronvideos  = '<div class="capitulo"><div class="imagen-text"><a href="([^"]+)"><img src="([^"]+)".*?alt="([^"]+)"'

    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    if DEBUG: scrapertools.printMatches(matches)

    itemlist = []
    for match in matches:
        scrapedtitle = match[2]
        scrapedplot = ""
        scrapedurl = urlparse.urljoin(item.url,match[0])
        scrapedthumbnail = urlparse.urljoin(item.url,match[1])
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        # Añade al listado de XBMC
        itemlist.append( Item(channel=CHANNELNAME, action="findvideos", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

    # Extrae el paginador
    patronvideos  = '<div class="paginacion-num"><a href="([^"]+)">'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    if len(matches)>0:
        scrapedtitle = "Página siguiente"
        scrapedurl = urlparse.urljoin(item.url,matches[0])
        itemlist.append( Item(channel=CHANNELNAME, action="peliculas", title=scrapedtitle , url=scrapedurl , folder=True) )

    return itemlist

def series(item):
    logger.info("[serieonline.py] series")

    # Descarga la página
    data = scrapertools.cachePage(item.url)

    # Extrae las entradas
    '''
    <div class="series">
    <div class="mostrar-series-imagen">
    <a href="http://www.serieonline.net/90210/">
    <img src="http://www.serieonline.net/imagenes/90210.jpg" alt="90210" height="155" width="200" />
    </a>
    </div>
    <div class="mostrar-series-texto">
    <a href="http://www.serieonline.net/90210/">90210</a>
    
    </div>
    </div>
    '''

    patronvideos  = '<div class="series">[^<]+'
    patronvideos += '<div class="mostrar-series-imagen">[^<]+'
    patronvideos += '<a href="([^"]+)">[^<]+'
    patronvideos += '<img src="([^"]+)"[^<]+'
    patronvideos += '</a>[^<]+'
    patronvideos += '</div>[^<]+'
    patronvideos += '<div class="mostrar-series-texto">[^<]+'
    patronvideos += '<a href="[^>]+>([^<]+)</a>'

    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    if DEBUG: scrapertools.printMatches(matches)

    itemlist = []
    for match in matches:
        scrapedtitle = match[2]
        scrapedplot = ""
        scrapedurl = urlparse.urljoin(item.url,match[0])
        scrapedthumbnail = urlparse.urljoin(item.url,match[1])
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        # Añade al listado de XBMC
        itemlist.append( Item(channel=CHANNELNAME, action="episodios", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

    # Extrae el paginador
    patronvideos  = '<div class="paginacion-num"><a href="([^"]+)">'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    if len(matches)>0:
        scrapedtitle = "Página siguiente"
        scrapedurl = urlparse.urljoin(item.url,matches[0])
        itemlist.append( Item(channel=CHANNELNAME, action="series", title=scrapedtitle , url=scrapedurl , folder=True) )

    return itemlist


def episodios(item):
    logger.info("[serieonline.py] episodios")

    # Descarga la página
    data = scrapertools.cachePage(item.url)

    # Extrae las entradas
    patronvideos  = '<div class="serie">(.*?)</div>'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    if len(matches)>0:
        cuerpo = matches[0]
    else:
        cuerpo = ""

    patronvideos  = '<a href="([^"]+)">([^<]+)</a>'
    matches = re.compile(patronvideos,re.DOTALL).findall(cuerpo)

    itemlist = []
    for match in matches:
        scrapedtitle = match[1]
        scrapedplot = ""
        scrapedurl = urlparse.urljoin(item.url,match[0])
        scrapedthumbnail = item.thumbnail
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        # Añade al listado de XBMC
        itemlist.append( Item(channel=CHANNELNAME, action="findvideos", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

    return itemlist