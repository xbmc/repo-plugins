# -*- coding: utf-8 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para buenaisla
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


CHANNELNAME = "buenaisla"
DEBUG = True

def isGeneric():
    return True

def mainlist(item):
    logger.info("[buenaisla.py] mainlist")

    itemlist = []
    itemlist.append( Item(channel=CHANNELNAME, title="Novedades", action="novedades", url="http://www.buenaisla.com/modules.php?name=Anime-Online"))
    itemlist.append( Item(channel=CHANNELNAME, title="Últimas Series Agregadas" , action="ultimas", url="http://www.buenaisla.com/modules.php?name=Anime-Online"))
    itemlist.append( Item(channel=CHANNELNAME, title="Listado por Géneros", action="cat", url="http://www.buenaisla.com/modules.php?name=Anime-Online"))
    itemlist.append( Item(channel=CHANNELNAME, title="Lista Completa" , action="listacompleta", url="http://www.buenaisla.com/modules.php?name=Anime-Online"))
    itemlist.append( Item(channel=CHANNELNAME, title="Buscar" , action="busqueda") )

    return itemlist

def novedades(item):
    logger.info("[buenaisla.py] novedades")

    # Descarga la página
    data = scrapertools.cachePage(item.url)

    # Extrae las entradas
    patronvideos  = '<td width="33%">(.*?)</td>'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    if DEBUG: scrapertools.printMatches(matches)

    itemlist = []
    for elemento in matches:
        patronvideos = '<a href="(.*?)">.*?<img alt="(.*?)" src="(.*?)".*?></a>'
        matches2 = re.compile(patronvideos,re.DOTALL).findall(elemento)

        for match in matches2:
            scrapedurl = urlparse.urljoin("http://www.buenaisla.com/",match[0])
            scrapedtitle = match[1]
            scrapedthumbnail = urlparse.urljoin("http://www.buenaisla.com/",match[2])
            scrapedplot = ""
            logger.info(scrapedtitle)

            # Añade al listado
            itemlist.append( Item(channel=CHANNELNAME, action="videos", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

    return itemlist
			
			
def videos(item):

	logger.info("[islapeliculas.py] videos")
	# Descarga la página
	data = scrapertools.cachePage(item.url)
	patron = '(modules.php\?name=Anime-Online&func=JokeView&jokeid=.*?&amp;Es=\d)'
	matches = re.compile(patron,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)
	for match in matches:
		url= urlparse.urljoin('http://www.buenaisla.com/',match)
		url = url.replace('&amp;','&')
		data2= scrapertools.cachePage(url)
		data = data + data2
			
	title= item.title
	scrapedthumbnail = item.thumbnail
	listavideos = servertools.findvideos(data)

	itemlist = []
	for video in listavideos:
		invalid = video[1]
		invalid = invalid[0:8]
		if invalid!= "FN3WE43K" and invalid!="9CC3F8&e":
			scrapedtitle = title.strip() + " - " + video[0]
			videourl = video[1]
			server = video[2]
			if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+videourl+"], thumbnail=["+scrapedthumbnail+"]")

			# Añade al listado de XBMC
			itemlist.append( Item(channel=CHANNELNAME, action="play", title=scrapedtitle , url=videourl , thumbnail=scrapedthumbnail , server=server , folder=False) )

	return itemlist


def cat(item):

	logger.info("[islapeliculas.py] categorias")

    # Descarga la página
	data = scrapertools.cachePage(item.url)

    # Extrae las entradas
	itemlist = []
	matches=["Accion","Artes-Marciales","Aventura","Ciencia-Ficcion","Comedia","Ecchi","Escolares","Deportes","Drama","Fantasia","Harem","Horror","Magicos","Misterio","Romance","Seinen","Shojo","Shonen","Vampiros"]
	for match in matches:
		scrapedurl = "http://www.buenaisla.com/modules.php?name=Anime-Online&func=Generos&Genero=" + match
		scrapedtitle = match
		scrapedtitle = scrapedtitle.replace("-"," ")
		scrapedthumbnail = ""
		scrapedplot = ""
		logger.info(scrapedtitle)

		# Añade al listado
		itemlist.append( Item(channel=CHANNELNAME, action="listaseries", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )
		
	return itemlist
	
def listaseries(item):
    logger.info("[islapeliculas.py] listaseries")

    # Descarga la página
    data = scrapertools.cachePage(item.url)

    # Extrae las entradas
    patronvideos  = '<td  align="center" width=.*?33%.*?>(.*?)</td>'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    if DEBUG: scrapertools.printMatches(matches)

    itemlist = []
    for elemento in matches:
        patronvideos = '<a href="([^"]+)".*?><img alt="Capitulos de ([^"]+)".*?src=\'(.*?)\'.*?</a>'
        matches2 = re.compile(patronvideos,re.DOTALL).findall(elemento)

        for match in matches2:
            scrapedurl = urlparse.urljoin("http://www.buenaisla.com/",match[0])
            scrapedtitle = match[1]
            scrapedthumbnail = urlparse.urljoin("http://www.buenaisla.com/",match[2])
            scrapedplot = ""
            logger.info(scrapedtitle)

            # Añade al listado
            itemlist.append( Item(channel=CHANNELNAME, action="listacapitulos", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

    return itemlist
	
def ultimas(item):
    logger.info("[islapeliculas.py] ultimas")

    # Descarga la página
    data = scrapertools.cachePage(item.url)

    # Extrae las entradas
    patronvideos  = '<h2>Ultimas series Agregadas(.*?)<td class="tbll">'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    if DEBUG: scrapertools.printMatches(matches)

    itemlist = []
    for elemento in matches:
        patronvideos = '<a href="([^"]+)".*?><img alt="Capitulos de ([^"]+)".*?src=\'(.*?)\'.*?</a><br><a.*?>.*?</a>.*?<td.*?>'
        matches2 = re.compile(patronvideos,re.DOTALL).findall(elemento)

        for match in matches2:
            scrapedurl = urlparse.urljoin("http://www.buenaisla.com/",match[0])
            scrapedtitle = match[1]
            scrapedthumbnail = urlparse.urljoin("http://www.buenaisla.com/",match[2])
            scrapedplot = ""
            logger.info(scrapedtitle)

            # Añade al listado
            itemlist.append( Item(channel=CHANNELNAME, action="listacapitulos", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

    return itemlist
	
def listacapitulos(item):
	logger.info("[islapeliculas.py] listacapitulos")

    # Descarga la página
	data = scrapertools.cachePage(item.url)
    # Extrae las entradas
	patronvideos  = '<a.*?alt="Capitulos de.*?".*?>.*?<img.*?src="(.*?)".*?SINOPSIS: </strong>(.*?)<b>'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	if DEBUG: scrapertools.printMatches(matches)
	if len (matches)>0:
			imagen = "http://www.buenaisla.com/"+matches[0][0]
			sinopsis = matches[0][1]

    # Extrae las entradas
	patronvideos  = '<td height="25">(.*?)</td>'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	itemlist = []
	for elemento in matches:
		patronvideos = '.*?<a href="(.*?)".*?>(.*?)</a>'
		matches2 = re.compile(patronvideos,re.DOTALL).findall(elemento)

		for match in matches2:
			scrapedurl = urlparse.urljoin("http://www.buenaisla.com/",match[0])
			scrapedtitle = match[1]
			logger.info(scrapedtitle)

			# Añade al listado
			itemlist.append( Item(channel=CHANNELNAME, action="videos", title=scrapedtitle , url=scrapedurl , thumbnail=imagen , plot=sinopsis , folder=True) )
			
	# Extrae la marca de siguiente página
	patronvideos = 'Chistes Encontrados(.*?)<b>'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)
	for elemento in matches:
		patronvideos = '[^\d](.*?) paginas.*?</font>.*?<a href=(.*?)>'
		matches2 = re.compile(patronvideos,re.DOTALL).findall(elemento)
		if len(matches2)>0:
			scrapedurl = "http://www.buenaisla.com/" + matches2[0][1][1:]
			scrapedurl = scrapedurl[0:-1]
			paginas= matches2[0][0]
			pagina= scrapedurl[-2:]
			pagina = pagina.replace('=','')
			scrapedtitle = "Página " + pagina + " de "+ paginas[1:]
			if pagina=="1":break
			itemlist.append( Item( channel=CHANNELNAME , title=scrapedtitle , action="listacapitulos" , url=scrapedurl , thumbnail="", plot="" , folder=True ) )

	return itemlist
	
def listacompleta(item):
    logger.info("[islapeliculas.py] lista")

    # Descarga la página
    data = scrapertools.cachePage(item.url)

    # Extrae las entradas
    patronvideos  = '<td bgcolor="#DEEBFE">(.*?)</td>'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    if DEBUG: scrapertools.printMatches(matches)

    itemlist = []
    for elemento in matches:
        patronvideos = '<a.*?href="(.*?)".*?>.*?>(.*?)</div></a>'
        matches2 = re.compile(patronvideos,re.DOTALL).findall(elemento)

        for match in matches2:
            scrapedurl = urlparse.urljoin("http://www.buenaisla.com/",match[0])
            scrapedtitle = match[1]
            scrapedthumbnail = ""
            scrapedplot = ""
            logger.info(scrapedtitle)

            # Añade al listado
            itemlist.append( Item(channel=CHANNELNAME, action="listacapitulos", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

    return itemlist

	
	
def busqueda(item):
	logger.info("[islapeliculas.py] busqueda")
    
	if config.get_platform()=="xbmc" or config.get_platform()=="xbmcdharma":
		from pelisalacarta import buscador
		texto = buscador.teclado()
		texto = texto.split()
		item.extra = texto[0]

	itemlist = resultados(item)

	return itemlist
	
def resultados(item):
    
    logger.info("[islapeliculas.py] resultados")
    teclado = item.extra
    teclado = teclado.capitalize()
    logger.info("[islapeliculas.py] " + teclado)
    item.url = "http://www.buenaisla.com/modules.php?name=Anime-Online"
    # Descarga la página
    data = scrapertools.cachePage(item.url)

    # Extrae las entradas
    patronvideos  = '<td bgcolor="#DEEBFE">(.*?)</td>'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    if DEBUG: scrapertools.printMatches(matches)

    itemlist = []
    for elemento in matches:
        patronvideos = '<a.*?href="(.*?)".*?>.*?>(.*?)(%s)(.*?)</div></a>' % teclado
        matches2 = re.compile(patronvideos,re.DOTALL).findall(elemento)

        for match in matches2:
            scrapedurl = urlparse.urljoin("http://www.buenaisla.com/",match[0])
            scrapedtitle = match[1] + match[2] + match[3]
            scrapedthumbnail = ""
            scrapedplot = ""
            logger.info(scrapedtitle)

            # Añade al listado
            itemlist.append( Item(channel=CHANNELNAME, action="listacapitulos", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )
		
    return itemlist