# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para capitancinema
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------
import urlparse,urllib2,urllib,re
import os, sys

import scrapertools
import servertools
import logger
import buscador
from item import Item

CHANNELNAME = "capitancinema"
DEBUG = True

def isGeneric():
	return True

def mainlist(item):
	logger.info("[capitancinema.py] mainlist")

	itemlist=[]
	itemlist.append( Item(channel=CHANNELNAME, action="novedades" , title="Películas - Novedades" , url="http://www.capitancinema.com/peliculas-online-novedades.htm"))

	return itemlist

def novedades(item):
	logger.info("[capitancinema.py] novedades")

	# Descarga la página
	data = scrapertools.cachePage(item.url)

	# Extrae las entradas (carpetas)
	patronvideos  = '<td width="23\%"><a href="([^"]+)"[^>]+><img style="[^"]+" src="([^"]+)" border="0" alt="([^"]+)"[^>]+></a></td>'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	itemlist=[]
	for match in matches:
		# Atributos
		scrapedtitle = match[2]
		scrapedtitle = scrapedtitle.replace("&quot;","")
		scrapedtitle = scrapertools.entityunescape(scrapedtitle)
		scrapedurl = urlparse.urljoin(item.url,match[0])
		scrapedthumbnail = urlparse.urljoin(item.url,match[1])
		scrapedplot = ""
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		itemlist.append( Item(channel=CHANNELNAME, action="mirrors", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

	return itemlist

def mirrors(item):
	logger.info("[capitancinema.py] mirrors")

	title = item.title
	thumbnail = item.thumbnail
	plot = item.plot

	# Descarga la página
	data = scrapertools.cachePage(item.url)
	patronvideos  = '<li><strong>DISPONIBLE EN EL FORO</strong>[^<]+<a href="([^"]+)"'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	itemlist = []
	if len(matches)>0:
		url = matches[0]
		data = scrapertools.cachePage(url)

		# ------------------------------------------------------------------------------------
		# Busca los enlaces a los videos
		# ------------------------------------------------------------------------------------
		listavideos = servertools.findvideos(data)

		for video in listavideos:
			scrapedtitle = title.strip() + " - " + video[0]
			scrapedurl = video[1]
			server = video[2]
			
			itemlist.append( Item(channel=CHANNELNAME, action="play" , title=scrapedtitle , url=scrapedurl, thumbnail=item.thumbnail, plot=item.plot, server=server, folder=False))

	return itemlist
