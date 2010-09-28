# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para cinegratis
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
import logger
import buscador

CHANNELNAME = "cinegratis"

# Esto permite su ejecución en modo emulado
try:
	pluginhandle = int( sys.argv[ 1 ] )
except:
	pluginhandle = ""

# Traza el inicio del canal
logger.info("[cinegratis.py] init")

DEBUG = True

def mainlist(params,url,category):
	logger.info("[cinegratis.py] mainlist")

	# Añade al listado de XBMC
	xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , "Películas - Novedades"            ,"http://www.cinegratis.net/index.php?module=peliculas","","")
	xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , "Películas - Estrenos"             ,"http://www.cinegratis.net/index.php?module=estrenos","","")
	xbmctools.addnewfolder( CHANNELNAME , "peliscat"   , category , "Películas - Lista por categorías" ,"http://www.cinegratis.net/index.php?module=generos","","")
	xbmctools.addnewfolder( CHANNELNAME , "pelisalfa"  , category , "Películas - Lista alfabética"     ,"","","")
	xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , "Películas - Alojadas en Veoh"     ,"http://www.cinegratis.net/index.php?module=servers&varserver=veoh","","")
	xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , "Películas - Alojadas en Megavideo","http://www.cinegratis.net/index.php?module=servers&varserver=megavideo","","")
	xbmctools.addnewfolder( CHANNELNAME , "listseries" , category , "Series - Novedades"               ,"http://www.cinegratis.net/index.php?module=series","","")
	xbmctools.addnewfolder( CHANNELNAME , "listsimple" , category , "Series - Todas"                   ,"http://www.cinegratis.net/index.php?module=serieslist","","")
	xbmctools.addnewfolder( CHANNELNAME , "listseries" , category , "Dibujos - Novedades"              ,"http://www.cinegratis.net/index.php?module=anime","","")
	xbmctools.addnewfolder( CHANNELNAME , "listsimple" , category , "Dibujos - Todos"                  ,"http://www.cinegratis.net/index.php?module=animelist","","")
	xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , "Documentales - Novedades"         ,"http://www.cinegratis.net/index.php?module=documentales","","")
	xbmctools.addnewfolder( CHANNELNAME , "listsimple" , category , "Documentales - Todos"             ,"http://www.cinegratis.net/index.php?module=documentaleslist","","")
	#xbmctools.addnewfolder( CHANNELNAME , "deportes"   , category , "Deportes"                         ,"","","")
	xbmctools.addnewfolder( CHANNELNAME , "search"     , category , "Buscar"                           ,"","","")

	# Cierra el directorio
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def pelisalfa(params, url, category):

	xbmctools.addnewfolder( CHANNELNAME ,"listsimple", category , "0-9","http://www.cinegratis.net/index.php?module=peliculaslist&init=","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listsimple", category , "A","http://www.cinegratis.net/index.php?module=peliculaslist&init=a","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listsimple", category , "B","http://www.cinegratis.net/index.php?module=peliculaslist&init=b","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listsimple", category , "C","http://www.cinegratis.net/index.php?module=peliculaslist&init=c","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listsimple", category , "D","http://www.cinegratis.net/index.php?module=peliculaslist&init=d","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listsimple", category , "E","http://www.cinegratis.net/index.php?module=peliculaslist&init=e","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listsimple", category , "F","http://www.cinegratis.net/index.php?module=peliculaslist&init=f","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listsimple", category , "G","http://www.cinegratis.net/index.php?module=peliculaslist&init=g","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listsimple", category , "H","http://www.cinegratis.net/index.php?module=peliculaslist&init=h","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listsimple", category , "I","http://www.cinegratis.net/index.php?module=peliculaslist&init=i","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listsimple", category , "J","http://www.cinegratis.net/index.php?module=peliculaslist&init=j","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listsimple", category , "K","http://www.cinegratis.net/index.php?module=peliculaslist&init=k","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listsimple", category , "L","http://www.cinegratis.net/index.php?module=peliculaslist&init=l","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listsimple", category , "M","http://www.cinegratis.net/index.php?module=peliculaslist&init=m","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listsimple", category , "N","http://www.cinegratis.net/index.php?module=peliculaslist&init=n","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listsimple", category , "O","http://www.cinegratis.net/index.php?module=peliculaslist&init=o","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listsimple", category , "P","http://www.cinegratis.net/index.php?module=peliculaslist&init=p","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listsimple", category , "Q","http://www.cinegratis.net/index.php?module=peliculaslist&init=q","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listsimple", category , "R","http://www.cinegratis.net/index.php?module=peliculaslist&init=r","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listsimple", category , "S","http://www.cinegratis.net/index.php?module=peliculaslist&init=s","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listsimple", category , "T","http://www.cinegratis.net/index.php?module=peliculaslist&init=t","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listsimple", category , "U","http://www.cinegratis.net/index.php?module=peliculaslist&init=u","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listsimple", category , "V","http://www.cinegratis.net/index.php?module=peliculaslist&init=v","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listsimple", category , "W","http://www.cinegratis.net/index.php?module=peliculaslist&init=w","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listsimple", category , "X","http://www.cinegratis.net/index.php?module=peliculaslist&init=x","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listsimple", category , "Y","http://www.cinegratis.net/index.php?module=peliculaslist&init=y","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listsimple", category , "Z","http://www.cinegratis.net/index.php?module=peliculaslist&init=z","","")

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def deportes(params, url, category):

	xbmctools.addnewfolder( CHANNELNAME ,"listsimple", category , "Fórmula 1","http://www.cinegratis.net/index.php?module=deporte&cat=Formula-1","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listsimple", category , "NBA","http://www.cinegratis.net/index.php?module=deporte&cat=NBA","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listsimple", category , "Moto GP","http://www.cinegratis.net/deporte.php?cat=MotoGP","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listsimple", category , "Fútbol","http://www.cinegratis.net/index.php?module=deporte&cat=Futbol","","")

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def search(params,url,category):
	
	buscador.listar_busquedas(params,url,category)

def searchresults(params,tecleado,category):
	logger.info("[cinegratis.py] search")

	buscador.salvar_busquedas(params,tecleado,category)
	tecleado = tecleado.replace(" ", "+")
	searchUrl = "http://www.cinegratis.net/index.php?module=search&title="+tecleado
	listsimple(params,searchUrl,category)

def performsearch(texto):
	logger.info("[cinegratis.py] performsearch")
	url = "http://www.cinegratis.net/index.php?module=search&title="+texto

	# Descarga la página
	data = scrapertools.cachePage(url)

	# Extrae las entradas (carpetas)
	patronvideos  = "<a href='(index.php\?module\=player[^']+)'[^>]*>(.*?)</a>"
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)
	
	resultados = []

	for match in matches:
		# Atributos
		scrapedtitle = match[1]
		scrapedtitle = scrapedtitle.replace("<span class='style4'>","")
		scrapedtitle = scrapedtitle.replace("</span>","")
		scrapedurl = urlparse.urljoin(url,match[0])
		scrapedthumbnail = ""
		scrapedplot = ""

		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		resultados.append( [CHANNELNAME , "detail" , "buscador" , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot ] )
		
	return resultados

def peliscat(params,url,category):
	logger.info("[cinegratis.py] peliscat")

	xbmctools.addnewfolder( CHANNELNAME , "listsimple" , category , "Versión original"     ,"http://www.cinegratis.net/index.php?module=search&title=subtitulado","","")
	xbmctools.addnewfolder( CHANNELNAME , "listsimple" , category , "Versión latina"       ,"http://www.cinegratis.net/index.php?module=search&title=latino","","")

	# Descarga la página
	data = scrapertools.cachePage(url)

	# Extrae las entradas (carpetas)
	patronvideos  = "<td align='left'><a href='([^']+)'><img src='([^']+)' border='0'></a></td>"
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	for match in matches:
		# Atributos
		patron2 = "genero/([A-Za-z\-]+)/"
		matches2 = re.compile(patron2,re.DOTALL).findall(match[0])
		scrapertools.printMatches(matches2)
		
		scrapedtitle = matches2[0]
		scrapedurl = urlparse.urljoin(url,match[0])
		scrapedthumbnail = urlparse.urljoin(url,match[1])
		scrapedplot = ""

		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def listsimple(params,url,category):
	logger.info("[cinegratis.py] listsimple")

	# Descarga la página
	data = scrapertools.cachePage(url)

	# Extrae las entradas (carpetas)
	patronvideos  = "<a href='(index.php\?module\=player[^']+)'[^>]*>(.*?)</a>"
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	for match in matches:
		# Atributos
		scrapedtitle = match[1]
		scrapedtitle = scrapedtitle.replace("<span class='style4'>","")
		scrapedtitle = scrapedtitle.replace("</span>","")
		scrapedurl = urlparse.urljoin(url,match[0])
		scrapedthumbnail = ""
		scrapedplot = ""

		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELNAME , "detail" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def listvideos(params,url,category):
	logger.info("[cinegratis.py] listvideos")

	if url=="":
		url = "http://www.cinegratis.net/index.php?module=peliculas"

	# Descarga la página
	data = scrapertools.cachePage(url)
	#logger.info(data)

	# Extrae las entradas (carpetas)
	patronvideos  = "<table.*?<td.*?>([^<]+)<span class='style1'>\(Visto.*?"
	patronvideos += "<div align='justify'>(.*?)</div>.*?"
	patronvideos += "<a href='(.*?)'.*?"
	patronvideos += "<img src='(.*?)'"
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	for match in matches:
		# Titulo
		scrapedtitle = match[0]
		# URL
		if url.startswith('http://www.cinegratis.net/genero'):
			url="http://www.cinegratis.net/"
		scrapedurl = urlparse.urljoin(url,match[2])
		# Thumbnail
		scrapedthumbnail = urlparse.urljoin(url,match[3])
		# Argumento
		scrapedplot = match[1]

		# Depuracion
		if (DEBUG):
			logger.info("scrapedtitle="+scrapedtitle)
			logger.info("scrapedurl="+scrapedurl)
			logger.info("scrapedthumbnail="+scrapedthumbnail)

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELNAME , "detail" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# Extrae la marca de siguiente página
	patronvideos  = "<a href='[^']+'><u>[^<]+</u></a> <a href='([^']+)'>"
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	if len(matches)>0:
		scrapedtitle = "Página siguiente"
		scrapedurl = urlparse.urljoin(url,matches[0])
		scrapedthumbnail = ""
		scrapedplot = ""
		xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def listseries(params,url,category):
	logger.info("[cinegratis.py] listvideos")

	if url=="":
		url = "http://www.cinegratis.net/index.php?module=peliculas"

	# Descarga la página
	data = scrapertools.cachePage(url)
	#logger.info(data)

	# Extrae las entradas (carpetas)
	patronvideos  = "<table width='785'[^>]+><tr><td[^>]+>([^<]+)<.*?"
	patronvideos += "<div align='justify'>(.*?)</div>.*?"
	patronvideos += "<a href='(.*?)'.*?"
	patronvideos += "<img src='(.*?)'"
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	for match in matches:
		# Titulo
		scrapedtitle = match[0]
		# URL
		scrapedurl = urlparse.urljoin(url,match[2])
		# Thumbnail
		scrapedthumbnail = urlparse.urljoin(url,match[3])
		# Argumento
		scrapedplot = match[1]

		# Depuracion
		if (DEBUG):
			logger.info("scrapedtitle="+scrapedtitle)
			logger.info("scrapedurl="+scrapedurl)
			logger.info("scrapedthumbnail="+scrapedthumbnail)

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELNAME , "detail" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# Extrae la marca de siguiente página
	patronvideos  = "<a href='[^']+'><u>[^<]+</u></a> <a href='([^']+)'>"
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	if len(matches)>0:
		scrapedtitle = "Página siguiente"
		scrapedurl = urlparse.urljoin(url,matches[0])
		scrapedthumbnail = ""
		scrapedplot = ""
		xbmctools.addnewfolder( CHANNELNAME , "listseries" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def detail(params,url,category):
	logger.info("[cinegratis.py] detail")

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
	logger.info("[cinegratis.py] play")

	title = unicode( xbmc.getInfoLabel( "ListItem.Title" ), "utf-8" )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = unicode( xbmc.getInfoLabel( "ListItem.Plot" ), "utf-8" )
	server = params["server"]
	
	xbmctools.playvideo(CHANNELNAME,server,url,category,title,thumbnail,plot)
