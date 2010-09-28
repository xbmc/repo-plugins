# -*- coding: utf-8 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para tupornotv
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
import buscador

CHANNELNAME = "tupornotv"

# Esto permite su ejecución en modo emulado
try:
	pluginhandle = int( sys.argv[ 1 ] )
except:
	pluginhandle = ""

# Traza el inicio del canal
logger.info("[tupornotv.py] init")

DEBUG = True

def mainlist(params,url,category):
	logger.info("[tupornotv.py] mainlist")
	
	itemlist = getmainlist(params,url,category)
	xbmctools.renderItems(itemlist, params, url, category)

def getmainlist(params,url,category):
	logger.info("[tupornotv.py] getmainlist")

	itemlist = []
	itemlist.append( Item( channel=CHANNELNAME , title="Novedades" , action="novedades" , url="http://tuporno.tv/" , folder=True ) )
	itemlist.append( Item( channel=CHANNELNAME , title="Categorias" , action="categorias" , url="http://tuporno.tv/" , folder=True ) )
	itemlist.append( Item( channel=CHANNELNAME , title="Videos Recientes" , action="novedades" , url="http://tuporno.tv/videosRecientes/" , folder=True ) )
	itemlist.append( Item( channel=CHANNELNAME , title="Top Videos (mas votados)" , action="masVotados" , url="http://tuporno.tv/topVideos/" , folder=True ) )
	itemlist.append( Item( channel=CHANNELNAME , title="Nube de Tags" , action="categorias" , url="http://tuporno.tv/" , folder=True ) )
	itemlist.append( Item( channel=CHANNELNAME , title="Buscar" , action="buscar" , url="http://tuporno.tv/" , folder=True ) )
	
	return itemlist

def masVotados(params,url,category):
	logger.info("[tupornotv.py] masVotadas")
	
	itemlist = getmasVotados(params,url,category)
	xbmctools.renderItems(itemlist, params, url, category)
	
def novedades(params,url,category):
	logger.info("[tupornotv.py] novedades")

	itemlist = getnovedades(params,url,category)
	xbmctools.renderItems(itemlist, params, url, category)

def categorias(params,url,category):
	logger.info("[tupornotv.py] categorias")

	itemlist = getcategorias(params,url,category)
	xbmctools.renderItems(itemlist, params, url, category)
	
def buscar(params,url,category):
	logger.info("[tupornotv.py] buscar")
	
	buscador.listar_busquedas(params,url,category)
	
def searchresults(params,Url,category):
	logger.info("[tupornotv.py] searchresults")
	
	buscador.salvar_busquedas(params,Url,category)
	url = "http://www.tuporno.tv/buscador/?str=%s" %Url
	itemlist = getsearchresults(params,url,category)
	xbmctools.renderItems(itemlist, params, url, category)
	
def nextsearchpage(params,url,category):
	logger.info("[tupornotv.py] nextsearchpage")
	
	itemlist = getsearchresults(params,url,category)
	xbmctools.renderItems(itemlist, params, url, category)	
	
def getmasVotados(params,url,category):
	logger.info("[tupornotv.py] getmasVotadas")
	
	itemlist = []
	itemlist.append( Item( channel=CHANNELNAME , title="Hoy" , action="novedades" , url="http://tuporno.tv/topVideos/todas/hoy" , folder=True ) )
	itemlist.append( Item( channel=CHANNELNAME , title="Recientes" , action="novedades" , url="http://tuporno.tv/topVideos/todas/recientes" , folder=True ) )
	itemlist.append( Item( channel=CHANNELNAME , title="Semana" , action="novedades" , url="http://tuporno.tv/topVideos/todas/semana" , folder=True ) )
	itemlist.append( Item( channel=CHANNELNAME , title="Mes" , action="novedades" , url="http://tuporno.tv/topVideos/todas/mes" , folder=True ) )
	itemlist.append( Item( channel=CHANNELNAME , title="Año" , action="novedades" , url="http://tuporno.tv/topVideos/todas/ano" , folder=True ) )
	
	return itemlist	

def getsearchresults(params,url,category):
	logger.info("[tupornotv.py] getsearchresults")

	# ------------------------------------------------------
	# Descarga la página
	# ------------------------------------------------------
	data = scrapertools.cachePage(url)
	#logger.info(data)

	# ------------------------------------------------------
	# Extrae las entradas
	# ------------------------------------------------------
	# seccion busquedas
	'''
	<td align="left"><a href="/videos/cumpleanos_4"><img src="/imagenes/videos//c/u/cumpleanos_4_imagen2.jpg" alt="cumpleaños" border="0" /></a></td>
    <td width="100%" rowspan="2" valign="top" class="datos">
	<h2><a href="/videos/cumpleanos_4">cumpleaños</a> <span class="tmp">1:53</span></h2>
	'''
	
	patronvideos = '<td align="left"><a href="(.videos[^"]+)"><img src="([^"]+)" alt="([^"]+)"'

	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	if DEBUG: scrapertools.printMatches(matches)

	itemlist = []
	for match in matches:
		# Titulo
		scrapedtitle = match[2].replace("<b>","").replace("</b>","")
		scrapedurl = urlparse.urljoin(url,match[0])
		scrapedthumbnail = urlparse.urljoin(url,match[1])
		scrapedplot = ""
		logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		itemlist.append( Item(channel=CHANNELNAME, action="play", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=False) )


	
	# ------------------------------------------------------
	# Extrae el paginador
	# ------------------------------------------------------
	#<a href="/buscador/?str=pillada&desde=2" class="enlace_si">Siguiente </a>
	
	patronvideos  = '<a href="([^"]+)" class="enlace_si">Siguiente </a>'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	if len(matches)>0:
		scrapedurl = urlparse.urljoin(url,matches[0])
		itemlist.append( Item(channel=CHANNELNAME, action="nextsearchpage", title="!Next page" , url=scrapedurl , folder=True) )
	
	
	return itemlist


def getnovedades(params,url,category):
	logger.info("[tupornotv.py] getnovedades")

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
	<table border="0" cellpadding="0" cellspacing="0" ><tr><td align="center" width="100%" valign="top" height="160px">
	<a href="/videos/cogiendo-en-el-bosque"><img src="imagenes/videos//c/o/cogiendo-en-el-bosque_imagen2.jpg" alt="Cogiendo en el bosque" border="0" align="top" /></a>
	<h2><a href="/videos/cogiendo-en-el-bosque">Cogiendo en el bosque</a></h2>
	'''
	patronvideos  = '(?:<table border="0" cellpadding="0" cellspacing="0" ><tr><td align="center" width="100." valign="top" height="160px">|<td align="center" valign="top" width="25%">)[^<]+'
	patronvideos += '<a href="(.videos[^"]+)"><img src="([^"]+)" alt="([^"]+)"'

	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	if DEBUG: scrapertools.printMatches(matches)

	itemlist = []
	for match in matches:
		# Titulo
		scrapedtitle = match[2]
		scrapedurl = urlparse.urljoin(url,match[0])
		scrapedthumbnail = urlparse.urljoin(url,match[1])
		scrapedplot = ""
		logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		itemlist.append( Item(channel=CHANNELNAME, action="play", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=False) )


	
	# ------------------------------------------------------
	# Extrae el paginador
	# ------------------------------------------------------
	#<a href="/topVideos/todas/mes/2/" class="enlace_si">Siguiente </a>
	patronvideos  = '<a href="([^"]+)" class="enlace_si">Siguiente </a>'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	if len(matches)>0:
		scrapedurl = urlparse.urljoin(url,matches[0])
		itemlist.append( Item(channel=CHANNELNAME, action="novedades", title="!Next page" , url=scrapedurl , folder=True) )
	
	
	return itemlist

def getcategorias(params,url,category):
	logger.info("[tupornotv.py] getcategorias")

	# ------------------------------------------------------
	# Descarga la página
	# ------------------------------------------------------
	data = scrapertools.cachePage(url)
	#logger.info(data)
	title = urllib.unquote_plus( params.get("title") )
	# ------------------------------------------------------
	# Extrae las entradas
	# ------------------------------------------------------
	# seccion categorias
	# Patron de las entradas
	if title == "Categorias":
		patronvideos  = '<li><a href="([^"]+)"'      # URL
		patronvideos += '>([^<]+)</a></li>'          # TITULO
	else:
		patronvideos  = '<a href="(.tags[^"]+)"'     # URL
		patronvideos += ' class="[^"]+">([^<]+)</a>'    # TITULO
	
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	if DEBUG: scrapertools.printMatches(matches)

	itemlist = []
	for match in matches:
		if match[1] in ["SexShop","Videochat","Videoclub"]:
			continue
		# Titulo
		scrapedtitle = match[1]
		scrapedurl = urlparse.urljoin(url,match[0])
		scrapedthumbnail = ""
		scrapedplot = ""
		logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		itemlist.append( Item(channel=CHANNELNAME, action="novedades", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )
	return itemlist

def play(params,url,category):
	logger.info("[tupornotv.py] play")

	title = urllib.unquote_plus( params.get("title") )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = unicode( xbmc.getInfoLabel( "ListItem.Plot" ), "utf-8" )
	server = "Directo"
	
	#http://tuporno.tv/videos/adolescentes-trio-follando-18
	#http://149.12.64.129/videoscodiH264/a/d/adolescentes-trio-follando-18.flv
	
	trozos = url.split("/")
	id = trozos[len(trozos)-1]
	url = "http://149.12.64.129/videoscodiH264/"+id[0:1]+"/"+id[1:2]+"/"+id+".flv"
	logger.info("url="+url)

	xbmctools.playvideo(CHANNELNAME,server,url,category,title,thumbnail,plot)

def addfolder(nombre,url,accion):
	logger.info('[tupornotv.py] addfolder( "'+nombre+'" , "' + url + '" , "'+accion+'")"')
	listitem = xbmcgui.ListItem( nombre , iconImage="DefaultFolder.png")
	itemurl = '%s?channel=tupornotv&action=%s&category=%s&url=%s' % ( sys.argv[ 0 ] , accion , urllib.quote_plus(nombre) , url )
	xbmcplugin.addDirectoryItem( handle = int(sys.argv[ 1 ]), url = itemurl , listitem=listitem, isFolder=True)

def addvideo(nombre,url,category,server):
	logger.info('[tupornotv.py] addvideo( "'+nombre+'" , "' + url + '" , "'+server+'")"')
	listitem = xbmcgui.ListItem( nombre, iconImage="DefaultVideo.png" )
	listitem.setInfo( "video", { "Title" : nombre, "Plot" : nombre } )
	itemurl = '%s?channel=tupornotv&action=play&category=%s&url=%s&server=%s' % ( sys.argv[ 0 ] , category , url , server )
	xbmcplugin.addDirectoryItem( handle=int(sys.argv[ 1 ]), url=itemurl, listitem=listitem, isFolder=False)

def addthumbnailfolder( scrapedtitle , scrapedurl , scrapedthumbnail , accion ):
	logger.info('[tupornotv.py] addthumbnailfolder( "'+scrapedtitle+'" , "' + scrapedurl + '" , "'+scrapedthumbnail+'" , "'+accion+'")"')
	listitem = xbmcgui.ListItem( scrapedtitle, iconImage="DefaultFolder.png", thumbnailImage=scrapedthumbnail )
	itemurl = '%s?channel=tupornotv&action=%s&category=%s&url=%s' % ( sys.argv[ 0 ] , accion , urllib.quote_plus( scrapedtitle ) , urllib.quote_plus( scrapedurl ) )
	xbmcplugin.addDirectoryItem( handle = int(sys.argv[ 1 ]), url = itemurl , listitem=listitem, isFolder=True)
