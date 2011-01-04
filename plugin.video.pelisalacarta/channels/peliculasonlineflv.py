# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para Peliculasonlineflv.blogspot.com
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
import youtube
import config
import logger
import vk

CHANNELNAME = "peliculasonlineflv"

# Esto permite su ejecución en modo emulado
try:
	pluginhandle = int( sys.argv[ 1 ] )
except:
	pluginhandle = ""

# Traza el inicio del canal
logger.info("[peliculasonlineflv.py] init")

DEBUG = True

def mainlist(params,url,category):
	logger.info("[peliculasonlineflv.py] mainlist")

	# Añade al listado de XBMC
	xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , "Peliculas - Novedades"            ,"http://peliculasonlineflv.org/","","")
	xbmctools.addnewfolder( CHANNELNAME , "ListCat"    , category , "Peliculas - Generos" ,"http://peliculasonlineflv.org/","","")
	#xbmctools.addnewfolder( CHANNELNAME , "DocuSeries" , category , "Documentales - Series Disponibles" ,"http://peliculasonlineflv.wordpress.com/","","")
	xbmctools.addnewfolder( CHANNELNAME , "DocuTag"    , category , "Peliculas - Tag" ,"http://peliculasonlineflv.org/","","")
	xbmctools.addnewfolder( CHANNELNAME , "DocuARCHIVO", category , "Peliculas - Archivo" ,"http://peliculasonlineflv.org/","","")
	xbmctools.addnewfolder( CHANNELNAME , "search"     , category , "Buscar"                           ,"","","")

	if config.getSetting("singlechannel")=="true":
		xbmctools.addSingleChannelOptions(params,url,category)

	# Propiedades
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def search(params,url,category):
	logger.info("[peliculasonlineflv.py] search")

	keyboard = xbmc.Keyboard('')
	keyboard.doModal()
	if (keyboard.isConfirmed()):
		tecleado = keyboard.getText()
		if len(tecleado)>0:
			#convert to HTML
			tecleado = tecleado.replace(" ", "+")
			searchUrl = "http://peliculasonlineflv.org/index.php?s="+tecleado
			SearchResult(params,searchUrl,category)
			
def SearchResult(params,url,category):
	logger.info("[peliculasonlineflv.py] SearchResult")

	# Descarga la página
	data = scrapertools.cachePage(url)

	# Extrae las entradas (carpetas)
	patronvideos  = '<p class="entry-title"><[^>]+>[^<]+</span><a href="([^"]+)"[^>]+>([^<]+)</a></p>'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	for match in matches:
		# Atributos
		scrapedurl = match[0]
		
		scrapedtitle =match[1]
		scrapedtitle = scrapedtitle.replace("&#8211;","-")
		scrapedtitle = scrapedtitle.replace("&nbsp;"," ")
		scrapedthumbnail = ""
		scrapedplot = ""
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELNAME , "detail" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# Propiedades
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )
		

def performsearch(texto):
	logger.info("[peliculasonlineflv.py] performsearch")
	url = "http://peliculasonlineflv.wordpress.com/index.php?s="+texto

	# Descarga la página
	data = scrapertools.cachePage(url)

	# Extrae las entradas (carpetas)
	patronvideos  = '<p class="entry-title"><[^>]+>[^<]+</span><a href="([^"]+)"[^>]+>([^<]+)</a></p>'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	resultados = []

	for match in matches:
		scrapedtitle = match[1]
		scrapedtitle = scrapedtitle.replace("&#8211;","-")
		scrapedtitle = scrapedtitle.replace("&nbsp;"," ")
		scrapedurl = match[0]
		scrapedthumbnail = ""
		scrapedplot = ""

		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		resultados.append( [CHANNELNAME , "detail" , "buscador" , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot ] )
		
	return resultados
def DocuSeries(params,url,category):
	logger.info("[peliculasonlineflv.py] DocuSeries")

	# Descarga la página
	data = scrapertools.cachePage(url)

	# Extrae las entradas (carpetas)
	patronvideos  = '<a href="([^"]+)" target="_blank"><img src="([^"]+)"></a><br>'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	for match in matches:
		# Atributos
		scrapedurl = match[0]
		mobj = re.search(r"http://peliculasonlineflv.wordpress.com/tag/([^/]+)/", scrapedurl)
		scrapedtitle = mobj.group(1)
		scrapedtitle = scrapedtitle.replace("-"," ")
		
		scrapedthumbnail = match[1]
		scrapedplot = ""
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# Propiedades
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )


def DocuTag(params,url,category):
	logger.info("[peliculasonlineflv.py] DocuSeries")

	# Descarga la página
	data = scrapertools.cachePage(url)

	# Extrae las entradas (carpetas)
	patronvideos  =    "<a dir='ltr' href='([^']+)'>([^<]+)</a>"
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	for match in matches:
		# Atributos
		scrapedurl = match[0]
		scrapedtitle = match[1]
		scrapedthumbnail = ""
		scrapedplot = ""
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELNAME , "listvideosMirror" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# Propiedades
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def DocuARCHIVO(params,url,category):
	logger.info("[peliculasonlineflv.py] DocuSeries")

	# Descarga la página
	data = scrapertools.cachePage(url)

	# Extrae las entradas (carpetas)
	patronvideos  =   "<li class='archivedate'>[^<]+"
	patronvideos +=  "<a href='([^']+)'>([^<]+)</a>([^<]+)</li>"
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	for match in matches:
		# Atributos
		scrapedurl = match[0]
		scrapedtitle = match[1] + match[2]
		scrapedthumbnail = ""
		scrapedplot = ""
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELNAME , "listvideosMirror" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# Propiedades
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )


def ListCat(params,url,category):
	logger.info("[peliculasonlineflv.py] peliscat")

	# Descarga la página
	data = scrapertools.cachePage(url)
	patronvideos = '<li><a href="[^"]+" title="">Generos</a>(.*?)</ul>'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	# Extrae las entradas (carpetas)
	if len(matches)>0:
		patronvideos  = '<li><a href="([^"]+)" title="">([^<]+)</a>'
		matches = re.compile(patronvideos,re.DOTALL).findall(matches[0])
		scrapertools.printMatches(matches)

		for match in matches:
			# Atributos
			scrapedtitle = match[1]
			scrapedurl = match[0]
			scrapedthumbnail = ""
			scrapedplot = ""
			if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")
				# Añade al listado de XBMC
			xbmctools.addnewfolder( CHANNELNAME , "listvideosMirror" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# Propiedades
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def listvideos(params,url,category):
	logger.info("[peliculasonlineflv.py] listvideos")

	scrapedthumbnail = ""
	scrapedplot = ""
	# Descarga la página
	data = scrapertools.cachePage(url)
	#logger.info(data)

	# Extrae las entradas (carpetas)
	patronvideos  = "<h2 class='title'>Ultimas Peliculas Subidas</h2>(.*?)</div>"
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	if len(matches)>0:
		patronvideos  = '<a.+?href="([^"]+)".+?><img.+?'
		patronvideos += 'src="([^"]+)"'
		matches = re.compile(patronvideos,re.DOTALL).findall(matches[0])
	scrapertools.printMatches(matches)

	for match in matches:
		regexp = re.compile(r'http:\/\/[^\/]+\/[^\/]+\/[^\/]+\/([^\.]+)\.html')
		matchtitle = regexp.search(match[0])
		if matchtitle is not None:
			scrapedtitle = matchtitle.group(1).replace("-"," ")       
		else:
			scrapedtitle = match[0]
		scrapedtitle = scrapedtitle.replace("&#8211;","-")
		scrapedtitle = scrapedtitle.replace("&nbsp;"," ")
		scrapedtitle = scrapedtitle.replace("&amp;;","&")
		scrapedurl = match[0]
		scrapedthumbnail = match[1]
		scrapedplot = ""
		
		#scrapedplot = scrapedplot.replace("â€¦","")
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELNAME , "detail" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# Extrae la marca de siguiente página
	patronvideos = '<div class="left"><a href="([^"]+)" ><span>&laquo;</span> Entradas Anteriores</a></div>'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	if len(matches)>0:
		scrapedtitle = "Página siguiente"
		scrapedurl = urlparse.urljoin(url,matches[0])
		scrapedthumbnail = ""
		scrapedplot = ""
		xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# Propiedades
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def listvideosMirror(params,url,category):
	logger.info("[peliculasonlineflv.py] listvideosMirror")

	scrapedthumbnail = ""
	scrapedplot = ""
	# Descarga la página
	data = scrapertools.cachePage(url)
	#logger.info(data)

	# Extrae las entradas (carpetas)
	patronvideos  = "<h3 class='post-title entry-title'>[^<]+"
	patronvideos += "<a href='([^']+)'>([^<]+)</a>.*?"
	patronvideos += "<div id='[^']+'><img.+?alt=\"\".+?src=\"([^\"]+)\".*?"
	patronvideos += ">((?:SINOPSIS|Sinopsis).*?)</div>"
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	if len(matches)>0:
			scrapertools.printMatches(matches)
			for match in matches:
				scrapedtitle = match[1]
				scrapedtitle = scrapedtitle.replace("&#8211;","-")
				scrapedtitle = scrapedtitle.replace("&nbsp;"," ")
				scrapedtitle = scrapedtitle.replace("&amp;;","&")
				scrapedtitle = scrapedtitle.replace("&#161;","¡")
				scrapedtitle = scrapedtitle.replace("&#191;","¿")
				scrapedurl = match[0]
				scrapedthumbnail = match[2]
				scrapedplot = match[3]
				scrapedplot = re.sub("<[^>]+>"," ",scrapedplot)
				#scrapedplot = scrapedplot.replace("â€¦","")
				if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")
				# Añade al listado de XBMC
				xbmctools.addnewfolder( CHANNELNAME , "detail" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# Extrae la marca de siguiente página
	patronvideos = "<a class='blog-pager-older-link' href='([^']+)'"
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	if len(matches)>0:
		scrapedtitle = "Página siguiente"
		scrapedurl = urlparse.urljoin(url,matches[0])
		scrapedthumbnail = ""
		scrapedplot = ""
		xbmctools.addnewfolder( CHANNELNAME , "listvideosMirror" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# Propiedades
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def detail(params,url,category):
	logger.info("[peliculasonlineflv.py] detail")

	
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = urllib.unquote_plus( params.get("plot") )
	url1 = url
	# Descarga la página
	data = scrapertools.cachePage(url)
	#logger.info(data)
	patron = 'src="(http://peliculasonlineflvgratis.blogspot.com.+?)"'
	matches = re.compile(patron,re.DOTALL).findall(data)
	if len(matches)>0:
		data = scrapertools.cachePage(matches[0])
	try:
		title = re.compile("<title>(.+?)</title>").findall(data)[0]
	except:
		title = urllib.unquote_plus( params.get("title") )
	# ------------------------------------------------------------------------------------
	# Busca los enlaces a los videos
	# ------------------------------------------------------------------------------------
	listavideos = servertools.findvideos(data)
	
	for video in listavideos:
		videotitle = video[0]
		
		if "myspacecdn" or "facebook" in video[1]:
			continue
		
		url = video[1].replace("&amp;","&")
		server = video[2]
		xbmctools.addnewvideo( CHANNELNAME , "play" , category , server , title.strip() + " - " + videotitle , url , thumbnail , plot )
	# ------------------------------------------------------------------------------------
	## --------------------------------------------------------------------------------------##
	#               Busca enlaces a videos .flv o (.mp4 dentro de un xml)                     #
	## --------------------------------------------------------------------------------------##
	patronvideos = 'file=(http\:\/\/[^\&]+)\&'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	print patronvideos
	c = 0
	if len(matches)>0:
		print matches
		for match in matches:
			subtitle = "[FLV-Directo]"
			if ("xml" in matches[0]):
				data2 = scrapertools.cachePage(matches[0])
				logger.info("data2="+data2)
				patronvideos  = '<track>.*?'
				patronvideos += '<creator>([^<]+)</creator>[^<]+'
				patronvideos += '<location>([^<]+)</location>[^<]+'
				patronvideos += '</track>'
				matches2 = re.compile(patronvideos,re.DOTALL).findall(data2)
				scrapertools.printMatches(matches2)

				for match2 in matches2:
					if ".mp4" in match2[1]:
						subtitle = "[MP4-Directo]"
					scrapedtitle = '%s (%s) - %s' %(title,match2[0].strip(),subtitle)
					scrapedurl = match2[1].strip()
					scrapedthumbnail = thumbnail
					scrapedplot = plot
					if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

					# Añade al listado de XBMC
					xbmctools.addnewvideo( CHANNELNAME , "play" , category , "Directo" , scrapedtitle, scrapedurl , scrapedthumbnail, scrapedplot )
			else:
				
				c +=1	
				xbmctools.addnewvideo( CHANNELNAME , "play" , category , "Directo" , title + " - Parte %d/%d " %(c,len(matches))+subtitle, match , thumbnail , plot )
	
	
	patronvideos = 'src="(http://vk[^/]+/video_ext.php[^"]+)"'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	long = len(matches)
	
	
	if long>0:
		for match in matches:
			print " encontro VKontakte.ru :%s" %match[0]
			scrapedurl = 	vk.geturl(match.replace("&amp;","&"))
			scrapedtitle = title
			server = "Directo"
			
			
			xbmctools.addnewvideo( CHANNELNAME , "play" , category ,server, scrapedtitle+" - [VKServer]" , scrapedurl , thumbnail, plot )
			
	
	patronvideos = 'http://www.yaflix.com/.+?key=([^"]+)"'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	
	
	
	if len(matches)>0:
		
		for match in matches:
			link = "http://www.yaflix.com/nuevo/playlist.php?key=" + match
			data2 = scrapertools.cachePage(link)
			#print " encontro yaflix :%s" %match[0]
			patron = "<file>([^<]+)</file>"
			matcheslink = re.compile(patron,re.DOTALL).findall(data2)
			if len (matcheslink)>0:
				scrapedurl = 	matcheslink[0]
			else:scrapedurl = ""
			scrapedtitle = title
			server = "Directo"
			
			
			xbmctools.addnewvideo( CHANNELNAME , "play" , category ,server, scrapedtitle+" - [YAFLIX]" , scrapedurl , thumbnail, plot )
				
	
	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
		
	# Disable sorting...
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def play(params,url,category):
	logger.info("[peliculasonlineflv.py] play")

	title = unicode( xbmc.getInfoLabel( "ListItem.Title" ), "utf-8" )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = unicode( xbmc.getInfoLabel( "ListItem.Plot" ), "utf-8" )
	server = params["server"]

	xbmctools.playvideo(CHANNELNAME,server,url,category,title,thumbnail,plot)

def youtubeplay(params,url,category):
	logger.info("[peliculasonlineflv.py] youtubeplay")
	if "www.youtube" not in url:
		url  = 'http://www.youtube.com'+url


	title = urllib.unquote_plus( params.get("title") )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = "Ver Video"
	server = "Directo"
	id = youtube.Extract_id(url)
	videourl = youtube.geturl(id)

	if len(videourl)>0:
		logger.info("link directo de youtube : "+videourl)
		xbmctools.playvideo("Trailer",server,videourl,category,title,thumbnail,plot)

	return
