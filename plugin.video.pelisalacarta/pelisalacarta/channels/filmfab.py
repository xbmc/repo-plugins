# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para cinegratis
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

CHANNELNAME = "FilmfaB"
DEBUG = True

def isGeneric():
    return True

def mainlist(item):
    logger.info("[Filmfab:py] mainlist")

    itemlist = []
    itemlist.append( Item(channel=CHANNELNAME, action="listvideos" , title="Novita (Ultimi film in ordine d'inserimento)"            , url="http://filmdblink.blogspot.com/index.html"))
    #itemlist.append( Item(channel=CHANNELNAME, action="listvideos" , title="Películas - Estrenos"             , url="http://www.cinegratis.net/index.php?module=estrenos"))

    #itemlist.append( Item(channel=CHANNELNAME, action="search"     , title="Buscar"))

    return itemlist



def listsimple(item):
    logger.info("[Filmfab:py] listsimple")

    url = item.url

    # Descarga la página
    data = scrapertools.cachePage(url)

    # Extrae los items
    patronvideos  = '<a href="(.*?)"><strong>(.*?)</strong></a> -<a .*?</a> -<a .*?</a> -<a .*?</a>((.*?)) -<a .*?</a>'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    itemlist = []
    for match in matches:
        # Atributos
        scrapedtitle = match[1]
        scrapedurl = urlparse.urljoin(url,match[0])
        scrapedthumbnail = ""
        scrapedplot = ""
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=[""]")

        itemlist.append( Item(channel=CHANNELNAME, action="findvideos" , title=scrapedtitle , url=scrapedurl, thumbnail=scrapedthumbnail, plot=scrapedplot))

    return itemlist

def listvideos(item):
    logger.info("[Filmfab:py] listvideos")

    url = item.url

    # Descarga la página
    data = scrapertools.cachePage(url)
    #logger.info(data)

    # Extrae los items
    patronvideos  = '<p>(<a href="[^"]+"><strong>.*?)</p>'
    entradas = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(entradas)
    
    itemlist = []
    for entrada in entradas:
        # Titulo
        patrontitulo = '<a href="[^"]+"><strong>([^<]+)<'
        matches = re.compile(patrontitulo,re.DOTALL).findall(entrada)
        scrapertools.printMatches(matches)
        if len(matches)>0:
            scrapedtitle = matches[0].strip()

        # Busca los enlaces a los videos
        import servertools
        listavideos = servertools.findvideos(entrada)
    
        for video in listavideos:
            scrapedtitle = scrapedtitle + " - " + video[0]
            scrapedurl = video[1]
            server = video[2]
            
            itemlist.append( Item(channel=CHANNELNAME, action="play" , title=scrapedtitle , url=scrapedurl, server=server, folder=False))

    return itemlist
