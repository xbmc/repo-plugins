# -*- coding: utf-8 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para anifenix
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------
import urlparse,urllib2,urllib,re
import os
import sys
import xbmc
import xbmcgui
import xbmcplugin
import scrapertools
import megavideo
import servertools
import binascii
import xbmctools
import config
from item import Item
import logger

CHANNELNAME = "anifenix"

# Esto permite su ejecución en modo emulado
try:
	pluginhandle = int( sys.argv[ 1 ] )
except:
	pluginhandle = ""

# Traza el inicio del canal
logger.info("[anifenix.py] init")

DEBUG = True

def mainlist(params,url,category):
	logger.info("[anifenix.py] mainlist")
	
	itemlist = getmainlist(params,url,category)
	xbmctools.renderItems(itemlist, params, url, category)

def getmainlist(params,url,category):
	logger.info("[anifenix.py] getmainlist")

	itemlist = []
	itemlist.append( Item( channel=CHANNELNAME , title="Novedades" , action="novedades" , url="http://anifenix.com/" , folder=True ) )
	
	return itemlist

def novedades(params,url,category):
	logger.info("[anifenix.py] novedades")

	itemlist = getnovedades(params,url,category)
	xbmctools.renderItems(itemlist, params, url, category)

def getnovedades(params,url,category):
	logger.info("[anifenix.py] getnovedades")

	# ------------------------------------------------------
	# Descarga la página
	# ------------------------------------------------------
	data = scrapertools.cachePage(url)
	#logger.info(data)

	# ------------------------------------------------------
	# Extrae las entradas
	# ------------------------------------------------------
	# seccion novedades
	'''
	<!--DWLayoutTable-->
	<tr>
	<td width="220" height="301" valign="top"><table width="100%" border="0" cellpadding="0" cellspacing="0">
	<!--DWLayoutTable-->
	<tr>
	<td height="214" colspan="2" valign="top"><a href="descripcion.php?ns=Another lady innocent"><img src="../Administracion/Noticias/archivos/33bd660(cab).jpg" alt="" width="214" height="212" border="0" /></a></td>
	<td width="6" rowspan="2" valign="top"><!--DWLayoutEmptyCell-->&nbsp;</td>
	</tr>
	<tr>
	<td width="107" height="87" valign="top"><img src="../Administracion/Noticias/archivos/th_51143_2_123_237lo(cab_sub_1).jpg" width="106" height="87" alt="" /></td>
	<td width="107" align="right" valign="top"><a href="descripcion.php?ns=Another lady innocent"><img src="../Administracion/Noticias/archivos/th_51147_4_123_414lo(cab_sub_2).jpg" alt="" width="106" height="87" border="0" /></a></td>
	</tr>
	</table>             </td>
	<td width="334" valign="top"><p align="center"><span class="Estilo57" style="margin:0px"><a href="serie-hentai-online-Another lady innocent.html">Serie hentai Online: Another lady innocent</a></span></p>
	'''

	patronvideos  = '<!--DWLayoutTable-->.*?<!--DWLayoutTable-->.*?<img src="([^"]+)".*?'
	patronvideos += '<span class="Estilo57"[^>]+><a href="([^"]+)">([^<]+)</a></span>.*?'
	patronvideos += '<p class="Estilo59">(.*?)</p>'


	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	if DEBUG: scrapertools.printMatches(matches)

	itemlist = []
	for match in matches:
		# Titulo
		scrapedtitle = match[2]
		scrapedurl = urlparse.urljoin(url,match[1])
		scrapedthumbnail = urlparse.urljoin(url,match[0][2:])
		scrapedplot = scrapertools.htmlclean(match[3].strip())
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		itemlist.append( Item(channel=CHANNELNAME, action="capitulos", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

	# ------------------------------------------------------
	# Extrae el paginador
	# ------------------------------------------------------
	patronvideos  = '<a href="(\/index.php\?pageNum[^"]+)">[^<]+</a></span>'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	if len(matches)>0:
		scrapedurl = urlparse.urljoin(url,matches[0])
		itemlist.append( Item(channel=CHANNELNAME, action="novedades", title="!Página siguiente" , url=scrapedurl , folder=True) )

	return itemlist

def capitulos(params,url,category):
	logger.info("[anifenix.py] capitulos")
	
	itemlist = getcapitulos(params,url,category)
	xbmctools.renderItems(itemlist, params, url, category)

def getcapitulos(params,url,category):
	logger.info("[anifenix.py] getcapitulos")

	title = urllib.unquote_plus( params.get("title") )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = urllib.unquote_plus( params.get("plot") )

	# ------------------------------------------------------------------------------------
	# Descarga la página
	# ------------------------------------------------------------------------------------
	data = scrapertools.cachePage(url)
	#logger.info(data)
	
	# ------------------------------------------------------------------------------------
	# Busca el argumento
	# ------------------------------------------------------------------------------------
	patronvideos  = '<div class="ficha_des">(.*?)</div>'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	if len(matches)>0:
		plot = scrapertools.htmlclean(matches[0])
		logger.info("plot actualizado en detalle");
	else:
		logger.info("plot no actualizado en detalle");
	
	# ------------------------------------------------------------------------------------
	# Busca los enlaces a los mirrors, o a los capítulos de las series...
	# ------------------------------------------------------------------------------------
	'''
	<a href="video-hentai-2349.html"><strong>Episodio 01(sub Ingles) sorry..</strong></a>
	'''
	patronvideos  = '<a href="(video-hentai[^"]+)"><strong>([^<]+)</strong></a>'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	
	itemlist = []
	for match in matches:
		# Titulo
		scrapedtitle = match[1]
		scrapedurl = urlparse.urljoin(url,match[0])
		scrapedthumbnail = thumbnail
		scrapedplot = plot
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		itemlist.append( Item(channel=CHANNELNAME, action="detail", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

	return itemlist

def detail(params,url,category):
	logger.info("[anifenix.py] detail")

	title = urllib.unquote_plus( params.get("title") )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = urllib.unquote_plus( params.get("plot") )

	# Descarga la página
	data = scrapertools.cachePage(url)
	#logger.info(data)

	# ------------------------------------------------------------------------------------
	# Busca los enlaces a los videos
	# ------------------------------------------------------------------------------------
	listavideos = servertools.findvideos(data)

	for video in listavideos:
		videotitle = video[0]
		url = video[1]
		server = video[2]
		xbmctools.addnewvideo( CHANNELNAME , "play" , category , server , title.strip() + " - " + videotitle , url , thumbnail , plot )
	# ------------------------------------------------------------------------------------

	# Cierra el directorio
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def play(params,url,category):
	logger.info("[anifenix.py] play")

	title = urllib.unquote_plus( params.get("title") )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = unicode( xbmc.getInfoLabel( "ListItem.Plot" ), "utf-8" )
	server = params["server"]

	xbmctools.playvideo(CHANNELNAME,server,url,category,title,thumbnail,plot)

def addfolder(nombre,url,accion):
	logger.info('[anifenix.py] addfolder( "'+nombre+'" , "' + url + '" , "'+accion+'")"')
	listitem = xbmcgui.ListItem( nombre , iconImage="DefaultFolder.png")
	itemurl = '%s?channel=anifenix&action=%s&category=%s&url=%s' % ( sys.argv[ 0 ] , accion , urllib.quote_plus(nombre) , url )
	xbmcplugin.addDirectoryItem( handle = int(sys.argv[ 1 ]), url = itemurl , listitem=listitem, isFolder=True)

def addvideo(nombre,url,category,server):
	logger.info('[anifenix.py] addvideo( "'+nombre+'" , "' + url + '" , "'+server+'")"')
	listitem = xbmcgui.ListItem( nombre, iconImage="DefaultVideo.png" )
	listitem.setInfo( "video", { "Title" : nombre, "Plot" : nombre } )
	itemurl = '%s?channel=anifenix&action=play&category=%s&url=%s&server=%s' % ( sys.argv[ 0 ] , category , url , server )
	xbmcplugin.addDirectoryItem( handle=int(sys.argv[ 1 ]), url=itemurl, listitem=listitem, isFolder=False)

def addthumbnailfolder( scrapedtitle , scrapedurl , scrapedthumbnail , accion ):
	logger.info('[anifenix.py] addthumbnailfolder( "'+scrapedtitle+'" , "' + scrapedurl + '" , "'+scrapedthumbnail+'" , "'+accion+'")"')
	listitem = xbmcgui.ListItem( scrapedtitle, iconImage="DefaultFolder.png", thumbnailImage=scrapedthumbnail )
	itemurl = '%s?channel=anifenix&action=%s&category=%s&url=%s' % ( sys.argv[ 0 ] , accion , urllib.quote_plus( scrapedtitle ) , urllib.quote_plus( scrapedurl ) )
	xbmcplugin.addDirectoryItem( handle = int(sys.argv[ 1 ]), url = itemurl , listitem=listitem, isFolder=True)
