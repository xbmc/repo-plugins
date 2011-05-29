# -*- coding: utf-8 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para internapoli
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------
import urlparse,urllib2,urllib,re
import os, sys

from core import logger
from core import config
from core import scrapertools
from core.item import Item
from servers import servertools

CHANNELNAME = "internapoli"
DEBUG = True

def isGeneric():
    return True

def mainlist(item):
    logger.info("[internapoli.py] mainlist")
    item.url = "http://internapoli-city.blogspot.com/"
    return novedades(item)

def novedades(item):
    logger.info("[internapoli.py] novedades")

    # Descarga la página
    data = scrapertools.cachePage(item.url)
    '''
    <a href='http://internapoli-city.blogspot.com/2011/05/love-storymegaupload-ita.html'>Love Story.Megaupload ita.</a>
    </h3>
    .*?<img style="x" id="BLOGGER_PHOTO_ID_5607274743329908370" border="0" alt="" src="http://1.bp.blogspot.com/-ukfFT7Mimu4/TdEKq6Iy5pI/AAAAAAAAf6o/GQIoTKklITM/s320/Love_Story_Poster.jpg" /></a> <strong>Megaupload .. <a href="http://www.megaupload.com/?d=RPVQB9SG"><span style="color:#ff0000;">QUI </span></a>- su </strong><a href="http://internapoli-city.blogspot.com/"><strong><span style="color:#ff0000;">Internapoli city</span></strong></a><strong><span style="color:#ff0000;"> </span></strong><br /><br />Oliver, figlio di un ricchissimo finanziere, e Jenny, figlia di un pasticcere di origine italiana, si conoscono nella biblioteca dell&#8217;università. Si frequentano, si innamorano. Nonostante il divieto paterno, Oliver sposa Jenny&#8230;<br />DRAMMATICO<br />Prima di Titanik, era considerato l'icona dei film d'amore piu' conosciuto di tutti i tempi della storia del cinema.<br />Da oggi (<strong>dopo Internapoli city</strong>) su tutti i blog.
    '''
    patronvideos  = "<h3 class='post-title entry-title'>[^<]+"
    patronvideos += "<a href='([^']+)'>([^<]+)</a>.*?"
    patronvideos += '<img style="[^"]+" id="[^"]+" border="[^"]+" alt="" src="([^"]+)"'
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
