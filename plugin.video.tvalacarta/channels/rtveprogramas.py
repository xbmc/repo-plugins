# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# tvalacarta - XBMC Plugin
# Canal para programas de RTVE
# http://blog.tvalacarta.info/plugin-xbmc/tvalacarta/
#------------------------------------------------------------

import urlparse,urllib2,urllib,re
import os
import sys
import xbmc
import xbmcgui
import xbmcplugin
import scrapertools
import binascii
import xbmctools
import rtve

try:
	pluginhandle = int( sys.argv[ 1 ] )
except:
	pluginhandle = ""

xbmc.output("[rtve.py] init")

DEBUG = True
CHANNELNAME = "Programas TVE"
CHANNELCODE = "rtveprogramas"

def mainlist(params,url,category):
	xbmc.output("[rtveprogramas.py] mainlist")

	# Añade al listado de XBMC
	xbmctools.addnewfolder( CHANNELCODE , "espanoles"  , CHANNELNAME        , "Españoles en el mundo" , "http://www.rtve.es/television/espanoles-en-el-mundo/" , "" , "" )
	xbmctools.addnewfolder( CHANNELCODE , "aguilaroja" , CHANNELNAME        , "Águila roja"           , "" , "" , "" )
	xbmctools.addnewfolder( CHANNELCODE , "generico"   , CHANNELNAME        , "Así se hizo"           , "http://www.rtve.es/television/asi-se-hizo/" , "" , "" )
	xbmctools.addnewfolder( CHANNELCODE , "generico"   , CHANNELNAME        , "Días de cine"          , "http://www.rtve.es/television/dias-cine-programas/" , "" , "" )
	xbmctools.addnewfolder( CHANNELCODE , "lasenora"   , CHANNELNAME        , "La señora"             , "" , "" , "" )
	xbmctools.addnewfolder( CHANNELCODE , "generico"   , "allowblanktitles" , "Guante blanco"         , "http://www.rtve.es/television/guanteblanco/capitulos-guante-blanco/" , "" , "" )
	#xbmctools.addnewfolder( CHANNELCODE , "generico"   , CHANNELNAME        , "Azahar"                , "http://www.rtve.es/television/azahar/" , "" , "" )
	#xbmctools.addnewfolder( CHANNELCODE , "generico"   , CHANNELNAME        , "50 años de..."         , "http://www.rtve.es/television/50-de-tve/temporada1/" , "" , "" )

	# Cierra el directorio
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def espanoles(params,url,category):
	xbmc.output("[rtveprogramas.py] espanoles")

	# --------------------------------------------------------
	# Descarga la página
	# --------------------------------------------------------
	data = scrapertools.cachePage(url)
	#xbmc.output(data)

	# --------------------------------------------------------
	# Extrae las categorias (carpetas)
	# --------------------------------------------------------
	#<div class="mark"><div class="news bg01   comp"><span class="imgL"><a href="http://www.rtve.es/television/espanoles-en-el-mundo/camerun/" title="Destino#46 Camerún"><img src="/imagenes/destino46-camerun/1267557505140.jpg" alt="Destino#46 Camerún" title="Destino#46 Camerún"/></a></span><h3 class="M "><a href="http://www.rtve.es/television/espanoles-en-el-mundo/camerun/" title="Destino#46 Camerún">Destino#46 Camerún</a></h3><div class="chapeaux">Este destino es mucho más que un país... es todo un continente. <strong>Vuelve a verlo</strong>.</div></div></div>
	#<div class="mark"><div class="news bg01   comp"><span class="imgT"><a href="http://www.rtve.es/television/espanoles-en-el-mundo/jalisco/" title="Destino#42 Jalisco (México)"><img src="/imagenes/destino42-jalisco-mexico/1264699947886.jpg" alt="Destino#42 Jalisco (México)" title="Destino#42 Jalisco (México)"/></a></span><h3 class="M "><a href="http://www.rtve.es/television/espanoles-en-el-mundo/jalisco/" title="Destino#42 Jalisco (México)">Destino#42 Jalisco (México)</a></h3><div class="chapeaux">¿Sabías que hay mariachis de chicas? ¿De dónde viene el tequila? <strong>Vuelve a verlo</strong>.</div></div></div><div class="mark"><div class="
	patron  = '<div class="mark"><div class="news bg01   comp"><span class="img."><a href="([^"]+)" title="([^"]+)"><img src="([^"]+)" alt="[^"]+" title="[^"]+"/></a></span><h. class=". "><a href="[^"]+" title="[^"]+">([^<]+)</a></h.><div class="chapeaux">([^<]+)<'
	matches = re.compile(patron,re.DOTALL).findall(data)
	if DEBUG: scrapertools.printMatches(matches)

	for match in matches:
		# Datos
		scrapedtitle = scrapertools.entityunescape(match[3])
		scrapedurl = urlparse.urljoin(url, match[0])
		scrapedthumbnail = urlparse.urljoin(url, match[2])
		scrapedplot = match[4]
		if (DEBUG): xbmc.output("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELCODE , "generico" , CHANNELNAME , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# --------------------------------------------------------
	# Descarga la página
	# --------------------------------------------------------
	url = "http://www.rtve.es/television/espanoles-en-el-mundo/programas-anteriores/"
	data = scrapertools.cachePage(url)
	#xbmc.output(data)

	# --------------------------------------------------------
	# Extrae las categorias (carpetas)
	# --------------------------------------------------------
	#<div class="news bg01   comp"><span class="imgT"><a href="http://www.rtve.es/television/espanoles-en-el-mundo/seul/" title="Destino#28 Seúl">
	#<img src="/imagenes/destino28-seul/1264701360856.jpg" alt="Destino#28 Seúl" title="Destino#28 Seúl"/></a></span>
	#<h3 class="M "><a href="http://www.rtve.es/television/espanoles-en-el-mundo/seul/" title="Destino#28 Seúl">Destino#28 Seúl</a></h3><div class="chapeaux"> Viajamos a la capital de Corea del Sur, la segunda urbe más poblada del planeta.<strong> Vuelve a verlo</strong></div>
	patron  = '<div class="news bg01   comp">[^<]*'
	patron += '<span class="img."><a href="([^"]+)" title="[^"]+"><img src="([^"]+)" alt="[^"]+" title="[^"]+"/></a></span>[^<]*'
	patron += '<h. class=". ">[^<]*'
	patron += '<a href="[^"]+" title="([^"]+)">([^<]+)</a>[^<]*'
	patron += '</h.>[^<]*'
	patron += '<div class="chapeaux">(.*?)</div>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	if DEBUG: scrapertools.printMatches(matches)

	for match in matches:
		# Datos
		scrapedtitle = scrapertools.entityunescape(match[3])
		scrapedurl = urlparse.urljoin(url, match[0])
		scrapedthumbnail = urlparse.urljoin(url, match[1])
		scrapedplot = match[4]
		if (DEBUG): xbmc.output("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELCODE , "generico" , CHANNELNAME , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# Cierra el directorio
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def aguilaroja(params,url,category):
	xbmc.output("[rtveprogramas.py] mainlist")

	# Añade al listado de XBMC
	xbmctools.addnewfolder( CHANNELCODE , "generico" , CHANNELNAME , "Temporada 1" , "http://www.rtve.es/television/aguila-roja/capitulos-completos/primera-temporada/"  , "" , "" )
	xbmctools.addnewfolder( CHANNELCODE , "generico" , CHANNELNAME , "Temporada 2" , "http://www.rtve.es/television/aguila-roja/capitulos-completos/segunda-temporada/"  , "" , "" )

	# Cierra el directorio
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def lasenora(params,url,category):
	xbmc.output("[rtveprogramas.py] mainlist")

	# Añade al listado de XBMC
	xbmctools.addnewfolder( CHANNELCODE , "generico" , CHANNELNAME , "Temporada 1" , "http://www.rtve.es/television/la-senora/capitulos-completos/primera-temporada/"  , "" , "" )
	xbmctools.addnewfolder( CHANNELCODE , "generico" , CHANNELNAME , "Temporada 2" , "http://www.rtve.es/television/la-senora/capitulos-completos/segunda-temporada/"  , "" , "" )
	xbmctools.addnewfolder( CHANNELCODE , "generico" , CHANNELNAME , "Temporada 3" , "http://www.rtve.es/television/la-senora/capitulos-completos/tercera-temporada/"  , "" , "" )

	# Cierra el directorio
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def generico(params,url,category):
	xbmc.output("[rtveprogramas.py] generico")

	# El parametro allowblanks permite que haya vídeos sin título
	allowblanktitles = False
	if category=="allowblanktitles":
		allowblanktitles = True
		category = CHANNELNAME
	

	# --------------------------------------------------------
	# Descarga la página
	# --------------------------------------------------------
	data = scrapertools.cachePage(url)
	#xbmc.output(data)

	# --------------------------------------------------------
	# Extrae las categorias (carpetas)
	# --------------------------------------------------------
	patron  = '<div class="news[^"]+">(.*?</div>)'
	bloques = re.compile(patron,re.DOTALL).findall(data)
	if DEBUG: scrapertools.printMatches(bloques)

	for bloque in bloques:
		'''
		##############################################################################################################	
		<span class="imgL"><a href="/mediateca/videos/20100225/aguila-roja-cap21/705225.shtml" title=""><img src="/imagenes/jpg/1267703487420.jpg" alt="" title=""/></a></span>
		<h3 class="M ">
		<a href="/mediateca/videos/20100225/aguila-roja-cap21/705225.shtml" title="Capítulo 21">Capítulo 21</a>
		</h3>
		<div class="chapeaux">Emitido el 25/02/10</div>
		##############################################################################################################	
		<span class="imgL"><a href="/mediateca/videos/20100218/aguila-roja-cap20/698541.shtml" title="Capítulo 20"><img src="/imagenes/capitulo-20/1267703445964.jpg" alt="Capítulo 20" title="Capítulo 20"/></a></span>
		<h3 class="M ">
		<a href="/mediateca/videos/20100218/aguila-roja-cap20/698541.shtml" title="Capítulo 20">Capítulo 20</a>
		</h3>
		<div class="chapeaux">Emitido el 18/02/10</div>
		##############################################################################################################	
		'''
		scrapedtitle = ""
		scrapedurl = ""
		scrapedthumbnail = ""
		scrapedplot = ""

		# Enlace a la página y título
		patron = '<a href="([^"]+)"[^>]+>([^<]+)<'
		matches = re.compile(patron,re.DOTALL).findall(bloque)
		if DEBUG: scrapertools.printMatches(matches)
		if len(matches)>0:
			scrapedurl = urlparse.urljoin(url, matches[0][0])
			scrapedtitle = scrapertools.entityunescape(matches[0][1])
		
		# Si no tiene titulo busca el primer enlace que haya
		if scrapedurl=="":
			# Enlace a la página y título
			patron = '<a href="([^"]+)"'
			matches = re.compile(patron,re.DOTALL).findall(bloque)
			if DEBUG: scrapertools.printMatches(matches)
			if len(matches)>0:
				scrapedurl = urlparse.urljoin(url, matches[0])

		# Thumbnail
		patron = '<img src="([^"]+)"'
		matches = re.compile(patron,re.DOTALL).findall(bloque)
		if DEBUG: scrapertools.printMatches(matches)
		if len(matches)>0:
			scrapedthumbnail = urlparse.urljoin(url, matches[0])

		# Argumento
		patron = '<div class="chapeaux">(.*?)</div>'
		matches = re.compile(patron,re.DOTALL).findall(bloque)
		if DEBUG: scrapertools.printMatches(matches)
		if len(matches)>0:
			scrapedplot = scrapertools.htmlclean(matches[0])

		if (DEBUG): xbmc.output("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")
		
		if allowblanktitles:
			titulos = scrapedurl.split("/")
			scrapedtitle = titulos[ len(titulos)-2 ]

		# Añade al listado de XBMC
		if scrapedtitle<>"" and scrapedurl<>"":
			xbmctools.addnewvideo( "rtve" , "play" , category , "Directo" , scrapedtitle , scrapedurl , scrapedthumbnail , scrapedplot )

	# Cierra el directorio
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )
