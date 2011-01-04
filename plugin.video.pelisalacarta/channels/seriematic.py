# -*- coding: utf-8 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para seriematic
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------
import urlparse,urllib2,urllib,re
import os, sys

import scrapertools
import servertools
import logger
import buscador
from item import Item

CHANNELNAME = "seriematic"
DEBUG = True

def isGeneric():
    return True

def mainlist(item):
    logger.info("[seriematic.py] mainlist")

    itemlist = []
    itemlist.append( Item(channel=CHANNELNAME, title="Series"       , action="series", url="http://www.seriematic.com/series.php"))
    itemlist.append( Item(channel=CHANNELNAME, title="Miniseries"   , action="series", url="http://www.seriematic.com/miniseries.php"))
    itemlist.append( Item(channel=CHANNELNAME, title="Dibujos"      , action="series", url="http://www.seriematic.com/dibujos.php"))
    itemlist.append( Item(channel=CHANNELNAME, title="Anime"        , action="series", url="http://www.seriematic.com/manga.php"))
    
    return itemlist

def series(item):
    logger.info("[seriematic.py] series")

    # Descarga la página
    data = scrapertools.cachePage(item.url)

    # Extrae las entradas
    '''
    <td><a href="1000_maneras_de_morir-5/">1000 Maneras de morir</a></td>
    '''

    patronvideos  = '<td><a href="([^"]+)">([^<]+)</a></td>'

    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    if DEBUG: scrapertools.printMatches(matches)

    itemlist = []
    for match in matches:
        scrapedtitle = match[1]
        scrapedplot = ""
        scrapedurl = urlparse.urljoin(item.url,match[0])
        scrapedthumbnail = ""
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        # Añade al listado de XBMC
        itemlist.append( Item(channel=CHANNELNAME, action="episodios", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

    return itemlist

def episodios(item):
    logger.info("[seriematic.py] episodios")

    # Descarga la página
    data = scrapertools.cachePage(item.url)

    # Extrae las entradas
    patronvideos  = '<\!-- Column 1 start -->(.*?)<\!-- Column 1 end -->'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    if DEBUG: scrapertools.printMatches(matches)

    itemlist = []
    for elemento in matches:
        patronvideos  = '<tr><td>([^<]+)<a href="([^"]+)">([^<]+)</a></td></tr>'
        matches2 = re.compile(patronvideos,re.DOTALL).findall(elemento)
        
        for match in matches2:
            scrapedtitle = match[0]+" "+match[2]
            scrapedplot = ""
            scrapedurl = urlparse.urljoin(item.url,match[1])
            scrapedthumbnail = ""
            if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")
    
            # Añade al listado de XBMC
            itemlist.append( Item(channel=CHANNELNAME, action="videos", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

    return itemlist

def videos(item):
    
    logger.info("[seriematic.py] videos")

    # Descarga la página
    data = scrapertools.cachePage(item.url)

    # Extrae las entradas
    patronvideos  = '<tr><td>[^<]+<a href="javascript:recomendar\(\'1\',\'([^\']+)\'[^<]+<img[^>]+>([^<]+)<img[^>]+>([^<]+)</a>.</td></tr>'

    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    if DEBUG: scrapertools.printMatches(matches)

    itemlist = []
    for match in matches:
        scrapedtitle = match[1]+" "+match[2]
        scrapedplot = ""
        scrapedurl = match[0]
        scrapedthumbnail = ""
        server="Megavideo"
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        # Añade al listado de XBMC
        itemlist.append( Item(channel=CHANNELNAME, action="play", title=scrapedtitle , url=scrapedurl , server=server , folder=False) )

    return itemlist
