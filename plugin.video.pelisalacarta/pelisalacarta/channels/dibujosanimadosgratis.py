# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para dibujosanimadosgratis
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

CHANNELNAME = "dibujosanimadosgratis"
DEBUG = True

def isGeneric():
    return True

def mainlist(item):
    logger.info("[cuevana.py] mainlist")

    itemlist = []
    itemlist.append( Item(channel=CHANNELNAME, title="Novedades"  , action="novedades" , url="http://dibujosanimadosgratis.net/"))
    itemlist.append( Item(channel=CHANNELNAME, title="Categorías" , action="categorias", url="http://dibujosanimadosgratis.net/"))
    
    return itemlist

def categorias(item):
    logger.info("[dibujosanimadosgratis.py] categorias")
    itemlist = []
    
    # Extrae las entradas
    data = scrapertools.cachePage(item.url)
    patron  = '<li class="cat-item cat-item[^"]+"><a href="([^"]+)" title="[^"]+">([^"]+)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for match in matches:
        scrapedtitle = match[1]
        scrapedurl = urlparse.urljoin(url,match[0])
        scrapedthumbnail = ""
        scrapedplot = ""
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")
        itemlist.append( Item(channel=CHANNELNAME, action="novedades", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

    return itemlist

def novedades(item):
    logger.info("[dibujosanimadosgratis.py] novedades")
    itemlist = []
    
    # Descarga la página
    data = scrapertools.cachePage(item.url)
    patron  = '<div class="post">[^<]+'
    patron += '<h2 class="postTitle"><a href="([^"]+)">([^<]+)</a></h2>(.*?)</div> <!-- Closes Post -->'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for match in matches:
        scrapedtitle = match[1]
        scrapedurl = urlparse.urljoin(item.url,match[0])
        scrapedthumbnail = ""
        patronthumb = '<img src="([^"]+)"'
        matchesthumb = re.compile(patronthumb,re.DOTALL).findall(match[2])
        if len(matchesthumb)>0:
            scrapedthumbnail = matchesthumb[0]
        scrapedplot = ""
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")
        itemlist.append( Item(channel=CHANNELNAME, action="findvideos", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

    patron  = '<a href="([^"]+)" >&laquo; videos anteriores'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
    if len(matches)>0:
        scrapedtitle = "!Página siguiente"
        scrapedurl = urlparse.urljoin(item.url,matches[0])
        scrapedthumbnail = ""
        scrapedplot = ""
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")
        itemlist.append( Item(channel=CHANNELNAME, action="novedades", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

    return itemlist
