# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para seriesyonkis
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
import library
import DecryptYonkis as Yonkis
import config
import logger
import buscador

CHANNELNAME = "seriesyonkis"
SERVER = {'pymeno2'   :'Megavideo' ,'pymeno3':'Megavideo','pymeno4':'Megavideo','pymeno5':'Megavideo','pymeno6':'Megavideo',
		  'svueno'    :'Stagevu'   ,
		  'movshare'   :'Movshare'  ,
		  'videoweed' :'Videoweed' ,
		  'veoh2'     :'Veoh'      ,
		  'megaupload':'Megaupload',
		  'pfflano'   :'Directo'   ,
		  }

#xbmc.executebuiltin("Container.SetViewMode(57)")  #57=DVD Thumbs
#xbmc.executebuiltin("Container.SetViewMode(50)")  #50=full list
#xbmc.executebuiltin("Container.SetViewMode(51)")  #51=list
#xbmc.executebuiltin("Container.SetViewMode(53)")  #53=icons
#xbmc.executebuiltin("Container.SetViewMode(54)")  #54=wide icons

# Esto permite su ejecución en modo emulado
try:
	pluginhandle = int( sys.argv[ 1 ] )
except:
	pluginhandle = ""

logger.info("[seriesyonkis.py] init")

DEBUG = True

def mainlist(params,url,category):
	logger.info("[seriesyonkis.py] mainlist")

	xbmctools.addnewfolder( CHANNELNAME , "lastepisodeslist" , category , "Últimos capítulos","http://www.seriesyonkis.com/ultimos-capitulos.php","","")
	xbmctools.addnewfolder( CHANNELNAME , "listalfabetico"   , category , "Listado alfabético","","","")
	xbmctools.addnewfolder( CHANNELNAME , "alltvserieslist"  , category , "Listado completo de series","http://www.seriesyonkis.com/","","")
	xbmctools.addnewfolder( CHANNELNAME , "allcartoonslist"  , category , "Listado completo de dibujos animados","http://www.seriesyonkis.com/","","")
	xbmctools.addnewfolder( CHANNELNAME , "allanimelist"     , category , "Listado completo de anime","http://www.seriesyonkis.com/","","")
	xbmctools.addnewfolder( CHANNELNAME , "allminilist"      , category , "Listado completo de miniseries","http://www.seriesyonkis.com/","","")
	xbmctools.addnewfolder( CHANNELNAME , "search"           , category , "Buscar","","","")

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
		
	# Disable sorting...
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def search(params,url,category):
	logger.info("[seriesyonkis.py] search")

	buscador.listar_busquedas(params,url,category)
	
def performsearch(texto):
	logger.info("[cine15.py] performsearch")
	url = "http://www.seriesyonkis.com/buscarSerie.php?s="+texto

	# Descarga la página
	data = scrapertools.cachePage(url)

	# Extrae las entradas (carpetas)
	patronvideos  = '<h2><li><a href="([^"]+)" title="([^"]+)"><img.*?src="([^"]+)".*?'
	patronvideos += '<span[^>]+>(.*?)</span>'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	resultados = []

	for match in matches:
		scrapedtitle = match[1]
		scrapedurl = match[0]
		scrapedthumbnail = match[2]
		scrapedplot = match[3]

		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		resultados.append( [CHANNELNAME , "list" , "buscador" , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot ] )
		
	return resultados

def searchresults(params,Url,category):
	logger.info("[seriesyonkis.py] searchresults")
	
	buscador.salvar_busquedas(params,Url,category)
	url = "http://www.seriesyonkis.com/buscarSerie.php?s="+Url.replace(" ", "+")

	# Descarga la página
	data = scrapertools.cachePage(url)
	#logger.info(data)

	# Extrae las entradas (carpetas)
	#<h2><li><a href="http://www.seriesyonkis.com/serie/house/" title="House"><img height="84" src="http://images.seriesyonkis.com/images/house.jpg" alt="House" align="right" /><div align="left"><strong>House</strong></div></a></h2><span style="font-size: 0.7em">Descripción: <h2 align="center"><u><strong><a href="http://www.seriesyonkis.com/serie/house/" title="House">Dr House</a></strong></u></h2>
	#<center><a href='http://tienda.seriesyonkis.com/house.htm'><img src='http://images.seriesyonkis.com/tienda/dr-house.gif' /></a></center>
	#Serie de TV (2004-Actualidad). 5 Nominaciones a los premios Emmy / Serie sobre un antipático médico especializado en enfermedades infecciosas. Gregory House es, seguramente, el mejor medico del Hospital, pero su carácter, rebeldía y su honestidad con los pacientes y su equipo le hacen único. Prefiere evitar el contacto directo con los pacientes, le interesa por encima de todo la investigación de las enfermedades. Además de no cumplir las normas, se niega a ponerse la bata de médico. Es adicto a los calmantes y a las series de hospitales, ¿contradictorio? No, es House. (FILMAFFINITY)<br /></span><br /><br /><br /><br /></li>
	#<h2><li><a href="http://www.seriesyonkis.com/serie/dollhouse/" title="Dollhouse"><img 
	
	patronvideos  = '<h2><li><a href="([^"]+)" title="([^"]+)"><img.*?src="([^"]+)".*?'
	patronvideos += '<span[^>]+>(.*?)</span>'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	for match in matches:
		scrapedtitle = match[1]
		scrapedurl = match[0]
		scrapedthumbnail = match[2]
		scrapedplot = match[3]
		
		Serie = scrapedtitle    # JUR-Añade nombre serie para librería

		# Depuracion
		if (DEBUG):
			logger.info("scrapedtitle="+scrapedtitle)
			logger.info("scrapedurl="+scrapedurl)
			logger.info("scrapedthumbnail="+scrapedthumbnail)
			logger.info("Serie="+Serie)

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELNAME , "list" , category , scrapedtitle , scrapedurl , scrapedthumbnail , scrapedplot , Serie)

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )

	# Disable sorting...
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def listalfabetico(params, url, category):
	xbmctools.addnewfolder(CHANNELNAME , "listseriesthumbnails" , category , "0-9","http://www.seriesyonkis.com/lista-series/listaSeriesNumeric.php","","")
	xbmctools.addnewfolder(CHANNELNAME , "listseriesthumbnails" , category , "A","http://www.seriesyonkis.com/lista-series/listaSeriesA.php","","")
	xbmctools.addnewfolder(CHANNELNAME , "listseriesthumbnails" , category , "B","http://www.seriesyonkis.com/lista-series/listaSeriesB.php","","")
	xbmctools.addnewfolder(CHANNELNAME , "listseriesthumbnails" , category , "C","http://www.seriesyonkis.com/lista-series/listaSeriesC.php","","")
	xbmctools.addnewfolder(CHANNELNAME , "listseriesthumbnails" , category , "D","http://www.seriesyonkis.com/lista-series/listaSeriesD.php","","")
	xbmctools.addnewfolder(CHANNELNAME , "listseriesthumbnails" , category , "E","http://www.seriesyonkis.com/lista-series/listaSeriesE.php","","")
	xbmctools.addnewfolder(CHANNELNAME , "listseriesthumbnails" , category , "F","http://www.seriesyonkis.com/lista-series/listaSeriesF.php","","")
	xbmctools.addnewfolder(CHANNELNAME , "listseriesthumbnails" , category , "G","http://www.seriesyonkis.com/lista-series/listaSeriesG.php","","")
	xbmctools.addnewfolder(CHANNELNAME , "listseriesthumbnails" , category , "H","http://www.seriesyonkis.com/lista-series/listaSeriesH.php","","")
	xbmctools.addnewfolder(CHANNELNAME , "listseriesthumbnails" , category , "I","http://www.seriesyonkis.com/lista-series/listaSeriesI.php","","")
	xbmctools.addnewfolder(CHANNELNAME , "listseriesthumbnails" , category , "J","http://www.seriesyonkis.com/lista-series/listaSeriesJ.php","","")
	xbmctools.addnewfolder(CHANNELNAME , "listseriesthumbnails" , category , "K","http://www.seriesyonkis.com/lista-series/listaSeriesK.php","","")
	xbmctools.addnewfolder(CHANNELNAME , "listseriesthumbnails" , category , "L","http://www.seriesyonkis.com/lista-series/listaSeriesL.php","","")
	xbmctools.addnewfolder(CHANNELNAME , "listseriesthumbnails" , category , "M","http://www.seriesyonkis.com/lista-series/listaSeriesM.php","","")
	xbmctools.addnewfolder(CHANNELNAME , "listseriesthumbnails" , category , "N","http://www.seriesyonkis.com/lista-series/listaSeriesN.php","","")
	xbmctools.addnewfolder(CHANNELNAME , "listseriesthumbnails" , category , "O","http://www.seriesyonkis.com/lista-series/listaSeriesO.php","","")
	xbmctools.addnewfolder(CHANNELNAME , "listseriesthumbnails" , category , "P","http://www.seriesyonkis.com/lista-series/listaSeriesP.php","","")
	xbmctools.addnewfolder(CHANNELNAME , "listseriesthumbnails" , category , "Q","http://www.seriesyonkis.com/lista-series/listaSeriesQ.php","","")
	xbmctools.addnewfolder(CHANNELNAME , "listseriesthumbnails" , category , "R","http://www.seriesyonkis.com/lista-series/listaSeriesR.php","","")
	xbmctools.addnewfolder(CHANNELNAME , "listseriesthumbnails" , category , "S","http://www.seriesyonkis.com/lista-series/listaSeriesS.php","","")
	xbmctools.addnewfolder(CHANNELNAME , "listseriesthumbnails" , category , "T","http://www.seriesyonkis.com/lista-series/listaSeriesT.php","","")
	xbmctools.addnewfolder(CHANNELNAME , "listseriesthumbnails" , category , "U","http://www.seriesyonkis.com/lista-series/listaSeriesU.php","","")
	xbmctools.addnewfolder(CHANNELNAME , "listseriesthumbnails" , category , "V","http://www.seriesyonkis.com/lista-series/listaSeriesV.php","","")
	xbmctools.addnewfolder(CHANNELNAME , "listseriesthumbnails" , category , "W","http://www.seriesyonkis.com/lista-series/listaSeriesW.php","","")
	xbmctools.addnewfolder(CHANNELNAME , "listseriesthumbnails" , category , "X","http://www.seriesyonkis.com/lista-series/listaSeriesX.php","","")
	xbmctools.addnewfolder(CHANNELNAME , "listseriesthumbnails" , category , "Y","http://www.seriesyonkis.com/lista-series/listaSeriesY.php","","")
	xbmctools.addnewfolder(CHANNELNAME , "listseriesthumbnails" , category , "Z","http://www.seriesyonkis.com/lista-series/listaSeriesZ.php","","")

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )

	# Disable sorting...
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def listseriesthumbnails(params,url,category):
	logger.info("[seriesyonkis.py] listseriesthumbnails")

	# Descarga la página
	data = scrapertools.cachePage(url)
	#logger.info(data)

	# Extrae las entradas (carpetas)
	#<td><center><a href='http://www.seriesyonkis.com/serie/a-camara-super-lenta/' title='A cámara súper lenta'><img src='http://images.seriesyonkis.com/images/a-camara-super-lenta.jpg' alt='A cámara súper lenta'/><br />A cámara súper lenta</a></center></td>
	if 'Numeric' in url:
		patronvideos  = "<td><center><a href='([^']+)' title='([^']+)'><img src='([^']+)'.*?</td>"
		t=1
		h=0
	else:
		patronvideos  = "<td><center><a title='([^']+)' href='([^']+)'><img src='([^']+)'.*?</td>"
		t=0
		h=1
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	for match in matches:
		# Titulo
		scrapedtitle = match[t]

		# URL
		scrapedurl = match[h]
		
		# Thumbnail
		scrapedthumbnail = match[2]
		
		# procesa el resto
		scrapedplot = ""
		Serie = scrapedtitle    # JUR-Añade nombre serie para librería

		# Depuracion
		if (DEBUG):
			logger.info("scrapedtitle="+scrapedtitle)
			logger.info("scrapedurl="+scrapedurl)
			logger.info("scrapedthumbnail="+scrapedthumbnail)
			logger.info("Serie="+Serie)

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELNAME , "list" , category , scrapedtitle , scrapedurl , scrapedthumbnail , scrapedplot, Serie )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )

	# Disable sorting...
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def lastepisodeslist(params,url,category):
	logger.info("[seriesyonkis.py] lastepisodeslist")

	# Descarga la página
	data = scrapertools.cachePage(url)
	#logger.info(data)

	# Extrae las entradas (carpetas)
	#<div class="ficha" style="background:url(http://images.seriesyonkis.com/images/house.jpg) #000000 center top no-repeat"><a href="http://www.seriesyonkis.com/capitulo/house/capitulo-01/44647/" title="(y 6x2) Broken">House - 6x01 - (y 6x2) Broken</a><br /><br /><img src="http://images.peliculasyonkis.com/images/tmegavideo.png" alt="Megavideo" style="vertical-align: middle;" /><img height="30" src="http://images.seriesyonkis.com/images/f/spanish.png" alt="Audio Español" title="Audio Español" style="vertical-align: middle;" /></div>
	#<div class="ficha" style="background:url(http://images.seriesyonkis.com/images/cinco-hermanos.jpg) #000000 center top no-repeat"><a href="http://www.seriesyonkis.com/capitulo/cinco-hermanos/capitulo-15/29162/" title="Capitulo 15">Cinco Hermanos - 3x15 - Capitulo 15</a><br /><br /><img src="http://images.peliculasyonkis.com/
	
	patronvideos  = '<div class="ficha" style="background:url\(([^\)]+)\)[^>]+><a.*?href="([^"]+)".*?>([^<]+)</a>(.*?)</div>'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	for match in matches:
		# Titulo
		esp=eng=latino=vos= ""
		if "Audio Espa\xc3\xb1ol" in match[3]:
			esp = "(Esp)"
		if "Subt\xc3\xadtulos en Espa\xc3\xb1ol" in match[3]:
			vos = "(V.O.S)"
		if "Audio Latino" in match[3]:
			latino = "(Latino)"
		if "Audio Ingl\xc3\xa9s" in match[2]:
			eng = "(Eng)"			
		scrapedtitle = "%s    %s%s%s%s" %(match[2],esp,vos,eng,latino)
		
		scrapedtitle2 = match[2]

		# URL
		scrapedurl = match[1]
		
		# Thumbnail
		scrapedthumbnail = match[0]
		
		# procesa el resto
		scrapedplot = ""

		#Serie - Trata de extraerla del título (no hay carpeta de serie aquí)
		#Esto son pruebas "muy preliminares" esto puede dar problemas con series añadidas completas
		try:
			Serie = scrapedtitle2[:scrapedtitle2.find("- ")-1]
		except:
			logger.info ("[seriesyonkis.py] ERROR extrayendo y limpiando nombre de serie de:"+scrapedtitle)
			Serie = ""

		# Depuracion
		if (DEBUG):
			logger.info("scrapedtitle="+scrapedtitle)
			logger.info("Serie="+Serie)
			logger.info("scrapedurl="+scrapedurl)
			logger.info("scrapedthumbnail="+scrapedthumbnail)
			logger.info("Serie="+Serie)

		# Añade al listado de XBMC
		xbmctools.addnewvideo( CHANNELNAME , "detail" , category , "Megavideo" , scrapedtitle , scrapedurl , scrapedthumbnail , scrapedplot ,Serie)

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )

	# Disable sorting...
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def alltvserieslist(params,url,category):
	allserieslist(params,url,category,"series")

def allcartoonslist(params,url,category):
	allserieslist(params,url,category,"dibujos")

def allanimelist(params,url,category):
	allserieslist(params,url,category,"anime")

def allminilist(params,url,category):
	allserieslist(params,url,category,"miniseries")

def allserieslist(params,url,category,clave):
	logger.info("[seriesyonkis.py] allserieslist")

	# Descarga la página
	data = scrapertools.cachePage(url)
	#logger.info(data)

	# Extrae el bloque de las series
	patronvideos = '<h4><a.*?id="'+clave+'".*?<ul>(.*?)</ul>'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	data = matches[0]

	# Extrae las entradas (carpetas)
	patronvideos  = '<li class="page_item"><a href="(http://www.seriesyonkis.com/serie[^"]+)"[^>]+>([^<]+)</a></li>'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	for match in matches:
		# Titulo
		scrapedtitle = match[1]

		# URL
		scrapedurl = match[0]
		
		# Thumbnail
		scrapedthumbnail = ""
		
		# procesa el resto
		scrapedplot = ""
		Serie = scrapedtitle    # JUR-Añade nombre serie para librería

		# Depuracion
		if (DEBUG):
			logger.info("scrapedtitle="+scrapedtitle)
			logger.info("scrapedurl="+scrapedurl)
			logger.info("scrapedthumbnail="+scrapedthumbnail)
			logger.info("Serie="+Serie)

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELNAME , "list" , category , scrapedtitle , scrapedurl , scrapedthumbnail , scrapedplot , Serie)

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )

	# Disable sorting...
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def list(params,url,category):
	logger.info("[seriesyonkis.py] list")

	# Descarga la página
	data = scrapertools.cachePage(url)
	#logger.info(data)

	if params.has_key("Serie"):
		Serie = params.get("Serie")
	else:
	  Serie = ""

	if params.has_key("thumbnail"):
		thumbnail = params.get("thumbnail")
	else:
	  thumbnail = ""

	# Busca la descripción
	patronvideos  = '<h3>Descripci.n.</h3>([^<]+)<'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)
	if len(matches)>0:
		scrapedplot = matches[0]
	else:
		scrapedplot = ""
	
	# Busca el thumbnail
	patronvideos = '<div class="post">.*?<img.*?src="(http\:\/\/images.seriesyonkis[^"]+)"'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)
	if len(matches)>0:
		scrapedthumbnail = matches[0]
	else:
		scrapedthumbnail = ""

	# Añade "Agregar todos a la librería"
	xbmctools.addnewvideo( CHANNELNAME , "addlist2Library" , category , "Megavideo", "AÑADIR TODOS LOS EPISODIOS A LA BIBLIOTECA" , url , scrapedthumbnail , scrapedplot , Serie)

	# Extrae las entradas (carpetas)
	patronvideos  = '<a href="(http://www.seriesyonkis.com/capitulo[^"]+)"[^>]+>([^<]+)</a>(.*?)</h5></li>'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	for match in matches:
		# Titulo
		esp=eng=latino=vos= ""
		if "Audio Espa\xc3\xb1ol" in match[2]:
			esp = "(Esp)"
		if "Subt\xc3\xadtulos en Espa\xc3\xb1ol" in match[2]:
			vos = "(V.O.S)"
		if "Audio Latino" in match[2]:
			latino = "(Latino)"
		if "Audio Ingl\xc3\xa9s" in match[2]:
			eng = "(Eng)"	
		scrapedtitle = "%s    %s%s%s%s" %(match[1],esp,vos,eng,latino)
		
		# URL
		scrapedurl = match[0]
		
		# Depuracion
		if (DEBUG):
			logger.info("scrapedtitle="+scrapedtitle)
			logger.info("scrapedurl="+scrapedurl)
			logger.info("scrapedthumbnail="+scrapedthumbnail)
			logger.info("Serie="+Serie)

		# Añade al listado de XBMC
		xbmctools.addnewvideo( CHANNELNAME , "detail" , category , "Megavideo" , scrapedtitle , scrapedurl , scrapedthumbnail , scrapedplot , Serie)

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )

	# Disable sorting...
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def detail(params,url,category):
	logger.info("[seriesyonkis.py] detail")

	title = urllib.unquote_plus( params.get("title") )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = unicode( xbmc.getInfoLabel( "ListItem.Plot" ), "utf-8" )
	Serie = urllib.unquote_plus( params.get("Serie") )
	# ------------------------------------------------------------------------------------
	# Busca los enlaces a los videos
	# ------------------------------------------------------------------------------------
	#server = "Megavideo"
	server,url = scrapvideoURL(url)
	if url == "":
		
		return
	logger.info("[seriesyonkis - detail] url="+url)
	
	xbmctools.playvideo(CHANNELNAME,server,url,category,title,thumbnail,plot,Serie=Serie)
	# ------------------------------------------------------------------------------------

def addlist2Library(params,url,category):
	logger.info("[seriesyonkis.py] addlist2Library")

	# Descarga la página
	data = scrapertools.cachePage(url)
	#logger.info(data)

	if params.has_key("Serie"):
		Serie = params.get("Serie")
	else:
	  Serie = ""

	if params.has_key("server"):
		server = params.get("server")
	else:
	  server = ""

	if params.has_key("thumbnail"):
		thumbnail = params.get("thumbnail")
	else:
	  thumbnail = ""

	# Extrae las entradas (carpetas)
	patronvideos  = '<a href="(http://www.seriesyonkis.com/capitulo[^"]+)"[^>]+>([^<]+)</a>'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	pDialog = xbmcgui.DialogProgress()
	ret = pDialog.create('pelisalacarta', 'Añadiendo episodios...')
	pDialog.update(0, 'Añadiendo episodio...')
	totalepisodes = len(matches)
	logger.info ("[seriesyonkis.py - addlist2Library] Total Episodios:"+str(totalepisodes))
	i = 0
	errores = 0
	nuevos = 0
	for match in matches:
		# Titulo
		scrapedtitle = match[1]
		i = i + 1
		pDialog.update(i*100/totalepisodes, 'Añadiendo episodio...',scrapedtitle)
		if (pDialog.iscanceled()):
			return

		# URL
		#  Tenemos 2 opciones. Scrapear todos los episodios en el momento de añadirlos 
		#  a la biblioteca o bien dejarlo para cuando se vea cada episodio. Esto segundo
		#  añade los episodios mucho más rápido, pero implica añadir una función
		#  strm_detail en cada módulo de canal. Por el bien del rendimiento elijo la
		#  segunda opción de momento (hacer la primera es simplemente descomentar un par de
		#  líneas.
		#  QUIZÁ SEA BUENO PARAMETRIZARLO (PONER OPCIÓN EN LA CONFIGURACIÓN DEL PLUGIN)
		#  PARA DEJAR QUE EL USUARIO DECIDA DONDE Y CUANDO QUIERE ESPERAR.
		url = match [0]
		# JUR-Las 3 líneas siguientes son para OPCIÓN 1
		#scrapedurl = scrapvideoURL(url)
		#if scrapedurl == "":
		#	errores = errores + 1
			
		# Thumbnail
		scrapedthumbnail = ""
		
		# procesa el resto
		scrapedplot = ""
		# Depuracion
		if (DEBUG):
			logger.info("scrapedtitle="+scrapedtitle)
#			logger.info("scrapedurl="+scrapedurl) #OPCION 1.
			logger.info("url="+url) #OPCION 2.
			logger.info("scrapedthumbnail="+scrapedthumbnail)
			logger.info("Serie="+Serie)
			logger.info("Episodio "+str(i)+" de "+str(totalepisodes)+"("+str(i*100/totalepisodes)+"%)")

		# Añade a la librería #Comentada la opción 2. Para cambiar invertir los comentarios
		#OPCION 1:
		#library.savelibrary(scrapedtitle,scrapedurl,scrapedthumbnail,server,scrapedplot,canal=CHANNELNAME,category="Series",Serie=Serie,verbose=False)
		#OPCION 2
		try:
			nuevos = nuevos + library.savelibrary(scrapedtitle,url,scrapedthumbnail,server,scrapedplot,canal=CHANNELNAME,category="Series",Serie=Serie,verbose=False,accion="strm_detail",pedirnombre=False)
		except IOError:
			logger.info("Error al grabar el archivo "+scrapedtitle)
			errores = errores + 1
		
#	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )
	pDialog.close()
	
	#Actualización de la biblioteca
	if errores > 0:
		logger.info ("[seriesyonkis.py - addlist2Library] No se pudo añadir "+str(errores)+" episodios") 
	library.update(totalepisodes,errores,nuevos)

	return nuevos
	

def strm_detail (params,url,category):
	logger.info("[seriesyonkis.py] strm_detail")

	title = urllib.unquote_plus( params.get("title") )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = unicode( xbmc.getInfoLabel( "ListItem.Plot" ), "utf-8" )
	#server = "Megavideo"
	# ------------------------------------------------------------------------------------
	# Busca los enlaces a los videos
	# ------------------------------------------------------------------------------------
	server,url = scrapvideoURL(url)
	if url == "":
		
		return
	logger.info("[seriesyonkis] strm_detail url="+url)
	
	xbmctools.playvideo("STRM_Channel",server,url,category,title,thumbnail,plot,1)
#<td><div align="center"><span style="font-size: 10px"><em><img src="http://simages.peliculasyonkis.com/images/tmegavideo.png" alt="Megavideo" style="vertical-align: middle;" /><img src='http://images.peliculasyonkis.com/images/tdescargar2.png' title='Tiene descarga directa' alt='Tiene descarga directa' style='vertical-align: middle;' /><a onmouseover="window.status=''; return true;" onmouseout="window.status=''; return true;" title="Seleccionar esta visualizacion" href="http://www.seriesyonkis.com/player/visor_pymeno4.php?d=1&embed=no&id=%CB%D8%DC%DD%C0%D3%E2%FC&al=%A6%B2%AC%B8%AC%A4%BD%A4" target="peli">SELECCIONAR ESTA</a> (flash desde megavideo)</em>		  </span></div></td>		  <td><div align="center"><img height="30" src="http://simages.seriesyonkis.com/images/f/spanish.png" alt="Audio Español" title="Audio Español" style="vertical-align: middle;" /></div></td>
#		  <td><div align="center"><span style="font-size: 10px">Español (Spanish)</span></div></td>		  <td><div align="center"><span style="font-size: 10px">no</span></div></td>		  <td><div align="center"><span style="font-size: 10px">Formato AVI 270mb</span></div></td>		  <td><div align="center"><span style="font-size: 10px">MasGlo<br />masglo</span></div></td>		</tr><tr>
 

def scrapvideoURL(urlSY):
	data = scrapertools.cachePage(urlSY)
	patronvideos  = 'href="http://www.seriesyonkis.com/player/visor_([^\.]+).php.*?id=([^"]+)".*?alt="([^"]+)".*?'
	patronvideos += '<td><div[^>]+><[^>]+>[^<]+</span></div></td>[^<]+<td><div[^>]+><[^>]+>[^<]+</span></div></td>[^<]+'
	patronvideos += '<td><div[^>]+><[^>]+>(.*?)</tr>'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)
	id=""
	
	if len(matches)==0:
		xbmctools.alertnodisponible()
		return "",""
	elif len(matches)==1:
		server = SERVER[matches[0][0]]
		#print matches[0][1]
		if matches[0][0] == "svueno":
			id = matches[0][1]
			logger.info("[seriesyonkis.py]  id="+id)
			dec = Yonkis.DecryptYonkis()
			id = dec.decryptALT(dec.charting(dec.unescape(id)))
			id = "http://stagevu.com/video/" + id
		elif matches[0][0] in ["pymeno2","pymeno3","pymeno4","pymeno5","pymeno6"]:
			cortar = matches[0][1].split("&")
			id = cortar[0]
			logger.info("[seriesyonkis.py]  id="+id)
			dec = Yonkis.DecryptYonkis()
			id = dec.decryptID_series(dec.unescape(id))
		else:pass
		print 'codigo :%s' %id
		return server,id		
	else:
		
		server,id = choiceOne(matches)
		if len(id)==0:return "",""
		print 'codigo :%s' %id
		return server,id
		
		
def choiceOne(matches):
	opciones = []
	IDlist = []
	servlist = []
	Nro = 0
	fmt=duracion=id=""
	
	for server,codigo,audio,data in matches:
		try:
			servidor = SERVER[server]
			Nro = Nro + 1
			regexp = re.compile(r"title='([^']+)'")
			match = regexp.search(data)
			if match is not None:
				fmt = match.group(1)
				fmt = fmt.replace("Calidad","").strip()
			regexp = re.compile(r"Duraci\xc3\xb3n:([^<]+)<")
			match = regexp.search(data)
			if match is not None:
				duracion = match.group(1).replace(".",":")		
			audio = audio.replace("Subt\xc3\xadtulos en Espa\xc3\xb1ol","Subtitulado") 
			audio = audio.replace("Audio","").strip()
			opciones.append("%02d) [%s] - (%s) - %s  [%s] " % (Nro , audio,fmt,duracion,servidor))
			IDlist.append(codigo)
			servlist.append(server)
		except:
			logger.info("[seriesyonkis.py] error (%s)" % server)
	dia = xbmcgui.Dialog()
	seleccion = dia.select("Nº)[AUDIO]-(CALIDAD)-DURACION", opciones)
	logger.info("seleccion=%d" % seleccion)
	if seleccion == -1 : return "",""
	if servlist[seleccion]  in ["pymeno2","pymeno3","pymeno4","pymeno5","pymeno6"]:
		cortar = IDlist[seleccion].split("&")
		id = cortar[0]
		logger.info("[seriesyonkis.py]  id="+id)
		dec = Yonkis.DecryptYonkis()
		id = dec.decryptID_series(dec.unescape(id))		
	elif servlist[seleccion] == "svueno":
		id = IDlist[seleccion]
		logger.info("[seriesyonkis.py]  id="+id)
		dec = Yonkis.DecryptYonkis()
		id = dec.decryptALT(dec.charting(dec.unescape(id)))
		id = "http://stagevu.com/video/" + id
	elif servlist[seleccion] == "movshare":
		id = IDlist[seleccion]
		logger.info("[seriesyonkis.py]  id="+id)
		dec = Yonkis.DecryptYonkis()
		id = dec.decryptALT(dec.charting(dec.unescape(id)))
	elif servlist[seleccion] == "videoweed":
		id = IDlist[seleccion]
		logger.info("[seriesyonkis.py]  id="+id)
		dec = Yonkis.DecryptYonkis()
		id = dec.decryptID(dec.charting(dec.unescape(id)))
		id = "http://www.videoweed.com/file/%s" %id				
	else:
		pass
	return SERVER[servlist[seleccion]],id
