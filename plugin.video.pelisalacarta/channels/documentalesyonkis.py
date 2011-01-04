# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para documentalesyonkis
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------
import urlparse,urllib2,urllib,re
import os, sys
import DecryptYonkis as Yonkis

import scrapertools
import servertools
import logger
import buscador
from item import Item

CHANNELNAME = "documentalesyonkis"
DEBUG = True

def isGeneric():
	return True

def mainlist(item):
	logger.info("[documentalesyonkis.py] mainlist")
	
	itemlist = []

	itemlist.append( Item(channel=CHANNELNAME, action="lastvideolist" , title="Últimos documentales",url="http://documentales.videosyonkis.com/ultimos-videos.php"))
	itemlist.append( Item(channel=CHANNELNAME, action="allvideolist"  , title="Listado completo",url="http://documentales.videosyonkis.com/lista-videos.php"))

	return itemlist

def lastvideolist(item):
	logger.info("[documentalesyonkis.py] lastvideolist")

	# Descarga la página
	data = scrapertools.cachePage(item.url)
	#logger.info(data)

	# Extrae las entradas (carpetas)
	patronvideos  = '<td><a href="([^"]+)" title="([^"]+)"><img.*?src=\'([^\']+)\'[^>]+>.*?</td>'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	itemlist = []
	
	for match in matches:
		try:
			scrapedtitle = unicode( match[1], "utf-8" ).encode("iso-8859-1")
		except:
			scrapedtitle = match[1]
		scrapedurl = match[0]
		scrapedthumbnail = match[2]
		scrapedplot = ""
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		itemlist.append( Item(channel=CHANNELNAME, action="findvideos" , title=scrapedtitle , url=scrapedurl, thumbnail=scrapedthumbnail, plot=scrapedplot))

	return itemlist

def allvideolist(item):
	logger.info("[documentalesyonkis.py] allvideolist")

	# Descarga la página
	data = scrapertools.cachePage(item.url)
	#logger.info(data)

	# Extrae las entradas (carpetas)
	patronvideos  = '<li> <a href="([^"]+)" title="([^"]+)"><img.*?src=\"([^\"]+)\"[^>]+\/>'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	itemlist = []
	
	for match in matches:
		try:
			scrapedtitle = unicode( match[1], "utf-8" ).encode("iso-8859-1")
		except:
			scrapedtitle = match[1]
		scrapedurl = match[0]
		scrapedthumbnail = match[2]
		scrapedplot = ""
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		itemlist.append( Item(channel=CHANNELNAME, action="findvideos" , title=scrapedtitle , url=scrapedurl, thumbnail=scrapedthumbnail, plot=scrapedplot))

	return itemlist

def findvideos(item):
	logger.info("[documentalesyonkis.py] detail")

	itemlist = []
	# ------------------------------------------------------------------------------------
	# Busca los enlaces a los videos
	# ------------------------------------------------------------------------------------
	data = scrapertools.cachePage(item.url)
	patroniframe = '<iframe src="(http:\/\/documentales\.videosyonkis\.com.*?id=(.*?))" onLoad.*'
	matches = re.compile(patroniframe,re.DOTALL).findall(data)
	#scrapertools.printMatches(matches)
	
	if(len(matches)>0):
		id = matches[0][1]
		logger.info("[documentalesyonkis.py] detail id="+id)
		if "&" in id:
			ids = id.split("&")
			id = ids[0]
		dec = Yonkis.DecryptYonkis()
		id = dec.decryptALT(dec.charting(dec.unescape(id)))
		logger.info("[documentalesyonkis.py] detail id="+id)
		url=id
		itemlist.append( Item(channel=CHANNELNAME, action="play" , title=item.title , url=url, thumbnail=item.thumbnail, plot=item.plot, server="Megavideo", folder=False))
	else:
		itemlist.append( Item(channel=CHANNELNAME, action="" , title="VIDEO NO DISPONIBLE" , url="", thumbnail="", plot=""))
	
	return itemlist