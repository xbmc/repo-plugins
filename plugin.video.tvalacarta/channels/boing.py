# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# tvalacarta - XBMC Plugin
# Canal para boing.es
# http://blog.tvalacarta.info/plugin-xbmc/tvalacarta/
#------------------------------------------------------------
import urlparse,urllib2,urllib,re
import os
import sys
import xbmc
import xbmcgui
import xbmcplugin
import xbmctools
import scrapertools
import binascii

try:
	pluginhandle = int( sys.argv[ 1 ] )
except:
	pluginhandle = ""

xbmc.output("[boing.py] init")

DEBUG = False
CHANNELNAME = "Boing"
CHANNELCODE = "boing"

def mainlist(params,url,category):
	xbmc.output("[boing.py] mainlist")

	# Añade al listado de XBMC
	xbmctools.addnewfolder( CHANNELCODE , "novedades" , CHANNELNAME , "Novedades" , "http://www.boing.es/videos/FFFFFF.xml"  , "" , "" )
	xbmctools.addnewfolder( CHANNELCODE , "series"    , CHANNELNAME , "Series"    , "http://www.boing.es/videos/FFFFFF.xml"  , "" , "" )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def series(params,url,category):
	xbmc.output("[boing.py] series")

	# Descarga la página
	data = scrapertools.cachePage(url)
	#xbmc.output(data)

	# Extrae las entradas (series)
	patronvideos = '<series>(.*?)</series>'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	if DEBUG: scrapertools.printMatches(matches)
	data = matches[0]
	
	patronvideos = '<item id="([^"]+)" nombre="([^"]+)"/>'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	if DEBUG: scrapertools.printMatches(matches)

	for match in matches:
		scrapedtitle = match[1]
		scrapedurl = match[0]
		scrapedthumbnail = "http://www.boing.es/videos/1clips/"+scrapedurl+"/videos/imagen.jpg"
		scrapedplot = ""
		if (DEBUG): xbmc.output("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELCODE , "episodios" , CHANNELNAME , scrapedtitle , scrapedurl , scrapedthumbnail , scrapedplot )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_LABEL )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def episodios(params,url,category):
	xbmc.output("[boing.py] videolist")

	# El título es el de la serie
	title = urllib.unquote_plus( params.get("title") )

	# Descarga la página
	data = scrapertools.cachePage("http://www.boing.es/videos/FFFFFF.xml")
	#xbmc.output(data)

	'''
	<video id="ben10af_ep2_01" series="ben10af" extras="" novedad="0">
	<titulo>Episodio 2  (parte 1)</titulo>
	<imagen>/videos/1clips/ben10af/ep/ep.jpg</imagen>
	<url>http://ht.cdn.turner.com/tbseurope/big/toones/protected_auth/b10af/Ben10_Ep02_Sg01.flv</url>
	<stats>http://www.boing.es/videos/stats/episodios_ben10af.html</stats>
	<descripcion><![CDATA[<a href='/microsites/ben10alienforce/index.jsp' target='_self'><font color='#FF0000'>Pincha</font></a> para visitar la página de Ben 10 Alien Force<br/>Episodios solamente disponibles en España]]></descripcion>
	</video>
	'''

	# Extrae las entradas (videos, el parámetro url es el id de la serie)
	patronvideos  = '<video id="[^"]+" series="'+url+'"[^>]+>[^<]+'
	patronvideos += '<titulo>([^<]+)</titulo>[^<]+'
	patronvideos += '<imagen>([^<]+)</imagen>[^<]+'
	patronvideos += '<url>([^<]+)</url>[^<]+'
	patronvideos += '<stats>[^<]+</stats>[^<]+'
	patronvideos += '<descripcion>(.*?)</descripcion>[^<]+'
	patronvideos += '</video>'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	for match in matches:
		# Titulo
		try:
			scrapedtitle = unicode( match[0], "utf-8" ).encode("iso-8859-1")
		except:
			scrapedtitle = match[0]
		scrapedurl = urlparse.urljoin(url,match[2])
		scrapedthumbnail = urlparse.urljoin(url,match[1])
		try:
			scrapedplot = scrapertools.htmlclean(unicode( match[3], "utf-8" ).encode("iso-8859-1"))
		except:
			scrapedplot = scrapertools.htmlclean(match[3])
		if (DEBUG): xbmc.output("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		xbmctools.addnewvideo( CHANNELCODE , "play" , category , "Directo" , title + " - " + scrapedtitle , scrapedurl , scrapedthumbnail , scrapedplot )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_LABEL )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def novedades(params,url,category):
	xbmc.output("[boing.py] videolist")

	# Descarga la página
	data = scrapertools.cachePage(url)
	#xbmc.output(data)

	'''
	<video id="naruto_promo" extras="naruto" novedad="1" promo="">
	<titulo>Naruto en Boing FDF</titulo>
	<imagen>/videos/extras/naruto/thumb.jpg</imagen>
	<url>http://ht.cdn.turner.com/tbseurope/big/toones/naruto/PromoNaruto.flv</url>
	<stats>http://www.boing.es/videos/stats/clips.html</stats>			
	<descripcion><![CDATA[<a href='/microsites/naruto/index.jsp' target='_self'><font color='#FF0000'>Pincha</font></a> para visitar la página de Naruto para Juegos y Descargas]]></descripcion>
	</video>
	'''

	# Extrae las entradas (videos, el parámetro url es el id de la serie)
	patronvideos  = '<video id="[^"]+" extras="([^"]+)"[^>]+>[^<]+'
	patronvideos += '<titulo>([^<]+)</titulo>[^<]+'
	patronvideos += '<imagen>([^<]+)</imagen>[^<]+'
	patronvideos += '<url>([^<]+)</url>[^<]+'
	patronvideos += '<stats>[^<]+</stats>[^<]+'
	patronvideos += '<descripcion>(.*?)</descripcion>[^<]+'
	patronvideos += '</video>'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	for match in matches:
		# Titulo
		try:
			scrapedtitle = match[0] + " - " + unicode( match[1], "utf-8" ).encode("iso-8859-1")
		except:
			scrapedtitle = match[1]
		scrapedurl = urlparse.urljoin(url,match[3])
		scrapedthumbnail = urlparse.urljoin(url,match[2])
		try:
			scrapedplot = scrapertools.htmlclean(unicode( match[4], "utf-8" ).encode("iso-8859-1"))
		except:
			scrapedplot = scrapertools.htmlclean(match[4])
		if (DEBUG): xbmc.output("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		xbmctools.addnewvideo( CHANNELCODE , "play" , category , "Directo" , scrapedtitle , scrapedurl , scrapedthumbnail , scrapedplot )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_LABEL )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def play(params,url,category):
	xbmc.output("[boing.py] play")

	title = unicode( xbmc.getInfoLabel( "ListItem.Title" ), "utf-8" )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = unicode( xbmc.getInfoLabel( "ListItem.Plot" ), "utf-8" )
	server = "Directo"

	xbmctools.playvideo(CHANNELNAME,server,url,category,title,thumbnail,plot)
