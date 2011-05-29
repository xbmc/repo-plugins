# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para peliculasid - actual. automat. ver.1.0
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------
import urlparse,urllib2,urllib,re
import os
import sys
import xbmc
import xbmcgui
import xbmcplugin

from xml.dom import minidom
from xml.dom import EMPTY_NAMESPACE

from core import scrapertools
from core import logger
from core.item import Item
from core import downloadtools
from core import xbmctools

from servers import servertools
from servers import xmltoplaylist

CHANNELNAME = "peliculasid"

# Traza el inicio del canal
logger.info("[peliculasid.py] init")

DEBUG = True

def mainlist(params,url,category):
	logger.info("[peliculasid.py] mainlist")

	# Añade al listado de XBMC
	xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , "Ultimas Películas Subidas"	,"http://www.peliculasid.net/","","")
	xbmctools.addnewfolder( CHANNELNAME , "listcategorias" , category , "Categorias"		,"http://www.peliculasid.net/","","")
	

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )

	# Disable sorting...
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def listcategorias(params,url,category):
	logger.info("[peliculas.py] listcategorias")
	
	xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , "2008"	,"http://peliculasid.net/2008-1.html","","")
	xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , "2009"	,"http://peliculasid.net/2009-1.html","","")
	xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , "2010"	,"http://peliculasid.net/2010-1.html","","")
	xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , "Acción"	,"http://www.peliculasid.net/accion-1.html","","")
	xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , "Animación"	,"http://www.peliculasid.net/animacion-1.html","","")
	xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , "Aventura"	,"http://www.peliculasid.net/aventura-1.html","","")
	xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , "Ciencia Ficción"	,"http://www.peliculasid.net/ciencia_ficcion-1.html","","")
	xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , "Cine Indio"	,"http://www.peliculasid.net/cine_indio-1.html","","")
	xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , "Comedia"	,"http://www.peliculasid.net/comedia-1.html","","")
	xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , "Crimen"	,"http://www.peliculasid.net/crimen-1.html","","")
	xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , "Documentales y mas"	,"http://www.peliculasid.net/documentales-1.html","","")
	xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , "Drama"	,"http://www.peliculasid.net/drama-1.html","","")
	xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , "Fantasia"	,"http://www.peliculasid.net/fantasia-1.html","","")
	xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , "Horror"	,"http://www.peliculasid.net/horror-1.html","","")
	xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , "Misterio"	,"http://www.peliculasid.net/misterio-1.html","","")
	xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , "Romance"	,"http://www.peliculasid.net/romance-1.html","","")
	xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , "Thriller"	,"http://www.peliculasid.net/thriller-1.html","","")

	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )
		

def listvideos(params,url,category):
	logger.info("[peliculasid.py] listvideos")

	if url=="":
		url = "http://www.peliculasid.net/"
				
	# Descarga la página
	data = scrapertools.cachePage(url)
	#logger.info(data)

	# Extrae las entradas (carpetas)
	patronvideos  = '<div class="item">[^<]+<h1>([^<]+)</h1>[^<]+'
	patronvideos += '<a href="([^"]+)"><img src="([^"]+)"'
	#patronvideos += '<div class="cover boxcaption">.*?<h6>([^<]+)</h6>'

	#patronvideos += "<img src='(.*?)'"
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	for match in matches:
		# Titulo
		scrapedtitle = match[0]
		scrapedtitle = scrapedtitle.replace('&#8217;',"'")
		# URL
		scrapedurl = match[1]
		# Thumbnail
		scrapedthumbnail = match[2]
		scrapedthumbnail = scrapedthumbnail.replace(" ","")
		# Argumento
		scrapedplot = ""

		# Depuracion
		if (DEBUG):
			logger.info("scrapedtitle="+scrapedtitle)
			logger.info("scrapedurl="+scrapedurl)
			logger.info("scrapedthumbnail="+scrapedthumbnail)

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELNAME , "detail" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# Extrae la marca de siguiente página
	
	patronvideos  = '<a href="([^"]+)" class="nextpostslink">'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	if len(matches)>0:
		scrapedtitle = "Página siguiente"
		scrapedurl = urlparse.urljoin(url,matches[0])
		scrapedthumbnail = ""
		scrapedplot = ""
		xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def detail(params,url,category):
	logger.info("[peliculasid.py] detail")

	title = urllib.unquote_plus( params.get("title") )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = urllib.unquote_plus( params.get("plot") )

	# Descarga la página
	data = scrapertools.cachePage(url)
	#logger.info(data)
	patrondescrip = '<strong>Sinopsis:</strong><br />(.*?)</p>'
	matches = re.compile(patrondescrip,re.DOTALL).findall(data)
	
	if len(matches)>0:
		descripcion = matches[0]
		descripcion = descripcion.replace("<br/>","")
		descripcion = descripcion.replace("\r","")
		descripcion = descripcion.replace("\n"," ")
		descripcion = descripcion.replace("\t"," ")
		descripcion = re.sub("<[^>]+>"," ",descripcion)
		#logger.info("descripcion="+descripcion)
		descripcion = acentos(descripcion)
		#logger.info("descripcion="+descripcion)
		try :
			plot = unicode( descripcion, "utf-8" ).encode("iso-8859-1")
		except:
			plot = descripcion
		plot = scrapertools.unescape(plot.strip())
		#--- Busca los videos Directos
		patronvideos = 'flashvars" value="file=([^\&]+)\&amp'
		matches = re.compile(patronvideos,re.DOTALL).findall(data)
		
		if len(matches)>0:
			
			if ("xml" in matches[0]):  
				xbmctools.addnewvideo( CHANNELNAME , "play" , category , "xml" , "Reproducir todas las partes a la vez" , matches[0] , thumbnail , plot )
				#data = scrapertools.cachePage(matches[0])
				req = urllib2.Request(matches[0])
				try:
					response = urllib2.urlopen(req)
				except:
					xbmctools.alertnodisponible()
					return
				data=response.read()
				response.close()
				
					
			#logger.info("archivo xml :"+data)
				newpatron = '<title>([^<]+)</title>[^<]+<location>([^<]+)</location>'
				newmatches = re.compile(newpatron,re.DOTALL).findall(data)
				if len(newmatches)>0:
					for match in newmatches:
						logger.info(" videos = "+match[1])
						if match[1].startswith("vid"):
							subtitle = match[0] + " (rtmpe) no funciona en xbmc"
						else:
							subtitle = match[0]
				
						xbmctools.addnewvideo( CHANNELNAME , "play" , category , "Directo" , title + " - "+subtitle, match[1] , thumbnail , plot )
				 
			else:
				logger.info(" matches = "+matches[0])
				xbmctools.addnewvideo( CHANNELNAME , "play" , category , "Directo" , title, matches[0] , thumbnail , plot )


	# Ahora usa servertools
	listavideos = servertools.findvideos(data)

	j=1
	for video in listavideos:
		videotitle = video[0]
		url = video[1]
		server = video[2]
		xbmctools.addnewvideo( CHANNELNAME , "play" , category , server , (title.strip() + " (%d) " + videotitle) % j , url , thumbnail , plot )
		j=j+1
	patronvideos = '<a href="(http://peliculasid.net/modulos/iframeplayer.php[^"]+)" target="[^"]+">([^<]+)</a>'
	#patronvideos2 = 'file=([^\&]+)\&'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	if len(matches)>0:
		urllists = ""
		for match in matches:
			if urllists == "":
				urllists = match[0]
			else:	
				urllists = urllists + "|" + match[0] 
			#data2 = scrapertools.cachePage(match[0])
			#matches2 = re.compile(patronvideos2,re.DOTALL).findall(data2)
			xbmctools.addnewvideo( CHANNELNAME , "play" , category , "Directo" , title+" - "+match[1], match[0] , thumbnail , plot )
		xbmctools.addnewvideo( CHANNELNAME , "play" , category , "Directo" , "(Reproducir todas las partes a la vez...)", urllists , thumbnail , plot )
	## --------------------------------------------------------------------------------------##
	#			Busca enlaces de videos para el servidor vkontakte.ru						#
	## --------------------------------------------------------------------------------------##
	#"http://vkontakte.ru/video_ext.php?oid=89710542&id=147003951&hash=28845bd3be717e11&hd=1
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
		 
		data2 = scrapertools.cachePage(matches[0])
		print data2
		patron  = "var video_host = '([^']+)'.*?"
		patron += "var video_uid = '([^']+)'.*?"
		patron += "var video_vtag = '([^']+)'.*?"
		patron += "var video_no_flv = ([^;]+);.*?"
		patron += "var video_max_hd = '([^']+)'"
		matches2 = re.compile(patron,re.DOTALL).findall(data2)
		if len(matches2)>0:	#http://cs12385.vkontakte.ru/u88260894/video/d09802a95b.360.mp4
			for match in matches2:
				if match[3].strip() == "0":
					tipo = "flv"
					videourl = "%s/u%s/video/%s.%s" % (match[0],match[1],match[2],tipo)
					xbmctools.addnewvideo( CHANNELNAME , "play" , category , "Directo" , title + " - "+"[VKONTAKTE] [%s]" %tipo, videourl , thumbnail , plot )
				else:
					tipo = "360.mp4"
					videourl = "%s/u%s/video/%s.%s" % (match[0],match[1],match[2],tipo)
					xbmctools.addnewvideo( CHANNELNAME , "play" , category , "Directo" , title + " - "+"[VKONTAKTE] [%s]" %tipo, videourl , thumbnail , plot )
					tipo = "240.mp4"
					videourl = "%s/u%s/video/%s.%s" % (match[0],match[1],match[2],tipo)
					xbmctools.addnewvideo( CHANNELNAME , "play" , category , "Directo" , title + " - "+"[VKONTAKTE] [%s]" %tipo, videourl , thumbnail , plot )
	
	patronvideos = '"(http://peliculasid.net/modulos/iframevk.php[^"]+)"'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	if len(matches)>0:
		print " encontro VKontakte.ru :%s" %matches[0]	
		xbmctools.addnewvideo( CHANNELNAME , "play" , category , "Directo" , title+" - [VKserver]", matches[0] , thumbnail , plot )
		
	patronvideos = '"(http://peliculasid.net/modulos/iframemv.php[^"]+)"'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	if len(matches)>0:
		print " encontro Megavideo :%s" %matches[0]	
		xbmctools.addnewvideo( CHANNELNAME , "play" , category , "Megavideo" , title+" - [Megavideo]", matches[0] , thumbnail , plot )
	
	patronvideos = '"(http://peliculasid.net/modulos/iframebb.php[^"]+)"'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	if len(matches)>0:
		print " encontro Videobb :%s" %matches[0]
		xbmctools.addnewvideo( CHANNELNAME , "play" , category , "videobb" , title+" - [Videobb]", matches[0] , thumbnail , plot )
				
	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )
	
def play(params,url,category):
	logger.info("[peliculasid.py] play")
	
	
	title = unicode( xbmc.getInfoLabel( "ListItem.Title" ), "utf-8" )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	try:
		plot = unicode( xbmc.getInfoLabel( "ListItem.Plot" ), "utf-8" )
	except:
		plot = xbmc.getInfoLabel( "ListItem.Plot" )
	server = params["server"]
	if "|" in url:
		matches = url.split("|")
		patronvideos = 'file=([^\&]+)\&'
		c = 0
		listdata = []
		for match in matches:
			c += 1
			print match
			data = scrapertools.cachePage(match)
			matches2 = re.compile(patronvideos,re.DOTALL).findall(data)
			listdata.append(["Parte %d" %c,matches2[0]])
		
		url = xmltoplaylist.MakePlaylistFromList(listdata)	
	elif "iframeplayer.php" in url:	  #"http://peliculasid.net/iframeplayer.php?url=aHR0cDovL3ZpZGVvLmFrLmZhY2Vib29rLmNvbS9jZnMtYWstc25jNC80MjIxNi82MS8xMjgxMTI4ODgxOTUwXzM5NTAwLm1wNA=="
		data = scrapertools.cachePage(url)
		patronvideos = 'file=([^\&]+)\&'
		matches = re.compile(patronvideos,re.DOTALL).findall(data)
		if len(matches)>0:
			url = matches[0]
			
	elif "iframevk.php" in url:
		data = scrapertools.cachePage(url)
		patronvideos = '<iframe src="(http://vk[^/]+/video_ext.php[^"]+)"'
		matches = re.compile(patronvideos,re.DOTALL).findall(data)
		if len(matches)>0:
			from servers import vk
			server = "Directo"
			url =	 vk.geturl(matches[0])
	elif "iframemv.php" in url:
		data = scrapertools.cachePage(url)
		patronvideos  = 'src="http://www.megavideo.com/mv_player.swf\?v\=([^"]+)"'
		matches = re.compile(patronvideos,re.DOTALL).findall(data)	
		if len(matches)>0:
			server = "Megavideo"
			url = matches[0]
	elif "iframebb.php" in url:
		data = scrapertools.cachePage(url)
		patronvideos  = 'src="http://www.videobb.com/e/([^"]+)"'
		matches = re.compile(patronvideos,re.DOTALL).findall(data)	
		if len(matches)>0:
			server = "videobb"
			url = "http://www.videobb.com/video/" + matches[0]

	xbmctools.playvideo(CHANNELNAME,server,url,category,title,thumbnail,plot)

def acentos(title):

		title = title.replace("Ã‚Â", "")
		title = title.replace("ÃƒÂ©","é")
		title = title.replace("ÃƒÂ¡","á")
		title = title.replace("ÃƒÂ³","ó")
		title = title.replace("ÃƒÂº","ú")
		title = title.replace("ÃƒÂ­","í")
		title = title.replace("ÃƒÂ±","ñ")
		title = title.replace("Ã¢â‚¬Â", "")
		title = title.replace("Ã¢â‚¬Å“Ã‚Â", "")
		title = title.replace("Ã¢â‚¬Å“","")
		title = title.replace("Ã©","é")
		title = title.replace("Ã¡","á")
		title = title.replace("Ã³","ó")
		title = title.replace("Ãº","ú")
		title = title.replace("Ã­","í")
		title = title.replace("Ã±","ñ")
		title = title.replace("Ãƒâ€œ","Ó")
		return(title)

def MakePlaylistFromXML(xmlurl,title="default"):
	logger.info("[%s.py] MakePlaylistFromXML" %CHANNELNAME)
	
	if title== ("default" or ""):
		nombrefichero = FULL_FILENAME_PATH_XML
	else:
		nombrefichero = os.path.join( downloadtools.getDownloadPath(),title + ".pls")
	xmldata = scrapertools.cachePage(xmlurl)
	patron = '<title>([^<]+)</title>.*?<location>([^<]+)</location>'
	matches = re.compile(patron,re.DOTALL).findall(xmldata)
	if len(matches)>0:
		playlistFile = open(nombrefichero,"w")
		playlistFile.write("[playlist]\n")
		playlistFile.write("\n")
		c = 0		
		for match in matches:
			c += 1
			playlistFile.write("File%d=%s\n"  %(c,match[1]))
			playlistFile.write("Title%d=%s\n" %(c,match[0]))
			playlistFile.write("\n")
			
		playlistFile.write("NumberOfEntries=%d\n" %c)
		playlistFile.write("Version=2\n")
		playlistFile.flush();
		playlistFile.close()	
		return nombrefichero,c
	else:
		return ""

def MakePlaylistFromList(Listdata,title="default"):
	logger.info("[%s.py] MakePlaylistFromList" %CHANNELNAME)
	
	if title== ("default" or ""):
		nombrefichero = FULL_FILENAME_PATH
	else:
		nombrefichero = os.path.join( downloadtools.getDownloadPath(),title + ".pls")

	if len(Listdata)>0:
		playlistFile = open(nombrefichero,"w")
		playlistFile.write("[playlist]\n")
		playlistFile.write("\n")
		c = 0		
		for match in Listdata:
			c += 1
			playlistFile.write("File%d=%s\n"  %(c,match[1]))
			playlistFile.write("Title%d=%s\n" %(c,match[0]))
			playlistFile.write("\n")
			
		playlistFile.write("NumberOfEntries=%d\n" %c)
		playlistFile.write("Version=2\n")
		playlistFile.flush();
		playlistFile.close()	
		return nombrefichero,c
	else:
		return ""
