# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para animetakus
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------
import urlparse,urllib2,urllib,re
import os, sys

import scrapertools
import servertools
import logger
import buscador
from item import Item

CHANNELNAME = "animetakus"
DEBUG = True

def isGeneric():
	return True

def mainlist(item):
	logger.info("[animetakus.py] mainlist")

	itemlist = []
	itemlist.append( Item(channel=CHANNELNAME, action="newlist"  , title="Novedades" , url="http://www.animetakus.com/"))
	itemlist.append( Item(channel=CHANNELNAME, action="fulllist" , title="Listado completo" , url="http://www.animetakus.com/"))

	return itemlist

def fulllist(item):
	logger.info("[animetakus.py] fulllist")

	# Descarga la página
	data = scrapertools.cachePage(item.url)
	#logger.info(data)

	# Patron de las entradas
	patron = "<a dir='ltr' href='(http.//www.animetakus.com/search/label/[^']+)'>([^<]+)</a>"
	matches = re.compile(patron,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	# Añade las entradas encontradas
	itemlist = []
	for match in matches:
		# Atributos
		scrapedtitle = match[1]
		scrapedurl = urlparse.urljoin(item.url,match[0])
		scrapedthumbnail = ""
		scrapedplot = ""
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		itemlist.append( Item(channel=CHANNELNAME, action="listmirrors" , title=scrapedtitle , url=scrapedurl, thumbnail=scrapedthumbnail, plot=scrapedplot))

	return itemlist

def newlist(item):
	logger.info("[animetakus.py] listmirrors")

	# Descarga la página
	data = scrapertools.cachePage(item.url)
	#logger.info(data)

	# Extrae las entradas (carpetas)
	# <a href="http://www.animeflv.com/2010/10/shinrei-tantei-yakumo.html"><img style="cursor: pointer; width: 134px; height: 190px;" src="http://2.bp.blogspot.com/_fNPIHUeM0lU/TKs9BiQCVzI/AAAAAAAAD90/ejz5Fu6Eodc/s400/Shinrei+Tantei+Yakumo.png" title="Shinrei Tantei Yakumo" alt="Foto animeflv" id="BLOGGER_PHOTO_ID_5524576464483276594" /></a><
	patron = '<a href="([^"]+)"><img style="[^"]+" src="([^"]+)".*?id="BLOGGER_PHOTO[^>]+></a>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)
	itemlist = []

	for match in matches:
		scrapedtitle = match[0][34:-5]
		scrapedurl = urlparse.urljoin(item.url,match[0])
		scrapedthumbnail = urlparse.urljoin(item.url,match[1])
		scrapedplot = ""
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		itemlist.append( Item(channel=CHANNELNAME, action="listmirrors" , title=scrapedtitle , url=scrapedurl, thumbnail=scrapedthumbnail, plot=scrapedplot))

	# Siguiente página
	#<a onblur="try {parent.deselectBloggerImageGracefully();} catch(e) {}" href="http://www.animetakus.com/2010/02/anime-sin-limites-de-tiempo.html"><img style="margin: 0pt 0pt 10px 10px; float: right; cursor: pointer; width: 42px; height: 42px;" src="http://4.bp.blogspot.com/_JErYxGCbX0M/S4Vh2R2bGAI/AAAAAAAACpc/Yr8yMKMwbng/s400/boton+delante.png"
	patron = '<a onblur="[^"]+" href="([^"]+)"><img style="[^"]+" src=".*?boton.delante.png"'
	matches = re.compile(patron,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	for match in matches:
		scrapedtitle = "Página siguiente"
		scrapedurl = urlparse.urljoin(item.url,match)
		scrapedthumbnail = ""
		scrapedplot = ""
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		itemlist.append( Item(channel=CHANNELNAME, action="newlist" , title=scrapedtitle , url=scrapedurl, thumbnail=scrapedthumbnail, plot=scrapedplot))

	return itemlist

def listmirrors(item):
	logger.info("[animetakus.py] listmirrors")

	title = item.title
	thumbnail = item.thumbnail
	plot = item.plot

	# Descarga la página
	data = scrapertools.cachePage(item.url)
	#logger.info(data)

	patron = '<a style="[^"]+" href="(http.//www.megavideoflv.com[^"]+)" target="_blank">([^<]+)</a>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)
	itemlist = []

	for match in matches:
		scrapedtitle = title + " " + match[1]
		scrapedurl = urlparse.urljoin(item.url,match[0])
		scrapedthumbnail = ""
		scrapedplot = ""
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		itemlist.append( Item(channel=CHANNELNAME, action="findvideos" , title=scrapedtitle , url=scrapedurl, thumbnail=scrapedthumbnail, plot=scrapedplot))

	# Busca vídeos sobre la propia página
	item.url = ""
	itemlist2 = findvideos(item,data)
	for item2 in itemlist2:
		itemlist.append( Item(channel=CHANNELNAME, action="play" , title=item2.title , url=item2.url, thumbnail=item2.thumbnail, plot=item2.plot, server=item2.server, folder=False))

	return itemlist

# Detalle de un vídeo (peli o capitulo de serie), con los enlaces
def findvideos(item,data):
	logger.info("[tumejortv.py] findvideos")

	# Descarga la página
	url = item.url
	if url!="":
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
