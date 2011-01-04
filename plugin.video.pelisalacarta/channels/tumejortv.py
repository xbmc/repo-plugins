# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para tumejortv
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------
import urlparse,urllib2,urllib,re
import os, sys

import scrapertools
import servertools
import logger
import buscador
from item import Item

CHANNELNAME = "tumejortv"
DEBUG = True

def isGeneric():
	return True

def mainlist(item):
	logger.info("[tumejortv.py] mainlist")
	
	itemlist = []

	itemlist.append( Item(channel=CHANNELNAME, action="newlist"           , title="Novedades" , url="http://www.tumejortv.com/"))
	itemlist.append( Item(channel=CHANNELNAME, action="moviecategorylist" , title="Películas - Por categorías" , url="http://www.tumejortv.com/"))
	itemlist.append( Item(channel=CHANNELNAME, action="moviealphalist"    , title="Películas - Por orden alfabético" , url="http://www.tumejortv.com/"))
	itemlist.append( Item(channel=CHANNELNAME, action="serienewlist"      , title="Series - Novedades" , url="http://www.tumejortv.com/"))
	itemlist.append( Item(channel=CHANNELNAME, action="seriealllist"      , title="Series - Todas" , url="http://www.tumejortv.com/"))
	itemlist.append( Item(channel=CHANNELNAME, action="seriealphalist"    , title="Series - Por orden alfabético" , url="http://www.tumejortv.com/"))
	#itemlist.append( Item(channel=CHANNELNAME, action="search"            , title="Buscar" , ""))

	return itemlist

# TODO: Esto no funciona en canales genéricos
def search(item):
	logger.info("[tumejortv.py] search")

	buscador.listar_busquedas(params,url,category)
	
# TODO: Esto no funciona en canales genéricos
def searchresults(params,tecleado,category):
	logger.info("[tumejortv.py] searchresults")
	
	buscador.salvar_busquedas(params,tecleado,category)
	resultados = performsearch(tecleado)

	for match in resultados:
		targetchannel = match[0]
		action = match[1]
		category = match[2]
		scrapedtitle = match[3]
		scrapedurl = match[4]
		scrapedthumbnail = match[5]
		scrapedplot = match[6]
		
		xbmctools.addnewfolder( targetchannel , action , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

# TODO: Esto no funciona en canales genéricos
def performsearch(texto):
	logger.info("[tumejortv.py] performsearch")
	url = "http://www.tumejortv.com/buscar/?s="+texto+"&x=0&y=0"
	
	# Descarga la página
	resultados = []
	data = scrapertools.cachePage(url)
	#logger.info(data)

	# Extrae las películas
	patron  = "<h3>Pel.iacute.culas online</h3><ul class='alphaList'>(.*?)</ul>"
	matches = re.compile(patron,re.DOTALL).findall(data)
	if DEBUG: scrapertools.printMatches(matches)
	data2 = ""
	if len(matches)>0:
		data2 = matches[0]
	
	patron  = '<li><div class="movieTitle">[^<]+</div><div class="covershot"><a href="([^"]+)" title="([^"]+)"><img src="([^"]+)"'
	matches = re.compile(patron,re.DOTALL).findall(data2)
	if DEBUG: scrapertools.printMatches(matches)

	for match in matches:
		scrapedtitle = match[1]
		scrapedurl = match[0]
		scrapedthumbnail = match[2]
		scrapedplot = ""
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")
		
		# Añade al listado de XBMC
		resultados.append( [CHANNELNAME , "findvideos" , "buscador" , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot ] )

	# Extrae las películas
	patron  = "<h3>Series online</h3><ul class='alphaList'>(.*?)</ul>"
	matches = re.compile(patron,re.DOTALL).findall(data)
	if DEBUG: scrapertools.printMatches(matches)
	if len(matches)>0:
		data2 = matches[0]
	
	patron  = '<li><div class="movieTitle">[^<]+</div><div class="covershot"><a href="([^"]+)" title="([^"]+)"><img src="([^"]+)"'
	matches = re.compile(patron,re.DOTALL).findall(data2)
	if DEBUG: scrapertools.printMatches(matches)

	for match in matches:
		scrapedtitle = match[1]
		scrapedurl = match[0]
		scrapedthumbnail = match[2]
		scrapedplot = ""
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")
		
		# Añade al listado de XBMC
		resultados.append( [CHANNELNAME , "detailserie" , "buscador" , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot ] )

	return resultados

# Listado de novedades de la pagina principal
def newlist(item):
	logger.info("[tumejortv.py] movielist")

	url = item.url
	# Descarga la página
	data = scrapertools.cachePage(url)
	#logger.info(data)

	# Extrae las películas
	patron  = '<div class="item " style="clear:both;">[^<]+'
	patron += '<div class="covershot[^<]+'
	patron += '<a href="([^"]+)"[^<]+<img src="([^"]+)"[^<]+</a>[^<]+'
	patron += '</div>[^<]+'
	patron += '<div class="post-title">[^<]+'
	patron += '<h3><a[^<]+>(.*?)</a>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	if DEBUG: scrapertools.printMatches(matches)

	itemlist = []
	for match in matches:
		scrapedtitle = match[2]
		scrapedtitle = scrapedtitle.replace("<span class=\'smallTitle'>","(")
		scrapedtitle = scrapedtitle.replace("</span>",")")
		scrapedurl = match[0]
		scrapedthumbnail = match[1]
		scrapedplot = ""
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		itemlist.append( Item(channel=CHANNELNAME, action="findvideos" , title=scrapedtitle , url=scrapedurl, thumbnail=scrapedthumbnail, plot=scrapedplot))

	# Extrae la página siguiente
	patron = '<a href="([^"]+)" >&raquo;</a>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	if DEBUG:
		scrapertools.printMatches(matches)

	if len(matches)>0:
		scrapedtitle = "!Pagina siguiente"
		scrapedurl = matches[0]
		scrapedthumbnail = ""
		scrapeddescription = ""
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		itemlist.append( Item(channel=CHANNELNAME, action="newlist" , title=scrapedtitle , url=scrapedurl, thumbnail=scrapedthumbnail, plot=scrapedplot))

	return itemlist

# Listado de películas de una categoria / letra
def shortlist(item):
	logger.info("[tumejortv.py] shortlist")

	url = item.url
	# Descarga la página
	data = scrapertools.cachePage(url)
	#logger.info(data)

	# Extrae las películas
	patron  = '<li><div class="movieTitle">[^<]+</div><div class="covershot">'
	patron += '<a href="([^"]+)" title="([^"]+)"><img src="([^"]+)"[^>]+></a></div></li>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	if DEBUG: scrapertools.printMatches(matches)

	itemlist = []
	for match in matches:
		scrapedtitle = match[1]
		scrapedurl = match[0]
		scrapedthumbnail = match[2]
		scrapedplot = ""
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		itemlist.append( Item(channel=CHANNELNAME, action="findvideos" , title=scrapedtitle , url=scrapedurl, thumbnail=scrapedthumbnail, plot=scrapedplot))

	# Extrae la página siguiente
	patron = '<a href="([^"]+)" >&raquo;</a>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	if DEBUG: scrapertools.printMatches(matches)

	if len(matches)>0:
		scrapedtitle = "!Pagina siguiente"
		scrapedurl = matches[0]
		scrapedthumbnail = ""
		scrapedplot = ""
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		itemlist.append( Item(channel=CHANNELNAME, action="shortlist" , title=scrapedtitle , url=scrapedurl, thumbnail=scrapedthumbnail, plot=scrapedplot))

	return itemlist

# Listado de series de una letra
def shortlistserie(item):
	logger.info("[tumejortv.py] shortlistserie")

	url = item.url
	# Descarga la página
	data = scrapertools.cachePage(url)
	#logger.info(data)

	# Extrae las películas
	patron  = '<li><div class="covershot"><a href="([^"]+)" title="([^"]+)"><img src="([^"]+)"[^>]+></a></div></li>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	if DEBUG: scrapertools.printMatches(matches)

	itemlist = []
	for match in matches:
		scrapedtitle = match[1]
		scrapedurl = match[0]
		scrapedthumbnail = match[2]
		scrapedplot = ""
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		itemlist.append( Item(channel=CHANNELNAME, action="detailserie" , title=scrapedtitle , url=scrapedurl, thumbnail=scrapedthumbnail, plot=scrapedplot))

	# Extrae la página siguiente
	patron = '<a href="([^"]+)" >&raquo;</a>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	if DEBUG: scrapertools.printMatches(matches)

	if len(matches)>0:
		scrapedtitle = "Pagina siguiente"
		scrapedurl = matches[0]
		scrapedthumbnail = ""
		scrapedplot = ""
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		itemlist.append( Item(channel=CHANNELNAME, action="shortlistserie" , title=scrapedtitle , url=scrapedurl, thumbnail=scrapedthumbnail, plot=scrapedplot))

	return itemlist

# Listado de categorias de películas, de la caja derecha de la home
def moviecategorylist(item):
	logger.info("[tumejortv.py] moviecategorylist")

	url = item.url
	data = scrapertools.cachePage(url)
	#logger.info(data)

	# Extrae las películas
	patron  = '<li class="cat-item[^<]+<a href="(http\:\/\/www\.tumejortv\.com\/peliculas\-online\-es\/[^"]+)"[^>]+>([^<]+)</a>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	if DEBUG: scrapertools.printMatches(matches)

	itemlist = []
	for match in matches:
		scrapedtitle = match[1]
		scrapedurl = match[0]
		scrapedthumbnail = ""
		scrapedplot = ""
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		itemlist.append( Item(channel=CHANNELNAME, action="shortlist" , title=scrapedtitle , url=scrapedurl, thumbnail=scrapedthumbnail, plot=scrapedplot))

	return itemlist

# Listado de letras iniciales de película, de la caja derecha de la home
def moviealphalist(item):
	logger.info("[tumejortv.py] moviealphalist")

	# Descarga la página
	url = item.url
	data = scrapertools.cachePage(url)
	#logger.info(data)

	# Extrae las películas
	patron  = '<a href="(http\:\/\/www\.tumejortv\.com\/peliculas-es-con-letra-[^"]+)".*?class="listados_letras">([^<]+)</a>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	if DEBUG: scrapertools.printMatches(matches)

	itemlist = []
	for match in matches:
		scrapedtitle = match[1]
		scrapedurl = match[0]
		scrapedthumbnail = ""
		scrapedplot = ""
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		itemlist.append( Item(channel=CHANNELNAME, action="shortlist" , title=scrapedtitle , url=scrapedurl, thumbnail=scrapedthumbnail, plot=scrapedplot))

	return itemlist

# Listado de letras iniciales de series, de la caja derecha de la home
def seriealphalist(item):
	logger.info("[tumejortv.py] seriealphalist")

	# Descarga la página
	url = item.url
	data = scrapertools.cachePage(url)
	#logger.info(data)

	# Extrae las películas
	patron  = '<a href="(http\:\/\/www\.tumejortv\.com\/series-con-letra-[^"]+)".*?class="listados_letras">([^<]+)</a>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	if DEBUG: scrapertools.printMatches(matches)

	itemlist = []
	for match in matches:
		scrapedtitle = match[1]
		scrapedurl = match[0]
		scrapedthumbnail = ""
		scrapedplot = ""
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		itemlist.append( Item(channel=CHANNELNAME, action="shortlistserie" , title=scrapedtitle , url=scrapedurl, thumbnail=scrapedthumbnail, plot=scrapedplot))

	return itemlist

# Listado de series actualizadas, de la caja derecha de la home
def serienewlist(item):
	logger.info("[tumejortv.py] serienewlist")

	# Descarga la página
	url = item.url
	data = scrapertools.cachePage(url)
	#logger.info(data)

	# Extrae las películas
	patron  = '<span><a href="([^"]+)" title="([^"]+)"><img src="([^"]+)".*?</span>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	if DEBUG: scrapertools.printMatches(matches)

	itemlist = []
	for match in matches:
		scrapedtitle = match[1]
		scrapedurl = match[0]
		scrapedthumbnail = match[2]
		scrapedplot = ""
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		itemlist.append( Item(channel=CHANNELNAME, action="detailserie" , title=scrapedtitle , url=scrapedurl, thumbnail=scrapedthumbnail, plot=scrapedplot))

	return itemlist

# Listado de todas las series, de la caja derecha de la home
def seriealllist(item):
	logger.info("[tumejortv.py] seriealllist")

	# Descarga la página
	url = item.url
	data = scrapertools.cachePage(url)
	#logger.info(data)

	# Extrae las películas
	patron  = "<li class='cat-item[^<]+<a href='(http\:\/\/www\.tumejortv\.com\/series\-tv\-online\/[^']+)'[^>]+>([^<]+)</a></li>"
	matches = re.compile(patron,re.DOTALL).findall(data)
	if DEBUG: scrapertools.printMatches(matches)

	itemlist = []
	for match in matches:
		scrapedtitle = match[1]
		scrapedurl = match[0]
		scrapedthumbnail = ""
		scrapedplot = ""
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		itemlist.append( Item(channel=CHANNELNAME, action="detailserie" , title=scrapedtitle , url=scrapedurl, thumbnail=scrapedthumbnail, plot=scrapedplot))

	return itemlist

# Detalle de un vídeo (peli o capitulo de serie), con los enlaces
def findvideos(item):
	logger.info("[tumejortv.py] findvideos")

	# Descarga la página
	url = item.url
	data = scrapertools.cachePage(url)
	#logger.info(data)

	patron = '<div id="blogitem">[^<]+<p>([^<]+)</p>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	if len(matches)>0:
		plot = matches[0]

	listavideos = servertools.findvideos(data)
	
	itemlist = []
	for video in listavideos:
		scrapedtitle = item.title + " (" + video[2] + ")"
		scrapedurl = video[1]
		scrapedthumbnail = item.thumbnail
		scrapedplot = item.plot
		server = video[2]
		itemlist.append( Item(channel=CHANNELNAME, action="play" , title=scrapedtitle , url=scrapedurl, thumbnail=scrapedthumbnail, plot=scrapedplot, server=server, folder=False))

	return itemlist

# Detalle de una serie, con sus capítulos
def detailserie(item):
	logger.info("[tumejortv.py] detailserie")

	# Descarga la página
	url = item.url
	data = scrapertools.cachePage(url)
	#logger.info(data)

	# ------------------------------------------------------
	#<ul class="linksListados">
	#<li><a href="http://www.tumejortv.com/series-tv-online/babylon-5/babylon-5-temporada-1/capitulo-122-15-15-04-2009.html">Babylon 5, Babylon 5 Temporada 1, Capitulo 122</a></li>
	patron  = '<ul class="linksListados">(.*?)</ul>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	if DEBUG: scrapertools.printMatches(matches)

	itemlist = []
	for match in matches:
		patron2 = '<li><a href="([^"]+)"[^>]+>([^<]+)</a></li>'
		matches2 = re.compile(patron2,re.DOTALL).findall(match)
		if DEBUG:
			scrapertools.printMatches(matches2)

		for match2 in matches2:
			scrapedtitle = match2[1]
			scrapedtitle = scrapedtitle.replace("Temporada ","")
			scrapedtitle = scrapedtitle.replace(", Capitulo ","x")
			scrapedtitle = scrapedtitle.replace("&#215;","x")

			if scrapedtitle.startswith(item.title+", "):
				scrapedtitle = scrapedtitle[ len(item.title)+2 : ]
			
			scrapedurl = match2[0]
			scrapedthumbnail = ""
			scrapedplot = ""

			if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

			itemlist.append( Item(channel=CHANNELNAME, action="findvideos" , title=scrapedtitle , url=scrapedurl, thumbnail=scrapedthumbnail, plot=scrapedplot))

	return itemlist