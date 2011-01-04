# -*- coding: utf-8 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para seriespepito
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------
import urlparse,urllib2,urllib,re

import logger
import scrapertools
from item import Item

CHANNELNAME = "seriespepito"
DEBUG = True

def isGeneric():
    return True

def mainlist(item):
    logger.info("[seriespepito.py] mainlist")

    itemlist = []
    itemlist.append( Item(channel=CHANNELNAME, action="updatedserieslist", title="Series actualizadas", url="http://www.seriespepito.com/"))
    itemlist.append( Item(channel=CHANNELNAME, action="lastepisodelist"  , title="Nuevos capítulos"   , url="http://www.seriespepito.com/nuevos-capitulos/"))
    itemlist.append( Item(channel=CHANNELNAME, action="listalfabetico"   , title="Listado alfabético"))
    itemlist.append( Item(channel=CHANNELNAME, action="allserieslist"    , title="Listado completo",    url="http://www.seriespepito.com/"))

    return itemlist

def updatedserieslist(item):
    logger.info("[seriespepito.py] lastepisodeslist")

    # Descarga la página
    data = scrapertools.cachePage(item.url)
    #logger.info(data)

    # Extrae las entradas (carpetas)
    patron  = '<td valign="top" align="center" width="20%">[^<]+'
    patron += '<a class="azulverde" href="([^"]+)" title="">[^<]+'
    patron += "<img src='([^']+)'.*?/><br>([^<]+)</a>"
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    itemlist = []
    for match in matches:
        scrapedtitle = match[2]
        scrapedurl = match[0]
        scrapedthumbnail = match[1]
        scrapedplot = ""
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        # Ajusta el encoding a UTF-8
        scrapedtitle = unicode( scrapedtitle, "iso-8859-1" , errors="replace" ).encode("utf-8")

        itemlist.append( Item(channel=CHANNELNAME, action="episodelist" , title=scrapedtitle , url=scrapedurl, thumbnail=scrapedthumbnail, plot=scrapedplot))

    return itemlist

def alphaserieslist(item):
    logger.info("[seriespepito.py] alphaserieslist")

    # Descarga la página
    data = scrapertools.cachePage(item.url)
    #logger.info(data)

    # Extrae las entradas (carpetas)
    patron  = '<td valign="top" align="center" width="33%">[^<]+'
    patron += '<a class="azulverde" href="([^"]+)" title="[^"]+">[^<]+'
    patron += "<img src='([^']+)'.*?/><br />([^<]+)</a>[^<]+"
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    itemlist = []
    for match in matches:
        scrapedtitle = match[2]
        scrapedurl = match[0]
        scrapedthumbnail = match[1]
        scrapedplot = ""
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        # Ajusta el encoding a UTF-8
        scrapedtitle = unicode( scrapedtitle, "iso-8859-1" , errors="replace" ).encode("utf-8")

        itemlist.append( Item(channel=CHANNELNAME, action="episodelist" , title=scrapedtitle , url=scrapedurl, thumbnail=scrapedthumbnail, plot=scrapedplot, show=scrapedtitle))

    return itemlist

def lastepisodelist(item):
    logger.info("[seriespepito.py] lastepisodeslist")

    # Descarga la página
    data = scrapertools.cachePage(item.url)
    #logger.info(data)

    # Extrae las entradas (carpetas)
    patron  = '<td valign="top" align="center" width="33%">[^<]+'
    patron += '<a href="([^"]+)"[^>]+>[^<]+'
    patron += "<img src='([^']+)'.*?<br />[^<]+"
    patron += '<a.*?title="([^"]+).*?'
    patron += '<a.*?title="([^"]+).*?'
    patron += '<a.*?title="([^"]+)'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    itemlist = []
    for match in matches:
        scrapedtitle = match[2]+" - "+match[3]+" - "+match[4]
        scrapedurl = match[0]
        scrapedthumbnail = match[1]
        scrapedplot = ""

        # Ajusta el encoding a UTF-8
        scrapedtitle = unicode( scrapedtitle, "iso-8859-1" , errors="replace" ).encode("utf-8")

        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        itemlist.append( Item(channel=CHANNELNAME, action="findvideos" , title=scrapedtitle , url=scrapedurl, thumbnail=scrapedthumbnail, plot=scrapedplot))

    return itemlist

def allserieslist(item):
    logger.info("[seriespepito.py] lastepisodeslist")

    # Descarga la página
    data = scrapertools.cachePage(item.url)
    #logger.info(data)

    # Extrae las entradas (carpetas)
    patron  = '<b><a class="azulverde" href="([^"]+)">([^<]+)</a></b><br />'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    itemlist = []

    for match in matches:
        scrapedtitle = match[1]
        scrapedurl = match[0]
        scrapedthumbnail = ""
        scrapedplot = ""
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        # Ajusta el encoding a UTF-8
        scrapedtitle = unicode( scrapedtitle, "iso-8859-1" , errors="replace" ).encode("utf-8")

        itemlist.append( Item(channel=CHANNELNAME, action="episodelist" , title=scrapedtitle , url=scrapedurl, thumbnail=scrapedthumbnail, plot=scrapedplot))

    return itemlist

def listalfabetico(item):
    
    itemlist = []
    itemlist.append( Item(channel=CHANNELNAME, action="alphaserieslist" , title="0-9",url="http://www.seriespepito.com/lista-series-num/"))
    itemlist.append( Item(channel=CHANNELNAME, action="alphaserieslist" , title="A",url="http://www.seriespepito.com/lista-series-a/"))
    itemlist.append( Item(channel=CHANNELNAME, action="alphaserieslist" , title="B",url="http://www.seriespepito.com/lista-series-b/"))
    itemlist.append( Item(channel=CHANNELNAME, action="alphaserieslist" , title="C",url="http://www.seriespepito.com/lista-series-c/"))
    itemlist.append( Item(channel=CHANNELNAME, action="alphaserieslist" , title="D",url="http://www.seriespepito.com/lista-series-d/"))
    itemlist.append( Item(channel=CHANNELNAME, action="alphaserieslist" , title="E",url="http://www.seriespepito.com/lista-series-e/"))
    itemlist.append( Item(channel=CHANNELNAME, action="alphaserieslist" , title="F",url="http://www.seriespepito.com/lista-series-f/"))
    itemlist.append( Item(channel=CHANNELNAME, action="alphaserieslist" , title="G",url="http://www.seriespepito.com/lista-series-g/"))
    itemlist.append( Item(channel=CHANNELNAME, action="alphaserieslist" , title="H",url="http://www.seriespepito.com/lista-series-h/"))
    itemlist.append( Item(channel=CHANNELNAME, action="alphaserieslist" , title="I",url="http://www.seriespepito.com/lista-series-i/"))
    itemlist.append( Item(channel=CHANNELNAME, action="alphaserieslist" , title="J",url="http://www.seriespepito.com/lista-series-j/"))
    itemlist.append( Item(channel=CHANNELNAME, action="alphaserieslist" , title="K",url="http://www.seriespepito.com/lista-series-k/"))
    itemlist.append( Item(channel=CHANNELNAME, action="alphaserieslist" , title="L",url="http://www.seriespepito.com/lista-series-l/"))
    itemlist.append( Item(channel=CHANNELNAME, action="alphaserieslist" , title="M",url="http://www.seriespepito.com/lista-series-m/"))
    itemlist.append( Item(channel=CHANNELNAME, action="alphaserieslist" , title="N",url="http://www.seriespepito.com/lista-series-n/"))
    itemlist.append( Item(channel=CHANNELNAME, action="alphaserieslist" , title="O",url="http://www.seriespepito.com/lista-series-o/"))
    itemlist.append( Item(channel=CHANNELNAME, action="alphaserieslist" , title="P",url="http://www.seriespepito.com/lista-series-p/"))
    itemlist.append( Item(channel=CHANNELNAME, action="alphaserieslist" , title="Q",url="http://www.seriespepito.com/lista-series-q/"))
    itemlist.append( Item(channel=CHANNELNAME, action="alphaserieslist" , title="R",url="http://www.seriespepito.com/lista-series-r/"))
    itemlist.append( Item(channel=CHANNELNAME, action="alphaserieslist" , title="S",url="http://www.seriespepito.com/lista-series-s/"))
    itemlist.append( Item(channel=CHANNELNAME, action="alphaserieslist" , title="T",url="http://www.seriespepito.com/lista-series-t/"))
    itemlist.append( Item(channel=CHANNELNAME, action="alphaserieslist" , title="U",url="http://www.seriespepito.com/lista-series-u/"))
    itemlist.append( Item(channel=CHANNELNAME, action="alphaserieslist" , title="V",url="http://www.seriespepito.com/lista-series-v/"))
    itemlist.append( Item(channel=CHANNELNAME, action="alphaserieslist" , title="W",url="http://www.seriespepito.com/lista-series-w/"))
    itemlist.append( Item(channel=CHANNELNAME, action="alphaserieslist" , title="X",url="http://www.seriespepito.com/lista-series-x/"))
    itemlist.append( Item(channel=CHANNELNAME, action="alphaserieslist" , title="Y",url="http://www.seriespepito.com/lista-series-y/"))
    itemlist.append( Item(channel=CHANNELNAME, action="alphaserieslist" , title="Z",url="http://www.seriespepito.com/lista-series-z/"))

    return itemlist

def episodelist(item):
    logger.info("[seriespepito.py] list")

    # Descarga la página
    data = scrapertools.cachePage(item.url)
    #logger.info(data)

    # Extrae el argumento
    patron  = '<div class="contenido" id="noticia">.*?<span[^>]+>(.*?)</div>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    if len(matches)>0:
        scrapedplot = matches[0]
        scrapedplot = scrapertools.htmlclean(scrapedplot).strip()
        
        # Unas series están en utf-8, otras en iso-8859-1. Esta doble conversión funciona :)
        try:
            intermedia = unicode( scrapedplot, "utf-8" , errors="replace" ).encode("iso-8859-1")
            intermedia = unicode( intermedia, "iso-8859-1" , errors="replace" ).encode("utf-8")
            #print item.title+" encoding 1"
            scrapedplot = intermedia
        except:
            #print item.title+" encoding 2"
            scrapedplot = unicode( scrapedplot, "iso-8859-1" , errors="replace" ).encode("utf-8")
            
        item.plot = scrapedplot
    else:
        scrapedplot = ""

    # Extrae los capítulos
    patron = "<li class='li_capitulo'><a class='capitulo1' href='([^']+)' title='[^']+'>([^<]+)</a>&nbsp;<img src='([^']+)'[^>]+></li>"
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    itemlist = []
    for match in matches:
        scrapedtitle = match[1] + " ["+match[2][49:-4]+"]"
        scrapedurl = match[0]
        scrapedthumbnail = item.thumbnail
        #scrapedplot = ""
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        # Ajusta el encoding a UTF-8
        scrapedtitle = unicode( scrapedtitle, "iso-8859-1" , errors="replace" ).encode("utf-8")

        itemlist.append( Item(channel=CHANNELNAME, action="findvideos" , title=scrapedtitle , url=scrapedurl, thumbnail=scrapedthumbnail, plot=scrapedplot, show=item.show))

    return itemlist

if __name__ == "__main__":

    itemsletra = listalfabetico(None)

    for itemletra in itemsletra:
        itemsprogramas = alphaserieslist(itemletra)
        for itemprograma in itemsprogramas:
            print itemprograma.tostring()+" plot=["+itemprograma.plot+"]"
            if itemprograma.title == "5 Días para Morir":
                itemsepisodios = episodelist(itemprograma)
                for itemepisodio in itemsepisodios:
                    print itemepisodio.tostring()+" plot=["+itemepisodio.plot+"]"
                break
        break