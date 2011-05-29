# -*- coding: utf-8 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para islapeliculas
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


CHANNELNAME = "islapeliculas"
DEBUG = True

def isGeneric():
    return True

def mainlist(item):
    logger.info("[islapeliculas.py] mainlist")

    itemlist = []
    itemlist.append( Item(channel=CHANNELNAME, title="Novedades", action="novedades", url="http://www.islapeliculas.com/"))
    itemlist.append( Item(channel=CHANNELNAME, title="Listado por Categorías", action="cat", url="http://www.islapeliculas.com/"))
    itemlist.append( Item(channel=CHANNELNAME, title="Estrenos" , action="estrenos", url="http://www.islapeliculas.com/"))
    itemlist.append( Item(channel=CHANNELNAME, title="Buscar por Película", action="busqueda") )
    itemlist.append( Item(channel=CHANNELNAME, title="Buscar por Actor", action="busqueda") )

    return itemlist

def novedades(item):
    logger.info("[islapeliculas.py] novedades")

    # Descarga la página
    data = scrapertools.cachePage(item.url)

    # Extrae las entradas
    patronvideos  = '<div class="content">(.*?)</table>'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    if DEBUG: scrapertools.printMatches(matches)

    itemlist = []
    for elemento in matches:
        patronvideos = '.*?<h2 ><a.*?title="([^"]+)".*?href="([^"]+)".*?></a></h2>'
        patronvideos += '.*?<img src="([^"]+)".*?/>'
        matches2 = re.compile(patronvideos,re.DOTALL).findall(elemento)

        for match in matches2:
            scrapedurl = urlparse.urljoin(item.url,match[1])
            scrapedtitle = match[0]
            scrapedthumbnail = match[2]
            scrapedplot = ""
            logger.info(scrapedtitle)

            # Añade al listado
            itemlist.append( Item(channel=CHANNELNAME, action="listapelis", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )
			  
    # Extrae la marca de siguiente página
    patronvideos = '<td width="69">.*?<table.*?<a href="([^"]+)".*?>'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    if len(matches)>0:
		scrapedtitle = "Página siguiente"
		scrapedurl = urlparse.urljoin(item.url,matches[0])
		scrapedthumbnail = ""
		itemlist.append( Item( channel=CHANNELNAME , title=scrapedtitle , action="novedades" , url=scrapedurl , thumbnail=scrapedthumbnail, folder=True ) )

    return itemlist

	
def listapelis(item):
	logger.info("[islapeliculas.py] listapelis")

    # Descarga la página
	data = scrapertools.cachePage(item.url)

    # Extrae las entradas

	itemlist = []
	patronvideos = '<span class="estilo16"><a.*?href="([^"]+)".*?>.*?Pelicula (.*?)<strong>(.*?)</strong></a>'
	patronvideos += '.*?<img.*?>.*?<img.*?>.*?<strong>(.*?)</strong>'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	if DEBUG: scrapertools.printMatches(matches)
	for match in matches:
		if match[3]!="fileserve":
			scrapedurl = urlparse.urljoin("http://www.islapeliculas.com/",match[0])
			scrapedtitle = match[1] + match[2] + " - " + match[3]
			scrapedthumbnail = item.thumbnail
			logger.info(scrapedtitle)

			# Añade al listado
			itemlist.append( Item(channel=CHANNELNAME, action="videos", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , folder=True) )
			
	return itemlist
			
			
def videos(item):

	logger.info("[islapeliculas.py] videos")
	# Descarga la página
	data = scrapertools.cachePage(item.url)
	title= item.title
	scrapedthumbnail = item.thumbnail
	listavideos = servertools.findvideos(data)

	itemlist = []
	for video in listavideos:
		scrapedtitle = title.strip() + " - " + video[0]
		videourl = video[1]
		server = video[2]
		#logger.info("videotitle="+urllib.quote_plus( videotitle ))
		#logger.info("plot="+urllib.quote_plus( plot ))
		#plot = ""
		#logger.info("title="+urllib.quote_plus( title ))
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+videourl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		itemlist.append( Item(channel=CHANNELNAME, action="play", title=scrapedtitle , url=videourl , thumbnail=scrapedthumbnail , server=server , folder=False) )

	return itemlist


def cat(item):

	logger.info("[islapeliculas.py] cat")

    # Descarga la página
	data = scrapertools.cachePage(item.url)

    # Extrae las entradas
	patronvideos  = 'Género</td>(.*?)</table>'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	if DEBUG: scrapertools.printMatches(matches)

	itemlist = []
	for elemento in matches:
		patronvideos  = '.*?<h2>.*?<a href="(.*?)".*?>(.*?)</a>'
		matches2 = re.compile(patronvideos,re.DOTALL).findall(elemento)

		for match in matches2:
			scrapedurl = urlparse.urljoin(item.url,match[0])
			scrapedtitle = match[1]
			scrapedthumbnail = ""
			scrapedplot = ""
			logger.info(scrapedtitle)

			# Añade al listado
			itemlist.append( Item(channel=CHANNELNAME, action="novedades", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )
		
	return itemlist
	
def estrenos(item):
    logger.info("[islapeliculas.py] estrenos")

    # Descarga la página
    data = scrapertools.cachePage(item.url)

    # Extrae las entradas
    patronvideos  = 'Estrenos</td>(.*?)</table>'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    if DEBUG: scrapertools.printMatches(matches)

    itemlist = []
    for elemento in matches:
        patronvideos  = '.*?<td.*?<a href="([^"]+)".*?>(.*?)</a>'
        matches2 = re.compile(patronvideos,re.DOTALL).findall(elemento)

        for match in matches2:
            scrapedurl = urlparse.urljoin(item.url,match[0])
            scrapedtitle = match[1]
            scrapedthumbnail = ""
            scrapedplot = ""
            logger.info(scrapedtitle)

            # Añade al listado
            itemlist.append( Item(channel=CHANNELNAME, action="novedades", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )
	return itemlist

	
	
def busqueda(item):
	logger.info("[islapeliculas.py] busqueda")
    
	if config.get_platform()=="xbmc" or config.get_platform()=="xbmcdharma":
		from pelisalacarta import buscador
		texto = buscador.teclado()
		item.extra = texto

	itemlist = resultados(item)

	return itemlist
    
def resultados(item):
    logger.info("[islapeliculas.py] resultados")
    
    teclado = item.extra.replace(" ", "-")
    logger.info("[islapeliculas.py] " + teclado)
    if item.title == "Buscar por Película":
        item.url = "http://www.islapeliculas.com/buscar-pelicula-" +teclado
    else:
        item.url = "http://www.islapeliculas.com/actor-" +teclado

    return novedades(item)