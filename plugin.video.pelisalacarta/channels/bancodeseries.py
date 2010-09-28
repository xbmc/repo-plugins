# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para bancodeseries
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
import vk

CHANNELNAME = "bancodeseries"

# Esto permite su ejecución en modo emulado
try:
	pluginhandle = int( sys.argv[ 1 ] )
except:
	pluginhandle = ""

# Traza el inicio del canal
logger.info("[bancodeseries.py] init")

DEBUG = True

def mainlist(params,url,category):
	logger.info("[bancodeseries.py] mainlist")

	# Añade al listado de XBMC
	xbmctools.addnewfolder( CHANNELNAME , "novedades" , category , "Novedades" ,"http://bancodeseries.com/","","")
	xbmctools.addnewfolder( CHANNELNAME , "novedades" , category , "Estrenos" ,"http://bancodeseries.com/taquilla/estrenos/","","")
	xbmctools.addnewfolder( CHANNELNAME , "ListaCat" , category , "Categorias" ,"http://bancodeseries.com/taquilla/estrenos/","","")
	xbmctools.addnewfolder( CHANNELNAME , "FullSeriesList" , category , "Listado Completo de Series" ,"http://bancodeseries.com/","","")

	if config.getSetting("singlechannel")=="true":
		xbmctools.addSingleChannelOptions(params,url,category)

	# Cierra el directorio
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

	
def novedades(params,url,category):
	logger.info("[bancodeseries.py] novedades")

	# ------------------------------------------------------
	# Descarga la página
	# ------------------------------------------------------
	data = scrapertools.cachePage(url)
	#logger.info(data)

	# ------------------------------------------------------
	# Extrae las películas
	# ------------------------------------------------------
	#patron  = '<div class="thumb">[^<]+<a href="([^"]+)"><img src="([^"]+)".*?alt="([^"]+)"/></a>'
	patron  = '<div class="galleryitem">[^<]+'
	patron += '<h1>[^<]+</h1>[^<]+'
	patron += '<a href="([^"]+)">[^<]+<img src="([^"]+)" '
	patron += 'alt="([^"]+)"'
	matches = re.compile(patron,re.DOTALL).findall(data)
	if DEBUG: scrapertools.printMatches(matches)

	for match in matches:
		scrapedtitle = match[2]
		scrapedurl = match[0]
		scrapedthumbnail = match[1].replace(" ","%20")
		scrapedplot = ""
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")
		try:
			print scrapedtitle
			scrapedtitle = scrapedtitle.replace("Ã±","ñ")
			#scrapedtitle = unicode(scrapedtitle, "utf-8" )
			
		except:
			pass
		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELNAME , "listcapitulos" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# ------------------------------------------------------
	# Extrae la página siguiente
	# ------------------------------------------------------
	#patron = '<a href="([^"]+)" >\&raquo\;</a>'
	patron  = 'class="current">[^<]+</span><a href="([^"]+)"'
	matches = re.compile(patron,re.DOTALL).findall(data)
	if DEBUG:
		scrapertools.printMatches(matches)

	for match in matches:
		scrapedtitle = "!Pagina siguiente"
		scrapedurl = match
		scrapedthumbnail = ""
		scrapeddescription = ""
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		xbmctools.addthumbnailfolder( CHANNELNAME , scrapedtitle , scrapedurl , scrapedthumbnail, "novedades" )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def FullSeriesList(params,url,category):
	logger.info("[bancodeseries.py] FullSeriesList")

	# Descarga la página
	data = scrapertools.cachePage(url)
	#logger.info(data)


	# Patron de las entradas
	patronvideos  = "<a href='([^']+)' class='[^']+' title='[^']+' style='[^']+'"          # URL
	patronvideos += ">([^<]+)</a>"                                                         # TITULO
	  
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	# Añade las entradas encontradas
	for match in matches:
		# Atributos
		scrapedtitle = match[1]
		scrapedurl = match[0]
		scrapedthumbnail = ""
		scrapedplot = ""
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELNAME , "novedades" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )


	# Asigna el título, desactiva la ordenación, y cierra el directorio
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )


def ListaCat(params,url,category):
	logger.info("[bancodeseries.py] ListaCat")
	
	
	xbmctools.addnewfolder( CHANNELNAME ,"novedades", category , "Acción"        ,"http://bancodeseries.com/taquilla/accion/","","")
	#xbmctools.addnewfolder( CHANNELNAME ,"novedades", category , "Animacion"       ,"http://bancodeseries.com/taquilla/animacion/","","")
	#xbmctools.addnewfolder( CHANNELNAME ,"novedades", category , "Anime"         ,"http://bancodeseries.com/taquilla/anime/","","")
	#xbmctools.addnewfolder( CHANNELNAME ,"novedades", category , "Aventura"      ,"http://bancodeseries.com/taquilla/aventura/","","")
	#xbmctools.addnewfolder( CHANNELNAME ,"novedades", category , "Bèlico Guerra ","http://bancodeseries.com/taquilla/guerra/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"novedades", category , "Ciencia-Ficción","http://bancodeseries.com/taquilla/ciencia-ficcion/","","")
	#xbmctools.addnewfolder( CHANNELNAME ,"novedadesMirror", category , "Clásicos","http://bancodeseries.com/taquilla/peliculasclasicos/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"novedades", category , "Comedia"        ,"http://bancodeseries.com/taquilla/comedia/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"novedades", category , "Dibujos"   ,"http://bancodeseries.com/taquilla/dibujos/","","")
	#xbmctools.addnewfolder( CHANNELNAME ,"novedadesMirror", category , "Destacado","http://bancodeseries.com/taquilla/peliculasdestacado/","","")
	#xbmctools.addnewfolder( CHANNELNAME ,"novedades", category , "Documentales Online","http://bancodeseries.com/taquilla/documentales-online-completos/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"novedades", category , "Drama"          ,"http://bancodeseries.com/taquilla/drama/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"novedades", category , "Entretenimiento","http://bancodeseries.com/taquilla/entretenimiento/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"novedades", category , "Estrenos"       ,"http://bancodeseries.com/taquilla/ultimos-extrenos/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"novedades", category , "Fantastico"        ,"http://bancodeseries.com/taquilla/fantastico/","","")
	#xbmctools.addnewfolder( CHANNELNAME ,"novedades", category , "Intriga"        ,"http://bancodeseries.com/taquilla/intriga/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"novedades", category , "Misterio"      ,"http://bancodeseries.com/taquilla/misterio/","","")
	#xbmctools.addnewfolder( CHANNELNAME ,"novedades", category , "Peliculas HD"  ,"http://bancodeseries.com/taquilla/peliculaspeliculas-hd-categorias/","","")
	#xbmctools.addnewfolder( CHANNELNAME ,"novedades", category , "Romance"        ,"http://bancodeseries.com/taquilla/peliculas-sobre-romance/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"novedades", category , "Suspenso"       ,"http://bancodeseries.com/taquilla/suspenso/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"novedades", category , "Terror"         ,"http://bancodeseries.com/taquilla/terror/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"novedades", category , "Thriller"       ,"http://bancodeseries.com/taquilla/thriller/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"FullSeriesList", category , "Todas las Series","http://bancodeseries.com/","","")
	
	
	
	# Asigna el título, desactiva la ordenación, y cierra el directorio
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )



def listcapitulos(params,url,category):
	logger.info("[bancodeseries.py] listcapitulos")

	thumbnail = urllib.unquote_plus( params.get("thumbnail") )

		
	# Descarga la página
	data = scrapertools.cachePage(url)
	#logger.info(data)
	
	patron = '<div class="sinopsis">.*?<p><p>(.*?)</p>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	if len(matches)>0:
		plot = matches[0]
	else:plot=""	
	# Patron de las entradas
	patron = 'post_id="([^"]+)'
	matchesid = re.compile(patron,re.DOTALL).findall(data)
	
	'''
	<div class="capitulo" id="Adelanto">
    <h2><a class="title-capitulo">Adelanto Capitulo 1</a></h2>
    <div class="content blank_content"></div>
	</div>
	'''
	patron = '<div class="capitulo" id="([^"]+)">[^<]+'
	patron += '<h2><a class="title-capitulo">([^<]+)</a></h2>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)
	

	# Añade las entradas encontradas
	for match in matches:
		# Atributos
		scrapedtitle = match[1]
		#http://bancodeseries.com/capitulo.php?action=load_capitulo&id=Capitulo-1&post_id=1078&_=1285004415408
		scrapedurl = "http://bancodeseries.com/capitulo.php?action=load_capitulo&id=%s&post_id=%s" %(match[0],matchesid[0])
		scrapedthumbnail = thumbnail
		scrapedplot = plot
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELNAME , "listmirrors" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# Asigna el título, desactiva la ordenación, y cierra el directorio
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )
        
	
	

def listmirrors(params,url,category):
	logger.info("[bancodeseries.py] listmirrors")

	title = urllib.unquote_plus( params.get("title") )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = unicode( xbmc.getInfoLabel( "ListItem.Plot" ), "utf-8" )

	# Descarga la página de detalle
	# http://bancodeseries.com/sorority-row/
	data = scrapertools.cachePage(url)
	logger.info(data)
	
	# Extrae el argumento
	'''
	patron = '<div class="sinopsis">.*?<li>(.*?)</li>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	if len(matches)>0:
		plot = matches[0]
	'''
	# Extrae los enlaces a los vídeos (Megavídeo)
	
	
	
	scrapedthumbnail = thumbnail
	scrapedplot = plot
	
	
	patron  = '<a href="([^"]+)".+?>([^<]+)</a>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)
	
	for match in matches:
		scrapedtitle = title
		
		
		if match[0].endswith(".html"):
			if "/vk/" in match[0]:  #http://bancodeseries.com/vk/11223192/674072850/ml3mp2pm9v00nmp2/predators-online.html
				patron = "http\:\/\/bancodeseries.com\/vk\/([^\/]+)\/([^\/]+)\/([^\/]+)\/[^\.]+\.html"
				matchesvk = re.compile(patron).findall(match[0])
				scrapedurl = "http://bancodeseries.com/modulos/embed/vkontakteX.php?oid=%s&id=%s&hash=%s" %(matchesvk[0][0],matchesvk[0][1],matchesvk[0][2])
				server = "Directo"
				xbmctools.addnewvideo( CHANNELNAME , "play" , category ,server, scrapedtitle+" - %s [VK]" %match[1] , scrapedurl , scrapedthumbnail, scrapedplot )
			  			
		
		
			patron   = "http://bancodeseries.com/([^/]+)/([^/]+)/[^/]+/([^\.]+).html"    #http://bancodeseries.com/playlist/6917/el-equipo-a-online.html
			matches2 = re.compile(patron,re.DOTALL).findall(match[0])
							
			if matches2[0][0] == "playlist":
				xmlurl = "http://bancodeseries.com/xml/%s.xml" %matches2[0][1]
				xmldata = scrapertools.cachePage(xmlurl)
				logger.info("xmldata="+xmldata)
				patronvideos  = '<track>[^<]+'
				patronvideos += '<creator>([^<]+)</creator>[^<]+'
				patronvideos += '<location>([^<]+)</location>.*?'
				patronvideos += '</track>'
				matchesxml = re.compile(patronvideos,re.DOTALL).findall(xmldata)
				scrapertools.printMatches(matchesxml)
				for xmlmatch in matchesxml:
					scrapedurl = xmlmatch[1]
					#xbmctools.addnewvideo( CHANNELNAME , "play" , category , server , (title.strip() + " (%d) " + videotitle) % j , url , thumbnail , plot )
					server = "Directo"
					xbmctools.addnewvideo( CHANNELNAME , "play" , category ,server, scrapedtitle+" - %s [Directo]" %xmlmatch[0] , scrapedurl , scrapedthumbnail, scrapedplot )
			elif matches2[0][0] == "flash":
				url = "http://bancodeseries.com/megaembed/%s/%s.html" %(matches2[0][1],matches2[0][2])
				data1 = scrapertools.cachePage(url)
				listavideos = servertools.findvideos(data1)

				for video in listavideos:
		
					videotitle = video[0]
					url = video[1]
					server = video[2]
					xbmctools.addnewvideo( CHANNELNAME , "play" , category , server , scrapedtitle + " - " + videotitle , url , thumbnail , plot )	
				
		elif "vk.php" in match[0]:
			scrapedurl = "http://bancodeseries.com/modulos/embed/vkontakteX.php?%s" %match[0].split("?")[1]
			server = "Directo"
			xbmctools.addnewvideo( CHANNELNAME , "play" , category ,server, scrapedtitle+" - %s [VK]" %match[1] , scrapedurl , scrapedthumbnail, scrapedplot )
	# Cierra el directorio
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def play(params,url,category):
	logger.info("[bancodeseries.py] play")
	try:
		title = unicode( xbmc.getInfoLabel( "ListItem.Title" ), "utf-8" )
	except:
		title = urllib.unquote_plus( params.get("title") )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = unicode( xbmc.getInfoLabel( "ListItem.Plot" ), "utf-8" )
	server = params.get("server")

	# Abre dialogo
	dialogWait = xbmcgui.DialogProgress()
	dialogWait.create( 'Accediendo al video...', title , plot )

	# Descarga la página del reproductor
	# http://bancodeseries.com/modulos/player.php?url=dmlkZW8uYWsuZmFjZWJvb2suY29tL2Nmcy1hay1hc2gyLzMzMjM2LzY4NS8xMDU1NTcxNDYxNjI3MjNfMzQ5ODk=
	# http://bancodeseries.com/modulos/embed/playerembed.php?url=dmlkZW8uYWsuZmFjZWJvb2suY29tL2Nmcy1hay1hc2gyLzMzMjM2LzY4NS8xMDU1NTcxNDYxNjI3MjNfMzQ5ODk=
	logger.info("[bancodeseries.py] url="+url)
	
	## --------------------------------------------------------------------------------------##
	#            Busca enlaces de videos para el servidor vkontakte.ru                        #
	## --------------------------------------------------------------------------------------##
	#"http://vkontakte.ru/video_ext.php?oid=89710542&id=147003951&hash=28845bd3be717e11&hd=1
	
	
	if "vkontakteX.php" in url:
		data = scrapertools.cachePage(url)
		server = "Directo"
		'''
		var video_host = 'http://cs12916.vkontakte.ru/';
		var video_uid = '87155741';
		var video_vtag = 'fc697084d3';
		var video_no_flv = 1;
		var video_max_hd = '1'
		'''
		patronvideos = '<iframe src="(http://vk[^/]+/video_ext.php[^"]+)"'
		matches = re.compile(patronvideos,re.DOTALL).findall(data)
		if len(matches)>0:
			print " encontro VKontakte.ru :%s" %matches[0]
			url = 	vk.geturl(matches[0])
			
			
 		'''
			data2 = scrapertools.cachePage(matches[0])
			print data2
			patron  = "var video_host = '([^']+)'.*?"
			patron += "var video_uid = '([^']+)'.*?"
			patron += "var video_vtag = '([^']+)'.*?"
			patron += "var video_no_flv = ([^;]+);.*?"
			patron += "var video_max_hd = '([^']+)'"
			matches2 = re.compile(patron,re.DOTALL).findall(data2)
			if len(matches2)>0:    #http://cs12385.vkontakte.ru/u88260894/video/d09802a95b.360.mp4
				for match in matches2:
					if match[3].strip() == "0":
						tipo = "flv"
						url = "%su%s/video/%s.%s" % (match[0],match[1],match[2],tipo)
					
					else:
						tipo = "360.mp4"
						url = "%su%s/video/%s.%s" % (match[0],match[1],match[2],tipo)
						
		'''
	
	# Cierra dialogo
	dialogWait.close()
	del dialogWait

	if len(url)>0:
		
		logger.info("url="+url)
		xbmctools.playvideo(CHANNELNAME,server,url,category,title,thumbnail,plot)
	else:
		xbmctools.alertnodisponible()
