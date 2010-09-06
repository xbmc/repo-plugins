# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# tvalacarta - XBMC Plugin
# Canal para 7rm
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

try:
	pluginhandle = int( sys.argv[ 1 ] )
except:
	pluginhandle = ""

xbmc.output("[sieterm.py] init")

DEBUG = True
CHANNELNAME = "sieterm"
CHANNELCODE = "sieterm"

def mainlist(params,url,category):
	xbmc.output("[sieterm.py] mainlist")

	if url=="":
		url="http://www.7rm.es/servlet/rtrm.servlets.ServletLink2?METHOD=LSTBLOGALACARTA&sit=c,6&serv=BlogPortal2&orden=2"

	# Descarga la página
	data = scrapertools.cachePage(url)
	#xbmc.output(data)

	# Extrae las entradas (carpetas)
	'''
	<dt class="alacarta-video">
	<a href="/servlet/rtrm.servlets.ServletLink2?METHOD=DETALLEALACARTA&amp;sit=c,6,ofs,0&amp;serv=BlogPortal2&amp;orden=2&amp;idCarta=57">Azufre Rojo</a> · (archivo m&aacute;s visto 1971 veces)
	</dt>
	<dd style="height:100%;overflow:hidden;">
	<a href="/servlet/rtrm.servlets.ServletLink2?METHOD=DETALLEALACARTA&amp;sit=c,6,ofs,0&amp;serv=BlogPortal2&amp;orden=2&amp;idCarta=57"
	title="Ver los archivos del a la carta">
		<img src="/servlet/rtrm.servlets.Imagenes?METHOD=VERIMAGEN_2496&amp;nombre=azufre_res_150.jpg" alt="Azufre rojo" style="float:left;display:inline;" />
	</a>
		Los grandes temas tratados de manera tan amena como profunda en esta tertulia de 7 Región de Murcia: la felicidad, el cambio climático, las teorías sobre la evolución, la libertad...
	</dd>
	'''
	patron  = '<dt class="alacarta-video">[^<]+'
	patron += '<a href="([^"]+)">([^<]+)</a>[^<]+'
	patron += '</dt>[^<]+'
	patron += '<dd style="height:100%;overflow:hidden;">[^<]+'
	patron += '<a[^<]+'
	patron += '<img src="([^"]+)"[^<]+'
	patron += '</a>([^<]+)</dd>'
	matches = re.compile(patron,re.DOTALL).findall(data)

	for match in matches:
		# Atributos del vídeo
		scrapedtitle = match[1].strip()
		scrapedurl = urlparse.urljoin(url,match[0]).replace("&amp;","&")
		scrapedthumbnail = urlparse.urljoin(url,match[2]).replace("&amp;","&")
		scrapedplot = match[3].strip()
		if (DEBUG): xbmc.output("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELCODE , "videolist" , CHANNELNAME , scrapedtitle , scrapedurl , scrapedthumbnail , scrapedplot )

	patron = '<a class="list-siguientes" href="([^"]+)" title="Ver siguientes a la cartas">Siguiente</a>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	for match in matches:
		# Atributos del vídeo
		scrapedtitle = "Página siguiente"
		scrapedurl = urlparse.urljoin(url,match)
		scrapedthumbnail = ""
		scrapedplot = ""
		if (DEBUG): xbmc.output("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELCODE , "mainlist" , CHANNELNAME , scrapedtitle , scrapedurl , scrapedthumbnail , scrapedplot )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )

	# Disable sorting...
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def videolist(params,url,category):
	xbmc.output("[sieterm.py] videolist")

	# Descarga la página
	data = scrapertools.cachePage(url)
	#xbmc.output(data)

	# Extrae los vídeos
	'''
	<dt class="alacarta-video"><a href="http://www.7rm.es/servlet/rtrm.servlets.ServletLink2?METHOD=DETALLEALACARTA&amp;sit=c,6,ofs,0&amp;serv=BlogPortal2&amp;orden=2&amp;idCarta=36&amp;mId=3214&amp;autostart=TV" title="Ver v&iacute;deo">De la tierra al mar</a> · 22/12/2009 · (1072 veces visto)</dt>
	<dd style="height:100%; overflow:hidden">
	<a href="http://www.7rm.es/servlet/rtrm.servlets.ServletLink2?METHOD=DETALLEALACARTA&amp;sit=c,6,ofs,0&amp;serv=BlogPortal2&amp;orden=2&amp;idCarta=36&amp;mId=3214&amp;autostart=TV" title="Ver v&iacute;deo">
	<img src="http://mediateca.regmurcia.com/MediatecaCRM/ServletLink?METHOD=MEDIATECA&amp;accion=imagen&amp;id=3214" alt="De la tierra al mar" title="De la tierra al mar" style="width:95px" />
	</a>
	En este programa conocemos a Plácido, joven agricultor que nos mostrará la mala situación en que se encuentra el sector, informamos de la campaña 'Dale vida a tu árbol', asistimos a la presentación del libro 'Gestión ambiental. Guía fácil para empresas y profesionales', y nos hacemos eco del malestar de nuestros agricultores con la nueva normativa europea en materia de fitosanitarios, que entrará en vigor en junio de 2011.
	<a href="http://ficheros.7rm.es:3025/Video/3/2/3214_BAJA.mp4">
	<img src="/images/bajarArchivo.gif" alt="Descargar Archivo" title="Descargar Archivo" style="margin:0;padding:0 5px 0 0;vertical-align:middle;border:none" />
	</a>
	</dd>
	'''
	patron  = '<dt class="alacarta-video"><a href="[^"]+" title="[^"]+">([^<]+)</a>.*?([0-9][^\ ]+) · \([^\)]+\)</dt>[^<]+'
	patron += '<dd style="height:100%; overflow:hidden">[^<]+'
	patron += '<a href="[^"]+" title="[^"]+">[^<]+'
	patron += '<img src="([^"]+)"[^<]+'
	patron += '</a>([^<]+)<a href="([^"]+)">'
	matches = re.compile(patron,re.DOTALL).findall(data)

	for match in matches:
		# Atributos del vídeo
		scrapedtitle = match[0].strip()+" ("+match[1]+")"
		scrapedurl = urlparse.urljoin(url,match[4]).replace("&amp;","&")
		scrapedthumbnail = urlparse.urljoin(url,match[2]).replace("&amp;","&")
		scrapedplot = match[3].strip()
		if (DEBUG): xbmc.output("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		xbmctools.addnewvideo( CHANNELCODE , "play" , category , "Directo" , scrapedtitle , scrapedurl , scrapedthumbnail , scrapedplot )

	patron = '<a class="list-siguientes" href="([^"]+)" title="Ver siguientes archivos">'
	matches = re.compile(patron,re.DOTALL).findall(data)
	for match in matches:
		# Atributos del vídeo
		scrapedtitle = "Página siguiente"
		scrapedurl = urlparse.urljoin(url,match)
		scrapedthumbnail = ""
		scrapedplot = ""
		if (DEBUG): xbmc.output("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELCODE , "videolist" , CHANNELNAME , scrapedtitle , scrapedurl , scrapedthumbnail , scrapedplot )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )

	# Disable sorting...
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def play(params,url,category):
	xbmc.output("[sieterm.py] play")

	title = unicode( xbmc.getInfoLabel( "ListItem.Title" ), "utf-8" )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = unicode( xbmc.getInfoLabel( "ListItem.Plot" ), "utf-8" )
	server = "Directo"

	xbmctools.playvideo(CHANNELCODE,server,url,category,title,thumbnail,plot)
