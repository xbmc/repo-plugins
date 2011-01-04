# -*- coding: utf-8 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para peliculasflv
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------
import urlparse,urllib2,urllib,re
import os, sys

import scrapertools
import servertools
import logger
import buscador
from item import Item

CHANNELNAME = "peliculasflv"
DEBUG = True

def isGeneric():
    return True

def mainlist(item):
    logger.info("[peliculasflv.py] mainlist")

    itemlist = []
    itemlist.append( Item(channel=CHANNELNAME, title="Novedades"    , action="listado", url="http://www.peliculas-flv.com/"))
    itemlist.append( Item(channel=CHANNELNAME, title="Por tags"     , action="tags", url="http://www.peliculas-flv.com/"))
    
    return itemlist

def listado(item):
    logger.info("[peliculasflv.py] listado")

    # Descarga la página
    data = scrapertools.cachePage(item.url)

    # Extrae las entradas
    patron = "<div class='post hentry uncustomized-post-template'>(.*?)<div id=\"latency-"
    matches = re.compile(patron,re.DOTALL).findall(data)
    #scrapertools.printMatches(matches)
    itemlist = []

    for elemento in matches:
        '''
        <a href='http://www.peliculas-flv.com/2010/11/enredados-espanol.html'>
        <div id='summary5995647639525095152'>
        <img style="float:left; margin:0 10px 10px 0;" width="120" src="http://1.bp.blogspot.com/_s25JOvnW5sA/TPP677-EmhI/AAAAAAAABzg/9bKdrI7lU-Y/s200/Enredados-poster-en-grande-de-la-pelicula.jpg" />Cuando el más buscado -y encantador- bandido del reino, Flynn Rider, se esconde en una misteriosa torre, toma por rehén a Rapunzel, una bella y avispada adolescente con una cabellera dorada de 21 metros de largo, que está encerrada en la torre. La singular prisionera, buscando el pasaporte que la saque del encierro donde ha permanecido durante años, sella un pacto con el guapo ladrón. Así es como el dúo se lanza a una travesía llena de acción, con un caballo súper-policía, un camaleón sobreprotector y una ruda pandilla de matones.<br /><br /><div class="player"><div class="player-titulo"><h1>Enredados - Español (TS-Screener)</h1></div><div class="player-contenido"><center><iframe src="http://peliculas-flv.hostzi.com/reproflv.php?url=http://taringa.bligoo.com/media/users/7/396271/files/27203/Enredados-esp.xml"
        '''
        patron  = "<a href='([^']+)'[^<]+"
        patron += "<div id='summary[^<]+"
        patron += '<img.*?src="([^"]+)"[^>]+>(.*?)<div class="player"><div.*?class="player-titulo"><h1>([^<]+)</h1></div><div class="player-contenido"><center><iframe src="http://peliculas-flv.hostzi.com/reproflv.php.url=([^"]+)"'
    
        matches2 = re.compile(patron,re.DOTALL).findall(elemento)
        if DEBUG: scrapertools.printMatches(matches)
    
        for match in matches2:
            scrapedtitle = match[3]
            scrapedplot = match[2]
            scrapedurl = urlparse.urljoin(item.url,match[4])
            scrapedthumbnail = urlparse.urljoin(item.url,match[1])
            if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")
    
            # Añade al listado de XBMC
            itemlist.append( Item(channel=CHANNELNAME, action="findvideos", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

    # Extrae el paginador
    patronvideos  = "<a class='blog-pager-older-link' href='([^']+)' id='Blog1_blog-pager-older-link' title='Siguiente'>"
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    if len(matches)>0:
        #http://www.somosmovies.com/search/label/Peliculas?updated-max=2010-12-20T08%3A27%3A00-06%3A00&max-results=12
        scrapedurl = urlparse.urljoin(item.url,matches[0])
        scrapedurl = scrapedurl.replace("%3A",":")
        itemlist.append( Item(channel=CHANNELNAME, action="peliculas", title="!Página siguiente" , url=scrapedurl , folder=True) )

    return itemlist

def tags(item):
    logger.info("[peliculasflv.py] tags")

    # Descarga la página
    data = scrapertools.cachePage(item.url)

    # Extrae las entradas
    patron = "<a dir='ltr' href='([^']+)'>([^<]+)</a>"
    matches = re.compile(patron,re.DOTALL).findall(data)
    itemlist = []

    for match in matches:
        scrapedtitle = match[1]
        scrapedplot = ""
        scrapedurl = urlparse.urljoin(item.url,match[0])
        scrapedthumbnail = ""
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        # Añade al listado de XBMC
        itemlist.append( Item(channel=CHANNELNAME, action="listado", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

    return itemlist

def findvideos(item):
    logger.info("[peliculasflv.py] findvideos")

    # Descarga la pagina
    data = scrapertools.cachePage(item.url)
    #logger.info(data)
    
    patronvideos  = '<title>([^<]+)</title>[^<]+'
    patronvideos += '<media.content url="([^"]+)"'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    
    itemlist = []
    for match in matches:
        scrapedtitle = match[0]+" [directo]"
        scrapedurl = match[1]
        server="directo"
        itemlist.append( Item(channel=CHANNELNAME, action="play" , title=scrapedtitle , url=scrapedurl, thumbnail=item.thumbnail, plot=item.plot, server=server, folder=False))

    return itemlist