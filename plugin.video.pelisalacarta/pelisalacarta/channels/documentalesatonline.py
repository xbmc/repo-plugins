# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para documentalesatonline
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------
# Nota: Esta web ha dejado de actualizarse, ahora está en el canal documentalesatonline2
import urlparse,urllib2,urllib,re
import os, sys

from core import scrapertools
from core import config
from core import logger
from core import xbmctools
from core.item import Item
from servers import servertools
from servers import vk

from pelisalacarta import buscador

CHANNELNAME = "documentalesatonline"
DEBUG = True

def isGeneric():
    return True

def mainlist(item):
    logger.info("[documentalesatonline.py] mainlist")
    
    itemlist = []
    itemlist.append( Item(channel=CHANNELNAME, action="novedades"  , title="Novedades"     ,url="http://documentalesatonline.blogspot.com/"))
    itemlist.append( Item(channel=CHANNELNAME, action="categorias" , title="Por categorias",url="http://documentalesatonline.blogspot.com/"))

    return itemlist

def categorias(item):
    logger.info("[documentalesatonline.py] novedades")

    # Descarga la página
    data = scrapertools.cachePage(item.url)
    #logger.info(data)

    # Extrae las entradas (carpetas)
    patronvideos  = "<a dir='ltr' href='([^']+)'>([^<]+)</a>[^<]+<span dir='ltr'>([^<]+)</span>"
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    itemlist = []

    for match in matches:
        scrapedtitle = match[1]+" "+match[2]
        scrapedurl = urlparse.urljoin(item.url,match[0])
        scrapedthumbnail = ""
        scrapedplot = ""
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        itemlist.append( Item(channel=CHANNELNAME, action="novedades" , title=scrapedtitle , url=scrapedurl, thumbnail=scrapedthumbnail, plot=scrapedplot))

    return itemlist

def novedades(item):
    logger.info("[documentalesatonline.py] novedades")

    # Descarga la página
    data = scrapertools.cachePage(item.url)
    #logger.info(data)

    # Extrae las entradas (carpetas)
    patronvideos  = "<div class='post hentry'>.*?"
    patronvideos += "<h3 class='post-title entry-title'>[^<]+"
    patronvideos += "<a href='([^']+)'>([^<]+)</a>.*?"
    patronvideos += '<img.*?src="([^"]+)"[^>]+>(.*?)<div'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    itemlist = []

    for match in matches:
        scrapedtitle = match[1]
        scrapedurl = urlparse.urljoin(item.url,match[0])
        scrapedthumbnail = match[2]
        scrapedplot = scrapertools.htmlclean(match[3])
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        itemlist.append( Item(channel=CHANNELNAME, action="findvideos" , title=scrapedtitle , url=scrapedurl, thumbnail=scrapedthumbnail, plot=scrapedplot))

    # Página siguiente
    patronvideos  = "<a class='blog-pager-older-link' href='([^']+)' id='Blog1_blog-pager-older-link' title='Entradas antiguas'>Entradas antiguas</a>"
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for match in matches:
        scrapedtitle = "Página siguiente"
        scrapedurl = urlparse.urljoin(item.url,match)
        scrapedthumbnail = ""
        scrapedplot = ""
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        itemlist.append( Item(channel=CHANNELNAME, action="novedades" , title=scrapedtitle , url=scrapedurl, thumbnail=scrapedthumbnail, plot=scrapedplot))

    return itemlist
