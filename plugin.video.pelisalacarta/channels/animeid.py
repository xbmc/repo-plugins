# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para animeid
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------
import urlparse,urllib2,urllib,re
import os, sys

import scrapertools
import servertools
import logger
import buscador
from item import Item

CHANNELNAME = "animeid"
DEBUG = True

def isGeneric():
	return True

def mainlist(item):
	logger.info("[animeid.py] mainlist")
	
	itemlist = []
	itemlist.append( Item(channel=CHANNELNAME, action="newlist"  , title="Novedades"              , url="http://animeid.com/" ))
	itemlist.append( Item(channel=CHANNELNAME, action="fulllist" , title="Listado completo"       , url="http://animeid.com/" ))
	itemlist.append( Item(channel=CHANNELNAME, action="catlist"  , title="Listado por categorias" , url="http://animeid.com/anime/amagami-ss.html" ))

	return itemlist

def catlist(item):

	# Descarga la página
	data = scrapertools.downloadpageGzip(item.url)
	#logger.info(data)

	# Extrae las entradas (carpetas)  <a class="accion linkFader" href="../accion-1.html"></a>
	patronvideos  = '<a class="([^"]+)" href="([^"]+)"></a>'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	itemlist = []
	
	for match in matches:
		scrapedtitle = match[0].replace("linkFader","").strip()
		scrapedurl = urlparse.urljoin(item.url,match[1])
		scrapedthumbnail = ""
		scrapedplot = ""
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		itemlist.append( Item(channel=CHANNELNAME, action="newlist" , title=scrapedtitle , url=scrapedurl, thumbnail=scrapedthumbnail, plot=scrapedplot))

	return itemlist

def fulllist(item):

	# Descarga la página
	data = scrapertools.downloadpageGzip(item.url)
	#logger.info(data)

	# Extrae las entradas (carpetas)
	patronvideos  = '<li><a href="([^"]+)"><span>([^<]+)</span></a></li>'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	itemlist = []
	
	for match in matches:
		scrapedtitle = match[1]
		scrapedurl = urlparse.urljoin(item.url,match[0])
		scrapedthumbnail = ""
		scrapedplot = ""
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		itemlist.append( Item(channel=CHANNELNAME, action="detail" , title=scrapedtitle , url=scrapedurl, thumbnail=scrapedthumbnail, plot=scrapedplot))

	return itemlist

def newlist(item):

	# Descarga la página
	data = scrapertools.downloadpageGzip(item.url)
	#logger.info(data)

	# Extrae las entradas (carpetas)
	patronvideos  = '<div class="item">.*?<a href="([^"]+)"[^<]+<img src="([^"]+)".*?<div class="cover boxcaption">[^<]+<h1>([^<]+)</h1>'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	itemlist = []
	for match in matches:
		scrapedtitle = match[2]
		scrapedurl = urlparse.urljoin(item.url,match[0])
		scrapedthumbnail = urlparse.urljoin(item.url,match[1])
		scrapedplot = ""
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		itemlist.append( Item(channel=CHANNELNAME, action="detail" , title=scrapedtitle , url=scrapedurl, thumbnail=scrapedthumbnail, plot=scrapedplot))

	return itemlist

def detail(item):
	logger.info("[animeid.py] detail")

	url = item.url
	title = item.title
	thumbnail = item.thumbnail

	# Descarga la página
	data = scrapertools.downloadpageGzip(url)
	
	#logger.info(data)
	
	# Extrae el argumento
	patronvideos = '<div class="contenido">.*<p>([^<]+)<'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)
	plot = ""
	if len(matches)>0:
		plot=matches[0]

	# Extrae las entradas (capítulos)
	patronvideos  = '<div class="contenido-titulo">[^<]+'
	patronvideos += '<h2>Lista de Capitulos de [^<]+</h2>[^<]+'
	patronvideos += '</div>[^<]+'
	patronvideos += '<div class="contenido">(.*?)</div>'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)
	if len(matches)>0:
		data = matches[0]

	patronvideos = '<a href="([^"]+)"[^>]+>([^<]+)</a>'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	itemlist = []
	
	for match in matches:
		scrapedtitle = match[1]
		scrapedurl = urlparse.urljoin(url,match[0])
		scrapedthumbnail = thumbnail
		scrapedplot = plot
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		itemlist.append( Item(channel=CHANNELNAME, action="detail2" , title=scrapedtitle , url=scrapedurl, thumbnail=scrapedthumbnail, plot=scrapedplot))

	patronvideos = "<a href='([^']+)' target='_blank'>([^<]+)</a>"
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	for match in matches:
		scrapedtitle = match[1]
		scrapedurl = urlparse.urljoin(url,match[0])
		scrapedthumbnail = thumbnail
		scrapedplot = plot
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		itemlist.append( Item(channel=CHANNELNAME, action="detail2" , title=scrapedtitle , url=scrapedurl, thumbnail=scrapedthumbnail, plot=scrapedplot))

	# Extrae las entradas (capítulos)
	patronvideos = '<param name="flashvars" value="file=([^\&]+)&'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)
	if len(matches)>0:
		scrapedurl = matches[0]
		itemlist.append( Item(channel=CHANNELNAME, action="play" , title=title , url=scrapedurl, thumbnail=thumbnail, plot=plot, server="Directo", folder=False))

	return itemlist

def detail2(item):
	logger.info("[animeid.py] detail2")
	
	url = item.url
	title = item.title
	thumbnail = item.thumbnail
	plot = item.plot
	itemlist = []
	
	scrapedurl = ""
	# Lee la página con el player
	data = scrapertools.downloadpageGzip(url)
	#logger.info(data)
	
	patronvideos = '(?:file=|video_src=)([^\&]+)\&'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	if len(matches)>0:
		import urlparse 
		
		c= 0
		scrapedurl = ""
		for match in matches:
			parsedurl = urlparse.urlparse(match)
			parsedurl2 = parsedurl[1].split(".")
			parsedurl3 = parsedurl2[len(parsedurl2)-2]
			if parsedurl3 in scrapedurl:
				c += 1
			else:
				c =1
			scrapedurl = match
			server = 'Directo'
			scrapedtitle = title + " - parte %d [%s] [%s]" %(c,parsedurl[1],server)
		
			if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+thumbnail+"]")
			itemlist.append( Item(channel=CHANNELNAME, action="play" , title=scrapedtitle , url=scrapedurl, thumbnail=thumbnail, plot=plot, server=server, folder=False))
	
	patronvideos = 'http://[^\.]+.megavideo.com[^\?]+\?v=([A-Z0-9a-z]{8})'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	if len(matches)>0:
		scrapedurl = matches[0]
		scrapedtitle = title + " - [%s]" %server
		server = 'Megavideo'
		
		if (DEBUG): logger.info("title=["+title+"], url=["+scrapedurl+"], thumbnail=["+thumbnail+"]")
		itemlist.append( Item(channel=CHANNELNAME, action="play" , title=scrapedtitle , url=scrapedurl, thumbnail=thumbnail, plot=plot, server=server, folder=False))
		
	return itemlist
