# -*- coding: utf-8 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para robinfilm
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------
import urlparse,urllib2,urllib,re
import os, sys

from core import logger
from core import config
from core import scrapertools
from core.item import Item
from servers import servertools

CHANNELNAME = "robinfilm"
DEBUG = True

def isGeneric():
    return True

def mainlist(item):
    logger.info("[robinfilm.py] mainlist")
    item.url = "http://www.robinfilm.com/"
    return novedades(item)

def novedades(item):
    logger.info("[robinfilm.py] novedades")

    # Descarga la página
    data = scrapertools.cachePage(item.url)
    '''
    <div id='post-title-wrapper'>
    <a name='7524788762119126886'></a>
    <h3 class='post-title entry-title'>
    <a href='http://www.robinfilm.com/2011/05/uomini-senza-legge-2011.html'>Uomini Senza Legge (2011)</a>
    </h3>
    .*?
    <img alt="http://mr.comingsoon.it/imgdb/locandine/big/48020.jpg" height="400" src="http://mr.comingsoon.it/imgdb/locandine/big/48020.jpg" width="280" />
    '''
    patronvideos  = "<div id='post-title-wrapper'>[^<]+"
    patronvideos += "<a[^>]+></a>[^<]+"
    patronvideos += "<h3 class='post-title entry-title'>[^<]+"
    patronvideos += "<a href='([^']+)'>([^<]+)</a>.*?"
    patronvideos += '<img alt="[^"]+" height="[^"]+" src="([^"]+)"'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    if DEBUG: scrapertools.printMatches(matches)

    itemlist = []
    for match in matches:
        scrapedtitle = match[1]
        scrapedplot = ""
        scrapedurl = urlparse.urljoin(item.url,match[0])
        scrapedthumbnail = match[2]
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")
        itemlist.append( Item(channel=CHANNELNAME, action="findvideos", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

    patron = "<a class='blog-pager-older-link' href='([^']+)'"
    matches = re.compile(patron,re.DOTALL).findall(data)
    if DEBUG: scrapertools.printMatches(matches)

    for match in matches:
        scrapedtitle = "(Página siguiente)"
        scrapedplot = ""
        scrapedurl = urlparse.urljoin(item.url,match)
        scrapedthumbnail = match[2]
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")
        itemlist.append( Item(channel=CHANNELNAME, action="novedades", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

    return itemlist
