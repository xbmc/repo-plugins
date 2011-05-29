# -*- coding: utf-8 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para newhd
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


CHANNELNAME = "newhd"
DEBUG = True

def isGeneric():
    return True

def mainlist(item):
    logger.info("[newhd.py] mainlist")

    itemlist = []
    itemlist.append( Item(channel=CHANNELNAME, title="Novedades", action="novedades", url="http://www.newhd.org/index.php?do=cat&category=online"))
    itemlist.append( Item(channel=CHANNELNAME, title="Listado Alfabético", action="alfa", url="http://www.newhd.org/index.php?do=cat&category=online"))
    itemlist.append( Item(channel=CHANNELNAME, title="Listado por Categorías", action="cat", url="http://www.newhd.org/index.php?do=cat&category=online"))
    itemlist.append( Item(channel=CHANNELNAME, title="Lo más valorado" , action="valorados", url="http://www.newhd.org/index.php"))
    itemlist.append( Item(channel=CHANNELNAME, title="Buscar", action="search") )

    return itemlist

def novedades(item):
    logger.info("[newhd.py] novedades")

    # Descarga la página
    data = scrapertools.cachePage(item.url)

    # Extrae las entradas
    patronvideos  = '<li><i>IMDB: <strong>(.*?)</table>'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    if DEBUG: scrapertools.printMatches(matches)

    itemlist = []
    for elemento in matches:
        patronvideos = '(.*?)</strong>.*?'
        patronvideos += '<h3 class="btl"><a href="([^"]+)".*?>(.*?)</a></h3>.*?'
        patronvideos += '<img src="([^"]+)".*?</td>'
        patronvideos += '.*?<div id=".*?style="display:inline;">([^<]+)</div>'
        matches2 = re.compile(patronvideos,re.DOTALL).findall(elemento)

        for match in matches2:
            scrapedurl = match[1]
            scrapedtitle = match[2]
            scrapedthumbnail = urlparse.urljoin("http://www.newhd.org",match[3])
            scrapedplot = match[4] + "\n\n IMDB: "+ match[0]
            logger.info(scrapedtitle)

            # Añade al listado
            itemlist.append( Item(channel=CHANNELNAME, action="videos", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )
			  
    # Extrae la marca de siguiente página
    patronvideos = '<div class="nextprev">.*?<span class="thide pprev">.*?<a href="([^"]+)">'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    if len(matches)>0:
		scrapedtitle = "Página siguiente"
		scrapedurl = urlparse.urljoin(item.url,matches[0])
		scrapedthumbnail = ""
		itemlist.append( Item( channel=CHANNELNAME , title=scrapedtitle , action="novedades" , url=scrapedurl , thumbnail=scrapedthumbnail, folder=True ) )

    return itemlist

def videos(item):

	logger.info("[newhd.py] videos")
	# Descarga la página
	data = scrapertools.cachePage(item.url)
	title= item.title
	scrapedthumbnail = item.thumbnail
	scrapedplot = item.plot
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
		itemlist.append( Item(channel=CHANNELNAME, action="play", title=scrapedtitle , url=videourl , thumbnail=scrapedthumbnail , plot=scrapedplot , server=server , folder=False) )

	return itemlist

def alfa(item):

	logger.info("[newhd.py] alfa")

    # Descarga la página
	data = scrapertools.cachePage(item.url)

    # Extrae las entradas
	patronvideos  = '<span class="Estilo60 Estilo4" >(.*?)</span>'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	if DEBUG: scrapertools.printMatches(matches)

	itemlist = []
	for elemento in matches:
		patronvideos  = '<a href="(.*?)".*?>(.*?)</a>'
		matches2 = re.compile(patronvideos,re.DOTALL).findall(elemento)

		for match in matches2:
			scrapedurl = urlparse.urljoin("http://www.newhd.org",match[0])
			scrapedurl = scrapedurl.replace("&amp;","&")
			scrapedtitle = match[1]
			scrapedthumbnail = ""
			scrapedplot = ""
			logger.info(scrapedtitle)

			# Añade al listado
			itemlist.append( Item(channel=CHANNELNAME, action="novedades", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )
		
	return itemlist

def cat(item):

	logger.info("[newhd.py] cat")

    # Descarga la página
	data = scrapertools.cachePage(item.url)

    # Extrae las entradas
	patronvideos  = '<li class="submenu">(.*?)<span class="sublnk Estilo1 Estilo3">'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	if DEBUG: scrapertools.printMatches(matches)

	itemlist = []
	for elemento in matches:
		patronvideos  = '.*?<a title="(.*?)" href="(.*?)".*?>.*?</a>'
		matches2 = re.compile(patronvideos,re.DOTALL).findall(elemento)

		for match in matches2:
			scrapedurl = urlparse.urljoin("http://www.newhd.org",match[1])
			scrapedtitle = match[0]
			scrapedthumbnail = ""
			scrapedplot = ""
			logger.info(scrapedtitle)

			# Añade al listado
			itemlist.append( Item(channel=CHANNELNAME, action="novedades", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )
		
	return itemlist
	
def valorados(item):
    logger.info("[newhd.py] valorados")

    # Descarga la página
    data = scrapertools.cachePage(item.url)

    # Extrae las entradas
    patronvideos  = '<h4 class="btl">Lo mas valorado</h4>(.*?)</ul>'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    if DEBUG: scrapertools.printMatches(matches)

    itemlist = []
    for elemento in matches:
        patronvideos  = '.*?<a href="([^"]+)".*?>(.*?)</a>'
        matches2 = re.compile(patronvideos,re.DOTALL).findall(elemento)

        for match in matches2:
            scrapedurl = match[0]
            scrapedtitle = match[1]
            scrapedthumbnail = ""
            scrapedplot = ""
            logger.info(scrapedtitle)

            # Añade al listado
            itemlist.append( Item(channel=CHANNELNAME, action="videos", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )
	return itemlist

def search(item):
	logger.info("[newhd.py] search")
    
	if config.get_platform()=="xbmc" or config.get_platform()=="xbmcdharma":
		from pelisalacarta import buscador
		texto = buscador.teclado()
		item.extra = texto

	itemlist = searchresults(item)

	return itemlist
    
def searchresults(item):
    logger.info("[newhd.py] searchresults")
    
    teclado = item.extra.replace(" ", "+")
    logger.info("[newhd.py] " + teclado)
    item.url = "http://www.newhd.org/index.php?do=search&subaction=search&search_start=1&full_search=0&result_from=1&result_num=20&story=" +teclado

    return searchresults2(item,teclado)
	
def searchresults2(item,teclado):
    logger.info("[newhd.py] searchresults2")

    # Descarga la página
    data = scrapertools.cachePage(item.url)

    # Extrae las entradas
    patronvideos  = '<li><i>IMDB: <strong>(.*?)</table>'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    if DEBUG: scrapertools.printMatches(matches)

    itemlist = []
    for elemento in matches:
        patronvideos = '(.*?)</strong>.*?'
        patronvideos += '<h3 class="btl"><a href="([^"]+)".*?>(.*?)</a></h3>.*?'
        patronvideos += '<img src="([^"]+)".*?</td>'
        patronvideos += ".*?<div id='.*?>(.*?)</div>"
        matches2 = re.compile(patronvideos,re.DOTALL).findall(elemento)

        for match in matches2:
            scrapedurl = match[1]
            scrapedtitle = match[2]
            scrapedthumbnail = urlparse.urljoin("http://www.newhd.org",match[3])
            plot = match[4] + "\n\n IMDB: " + match[0]
            scrapedplot = plot.replace("<span style='background-color:yellow;'><font color='red'>"+teclado+"</font></span>",teclado)
            logger.info(scrapedtitle)

            # Añade al listado
            itemlist.append( Item(channel=CHANNELNAME, action="videos", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , fanart=scrapedthumbnail , folder=True) )
			  
    # Extrae la marca de siguiente página
    patronvideos = '<div class="nextprev">.*?<span class="thide pprev">.*?<a href="([^"]+)">'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    if len(matches)>0:
		scrapedtitle = "Página siguiente"
		scrapedurl = urlparse.urljoin(item.url,matches[0])
		scrapedthumbnail = ""
		itemlist.append( Item( channel=CHANNELNAME , title=scrapedtitle , action="novedades" , url=scrapedurl , thumbnail=scrapedthumbnail, folder=True ) )

    return itemlist