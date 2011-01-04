# -*- coding: utf-8 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para cuevana
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------
import urlparse,urllib2,urllib,re
import os, sys

import scrapertools
import servertools
import logger
import buscador
from item import Item

CHANNELNAME = "cuevana"
DEBUG = True

def isGeneric():
    return True

def mainlist(item):
    logger.info("[cuevana.py] mainlist")

    itemlist = []
    itemlist.append( Item(channel=CHANNELNAME, title="Películas"  , action="peliculas", url="http://www.cuevana.tv/peliculas/"))
    itemlist.append( Item(channel=CHANNELNAME, title="Series"     , action="series",    url="http://www.cuevana.tv/series/"))
    
    return itemlist

def peliculas(item):
    logger.info("[cuevana.py] peliculas")

    # Descarga la página
    data = scrapertools.cachePage(item.url)

    # Extrae las entradas
    '''
    <tr class='row2'>
    <td valign='top'><a href='/peliculas/2933/alpha-and-omega/'><img src='/box/2933.jpg' border='0' height='90' /></a></td>
    <td valign='top'><div class='tit'><a href='/peliculas/2933/alpha-and-omega/'>Alpha and Omega</a></div>
    <div class='font11'>Dos pequeños carrochos de lobo se ven obligados a convivir por determinadas circunstancias.
    <div class='reparto'><b>Reparto:</b> <a href='/buscar/?q=Animación&cat=actor'>Animación</a></div>
    </div></td>
    '''
    patronvideos  = "<tr class='row[^<]+"
    patronvideos += "<td valign='top'><a href='([^']+)'><img src='([^']+)'[^>]+></a></td>[^<]+"
    patronvideos += "<td valign='top'><div class='tit'><a[^>]+>([^<]+)</a></div>[^<]+"
    patronvideos += "<div class='font11'>([^<]+)<"

    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    if DEBUG: scrapertools.printMatches(matches)

    itemlist = []
    for match in matches:
        scrapedtitle = match[2]
        scrapedplot = match[3]
        scrapedurl = urlparse.urljoin(item.url,match[0])
        scrapedthumbnail = urlparse.urljoin(item.url,match[1])
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        # Añade al listado de XBMC
        itemlist.append( Item(channel=CHANNELNAME, action="findvideos", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

    # Extrae el paginador
    patronvideos  = "<a class='next' href='([^']+)' title='Siguiente'>"
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    if len(matches)>0:
        scrapedurl = urlparse.urljoin(item.url,matches[0])
        itemlist.append( Item(channel=CHANNELNAME, action="peliculas", title="!Página siguiente" , url=scrapedurl , folder=True) )

    return itemlist

def series(item):
    logger.info("[cuevana.py] series")

    # Descarga la página
    data = scrapertools.cachePage(item.url)

    # Extrae las entradas
    patron  = 'serieslist.push\(\{id\:([0-9]+),nombre\:"([^"]+)"\}\);'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
    itemlist = []
    for match in matches:
        scrapedtitle = match[1]
        scrapedplot = ""
        code = match[0]
        scrapedurl = "http://www.cuevana.tv/list_search_id.php?serie="+code
        scrapedthumbnail = "http://www.cuevana.tv/box/"+code+".jpg"
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        itemlist.append( Item(channel=CHANNELNAME, action="temporadas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , show=item.title , folder=True) )

    return itemlist

def temporadas(item):
    logger.info("[cuevana.py] temporadas")

    # Descarga la página
    data = scrapertools.cachePage(item.url)

    # Extrae las entradas
    patron  = '<li onclick=\'listSeries\(2,"([^"]+)"\)\'>([^<]+)</li>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
    itemlist = []
    for match in matches:
        scrapedtitle = match[1]
        scrapedplot = ""
        code = match[0]
        scrapedurl = "http://www.cuevana.tv/list_search_id.php?temporada="+code
        scrapedthumbnail = item.thumbnail
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        itemlist.append( Item(channel=CHANNELNAME, action="episodios", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , show=item.show + " - " + item.title , folder=True) )

    return itemlist

def episodios(item):
    logger.info("[cuevana.py] episodios")

    # Descarga la página
    data = scrapertools.cachePage(item.url)

    # Extrae las entradas
    #<li onclick='listSeries(3,"5099")'><span class='nume'>1</span> Truth Be Told</li>
    patron  = '<li onclick=\'listSeries\(3,"([^"]+)"\)\'><span class=\'nume\'>([^<]+)</span>([^<]+)</li>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
    itemlist = []
    for match in matches:
        code = match[0]
        scrapedtitle = match[1]+" "+match[2].strip()
        scrapedplot = ""
        scrapedurl = "http://www.cuevana.tv/list_search_info.php?episodio="+code
        scrapedthumbnail = item.thumbnail
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        itemlist.append( Item(channel=CHANNELNAME, action="findvideos", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , show = item.show , folder=True) )

    return itemlist

def listalfabetico(item):
    logger.info("[cuevana.py] listalfabetico")
    
    itemlist = []
    itemlist.append( Item(channel=CHANNELNAME, action="listpeliconcaratula" , title="0-9", url="http://www.cinetube.es/peliculas/0-9/"))
    itemlist.append( Item(channel=CHANNELNAME, action="listpeliconcaratula" , title="A"  , url="http://www.cinetube.es/peliculas/A/"))
    itemlist.append( Item(channel=CHANNELNAME, action="listpeliconcaratula" , title="B"  , url="http://www.cinetube.es/peliculas/B/"))
    itemlist.append( Item(channel=CHANNELNAME, action="listpeliconcaratula" , title="C"  , url="http://www.cinetube.es/peliculas/C/"))
    itemlist.append( Item(channel=CHANNELNAME, action="listpeliconcaratula" , title="D"  , url="http://www.cinetube.es/peliculas/D/"))
    itemlist.append( Item(channel=CHANNELNAME, action="listpeliconcaratula" , title="E"  , url="http://www.cinetube.es/peliculas/E/"))
    itemlist.append( Item(channel=CHANNELNAME, action="listpeliconcaratula" , title="F"  , url="http://www.cinetube.es/peliculas/F/"))
    itemlist.append( Item(channel=CHANNELNAME, action="listpeliconcaratula" , title="G"  , url="http://www.cinetube.es/peliculas/G/"))
    itemlist.append( Item(channel=CHANNELNAME, action="listpeliconcaratula" , title="H"  , url="http://www.cinetube.es/peliculas/H/"))
    itemlist.append( Item(channel=CHANNELNAME, action="listpeliconcaratula" , title="I"  , url="http://www.cinetube.es/peliculas/I/"))
    itemlist.append( Item(channel=CHANNELNAME, action="listpeliconcaratula" , title="J"  , url="http://www.cinetube.es/peliculas/J/"))
    itemlist.append( Item(channel=CHANNELNAME, action="listpeliconcaratula" , title="K"  , url="http://www.cinetube.es/peliculas/K/"))
    itemlist.append( Item(channel=CHANNELNAME, action="listpeliconcaratula" , title="L"  , url="http://www.cinetube.es/peliculas/L/"))
    itemlist.append( Item(channel=CHANNELNAME, action="listpeliconcaratula" , title="M"  , url="http://www.cinetube.es/peliculas/M/"))
    itemlist.append( Item(channel=CHANNELNAME, action="listpeliconcaratula" , title="N"  , url="http://www.cinetube.es/peliculas/N/"))
    itemlist.append( Item(channel=CHANNELNAME, action="listpeliconcaratula" , title="O"  , url="http://www.cinetube.es/peliculas/O/"))
    itemlist.append( Item(channel=CHANNELNAME, action="listpeliconcaratula" , title="P"  , url="http://www.cinetube.es/peliculas/P/"))
    itemlist.append( Item(channel=CHANNELNAME, action="listpeliconcaratula" , title="Q"  , url="http://www.cinetube.es/peliculas/Q/"))
    itemlist.append( Item(channel=CHANNELNAME, action="listpeliconcaratula" , title="R"  , url="http://www.cinetube.es/peliculas/R/"))
    itemlist.append( Item(channel=CHANNELNAME, action="listpeliconcaratula" , title="S"  , url="http://www.cinetube.es/peliculas/S/"))
    itemlist.append( Item(channel=CHANNELNAME, action="listpeliconcaratula" , title="T"  , url="http://www.cinetube.es/peliculas/T/"))
    itemlist.append( Item(channel=CHANNELNAME, action="listpeliconcaratula" , title="U"  , url="http://www.cinetube.es/peliculas/U/"))
    itemlist.append( Item(channel=CHANNELNAME, action="listpeliconcaratula" , title="V"  , url="http://www.cinetube.es/peliculas/V/"))
    itemlist.append( Item(channel=CHANNELNAME, action="listpeliconcaratula" , title="W"  , url="http://www.cinetube.es/peliculas/W/"))
    itemlist.append( Item(channel=CHANNELNAME, action="listpeliconcaratula" , title="X"  , url="http://www.cinetube.es/peliculas/X/"))
    itemlist.append( Item(channel=CHANNELNAME, action="listpeliconcaratula" , title="Y"  , url="http://www.cinetube.es/peliculas/Y/"))
    itemlist.append( Item(channel=CHANNELNAME, action="listpeliconcaratula" , title="Z"  , url="http://www.cinetube.es/peliculas/Z/"))

    return itemlist
    
def findvideos(item):
    logger.info("[cuevana.py] findvideos")

    code =""
    if (item.url.startswith("http://www.cuevana.tv/list_search_info.php")):
        data = scrapertools.cachePage(item.url)
        logger.info("data="+data)
        patron = "window.location\='/series/([0-9]+)/"
        matches = re.compile(patron,re.DOTALL).findall(data)
        if len(matches)>0:
            code = matches[0]
        logger.info("code="+code)
        url = "http://www.cuevana.tv/player/source?id=%s&subs=,ES&onstart=yes&tipo=s&sub_pre=ES" % matches[0]
    else:
        # http://www.cuevana.tv/peliculas/2553/la-cienaga/
        logger.info("url1="+item.url)
        patron = "http://www.cuevana.tv/peliculas/([0-9]+)/"
        matches = re.compile(patron,re.DOTALL).findall(item.url)
        if len(matches)>0:
            code = matches[0]
        logger.info("code="+code)
        url = "http://www.cuevana.tv/player/source?id=%s&subs=,ES&onstart=yes&sub_pre=ES#" % matches[0]
    
    logger.info("url2="+url)
    data = scrapertools.cachePage(url)
    logger.info("data="+data)

    # goSource('ee5533f50eab1ef355661eef3b9b90ec','megaupload')
    patron = "goSource\('([^']+)','megaupload'\)"
    matches = re.compile(patron,re.DOTALL).findall(data)
    if len(matches)>0:
        data = scrapertools.cachePagePost("http://www.cuevana.tv/player/source_get","key=%s&host=megaupload&vars=&id=2933&subs=,ES&tipo=&amp;sub_pre=ES" % matches[0])
    logger.info("data="+data)

    listavideos = servertools.findvideos(data)
    
    itemlist = []
    
    for video in listavideos:
        server = video[2]
        scrapedtitle = item.title + " [" + server + "]"
        scrapedurl = video[1]
        
        itemlist.append( Item(channel=CHANNELNAME, action="play" , title=scrapedtitle , url=scrapedurl, thumbnail=item.thumbnail, plot=item.plot, server=server, folder=False))

    return itemlist