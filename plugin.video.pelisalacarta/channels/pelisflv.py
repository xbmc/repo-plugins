# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para pelisflv.net by Bandavi
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

CHANNELNAME = "pelisflv"

# Esto permite su ejecución en modo emulado
try:
	pluginhandle = int( sys.argv[ 1 ] )
except:
	pluginhandle = ""

# Traza el inicio del canal
logger.info("[pelisflv.py] init")

DEBUG = True

def mainlist(params,url,category):
	logger.info("[pelisflv.py] mainlist")

	# Añade al listado de XBMC
	xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , "Novedades"    ,"http://www.pelisflv.net","","")
	xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , "Estrenos","http://www.pelisflv.net/search/label/Estrenos","","")
	xbmctools.addnewfolder( CHANNELNAME , "ListadoSeries" , category , "Series"        ,"http://www.pelisflv.net/","","")
	xbmctools.addnewfolder( CHANNELNAME , "ListadoSeries" , category , "Series Animadas"        ,"http://www.pelisflv.net/","","")
	xbmctools.addnewfolder( CHANNELNAME , "ListadoSeries" , category , "Anime"        ,"http://www.pelisflv.net/","","")
	xbmctools.addnewfolder( CHANNELNAME , "ListadoSeries" , category , "Categorias"        ,"http://www.pelisflv.net/","","")
	xbmctools.addnewfolder( CHANNELNAME , "ListadoSeries" , category , "Calidad"        ,"http://www.pelisflv.net/","","")
	xbmctools.addnewfolder( CHANNELNAME , "ListadoSeries" , category , "Audio"        ,"http://www.pelisflv.net/","","")
	xbmctools.addnewfolder( CHANNELNAME , "search" , category , "Buscar","http://www.pelisflv.net/","","")
	
	

	if config.getSetting("singlechannel")=="true":
		xbmctools.addSingleChannelOptions(params,url,category)

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )

	# Disable sorting...
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def search(params,url,category):
	logger.info("[pelisflv.py] search")

	keyboard = xbmc.Keyboard()
	#keyboard.setDefault('')
	keyboard.doModal()
	if (keyboard.isConfirmed()):
		tecleado = keyboard.getText()
		if len(tecleado)>0:
			#convert to HTML
			tecleado = tecleado.replace(" ", "+")
			searchUrl = "http://www.pelisflv.net/search?q="+tecleado
			listvideos(params,searchUrl,category)

def searchresults(params,url,category):
	logger.info("[pelisflv.py] SearchResult")
	
	
	# Descarga la página
	data = scrapertools.cachePage(url)
	#print data
	# Extrae las entradas (carpetas)
	patronvideos  = '<div class="poster">[^<]+<a href="([^"]+)"'                          # URL
	patronvideos += '><img src="([^"]+)" width=[^\/]+\/>'                                 # TUMBNAIL
	patronvideos += '</a>[^<]+<[^>]+>[^<]+<[^>]+>[^<]+<a href="[^"]+">([^<]+)</a>'        # TITULO 
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	for match in matches:
		# Atributos
		scrapedurl = match[0]
		
		scrapedtitle =match[2]
		scrapedtitle = scrapedtitle.replace("&#8211;","-")
		scrapedtitle = scrapedtitle.replace("&nbsp;"," ")
		scrapedthumbnail = match[1]
		scrapedplot = ""
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELNAME , "detail" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# Propiedades
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )
			


def ListadoSeries(params,url,category):
	logger.info("[peliculas24h.py] ListadoTotal")
	title = urllib.unquote_plus( params.get("title") )
	# Descarga la página
	data = scrapertools.cachePage(url)
	#logger.info(data)

	# Patron de las entradas
	patron = "<h2>"+title+"</h2>[^<]+<[^>]+>[^<]+<ul>(.*?)</ul>"
	matches = re.compile(patron,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)
	
	patron = "<a dir='ltr' href='([^']+)'>(.*?)</a>"
	matches = re.compile(patron,re.DOTALL).findall(matches[0])
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
		xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# Asigna el título, desactiva la ordenación, y cierra el directorio
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )
        

def listvideos(params,url,category):
	logger.info("[pelisflv.py] listvideos")

	if url=="":
		url = "http://www.pelisflv.net/"
                
	# Descarga la página
	data = scrapertools.cachePage(url)
	#logger.info(data)


	# Extrae las entradas (carpetas)
	patronvideos  = "<h3 class='post-title entry-title'>[^<]+<a href='([^']+)'"  # URL
	patronvideos += ">([^<]+)</a>.*?"                                            # Titulo   
	patronvideos += '<img style="[^"]+" src="([^"]+).*?'           # TUMBNAIL               
	patronvideos += 'border=[^>]+>.*?<span[^>]+>(.*?)</span></div>'        # Argumento	
	#patronvideos += '</h1>[^<]+</div>.*?<div class=[^>]+>[^<]+'
	#patronvideos += '</div>[^<]+<div class=[^>]+>.*?href="[^"]+"><img '                    
	#patronvideos += 'style=.*?src="([^"]+)".*?alt=.*?bold.*?>(.*?)</div>'                  # IMAGEN , DESCRIPCION
	#patronvideos += '.*?flashvars="file=(.*?flv)\&amp'                                      # VIDEO FLV 
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)
	scrapedtitle = ""
	for match in matches:
		# Titulo
		
		scrapedtitle = match[1]
		# URL
		scrapedurl = match[0]
		# Thumbnail
		scrapedthumbnail = match[2]
         
		# Argumento
		scrapedplot = match[3]
		scrapedplot = re.sub("<[^>]+>"," ",scrapedplot)
		scrapedplot = scrapedplot.replace('&#8220;','"')
		scrapedplot = scrapedplot.replace('&#8221;','"')
		scrapedplot = scrapedplot.replace('&#8230;','...')
		scrapedplot = scrapedplot.replace("&nbsp;","")

		# Depuracion
		if (DEBUG):
			logger.info("scrapedtitle="+scrapedtitle)
			logger.info("scrapedurl="+scrapedurl)
			logger.info("scrapedthumbnail="+scrapedthumbnail)

		
			# Añade al listado de XBMC
			xbmctools.addnewfolder( CHANNELNAME , "detail" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# Extrae la marca de siguiente página
	patronvideos  = "<a class='blog-pager-older-link' href='([^']+)'"
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	if len(matches)>0:
		scrapedtitle = "Página siguiente"
		scrapedurl = matches[0]
		scrapedthumbnail = ""
		scrapedplot = ""
		xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )

	# Disable sorting...
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def detail(params,url,category):
	logger.info("[pelisflv.py] detail")

	title = urllib.unquote_plus( params.get("title") )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = urllib.unquote_plus( params.get("plot") )

	# Descarga la página
	datafull = scrapertools.cachePage(url)
	#logger.info(data)
	patron = "google_ad_section_start(.*?)google_ad_section_end -->"
	matches = re.compile(patron,re.DOTALL).findall(datafull)
	data = matches[0]
                   
          
	# ------------------------------------------------------------------------------------
	# Busca los enlaces a los videos
	# ------------------------------------------------------------------------------------
	'''
	listavideos = servertools.findvideos(data)

	for video in listavideos:
		videotitle = video[0]
		url = video[1]
		server = video[2]
		xbmctools.addnewvideo( CHANNELNAME , "play" , category , server , title.strip() + " - " + videotitle , url , thumbnail , plot )
	'''
	# Busca enlaces en el servidor Stagevu - "el modulo servertools.findvideos() no los encuentra"
	
	patronvideos  = "'(http://stagevu.com[^']+)'"
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	if len(matches)>0:
		logger.info(" Servidor Stagevu")
		for match in matches:
			scrapedurl = match.replace("&amp;","&")
			xbmctools.addnewvideo( CHANNELNAME ,"play"  , category , "Stagevu" , title+" - [Stagevu]", scrapedurl , thumbnail , plot )

	# Busca enlaces en el servidor Movshare - "el modulo servertools.findvideos() no los encuentra"
	
	patronvideos  = "'(http://www.movshare.net[^']+)'"
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	if len(matches)>0:
		logger.info(" Servidor Movshare")
		for match in matches:
			scrapedurl = match.replace("&amp;","&")
			xbmctools.addnewvideo( CHANNELNAME ,"play"  , category , "Movshare" , title+" - [Movshare]", scrapedurl , thumbnail , plot )


		
	# ------------------------------------------------------------------------------------
        #--- Busca los videos Directos
        
	patronvideos = 'file=(http\:\/\/[^\&]+)\&'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)
	print "link directos encontrados :%s" %matches
	print data
	if len(matches)>0:
		for match in matches:
			subtitle = "[FLV-Directo]"
			if ("xml" in match):
				data2 = scrapertools.cachePage(match)
				logger.info("data2="+data2)
				patronvideos  = '<track>.*?'
				patronvideos += '<title>([^<]+)</title>[^<]+'
				patronvideos += '<location>([^<]+)</location>(?:[^<]+'
				patronvideos += '<meta rel="type">video</meta>[^<]+|[^<]+)'
				patronvideos += '<meta rel="captions">([^<]+)</meta>[^<]+'
				patronvideos += '</track>'
				matches2 = re.compile(patronvideos,re.DOTALL).findall(data2)
				scrapertools.printMatches(matches)
				
				for match2 in matches2:
					sub = ""
					playWithSubt = "play"
					if match2[2].endswith(".xml"): # Subtitulos con formato xml son incompatibles con XBMC
						sub = "[Subtitulo incompatible con xbmc]"
						
					if ".mp4" in match2[1]:
						subtitle = "[MP4-Directo]"
					scrapedtitle = '%s  - (%s)  %s' %(title,match2[0],subtitle)
					
					scrapedurl = match2[1].strip()
					scrapedthumbnail = thumbnail
					scrapedplot = plot
					
					if match2[2].endswith(".srt"): 
						scrapedurl = scrapedurl + "|" + match2[2]
						playWithSubt = "play2"
							
					if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")
							
					# Añade al listado de XBMC
					xbmctools.addnewvideo( CHANNELNAME , playWithSubt , category , "Directo" , scrapedtitle, scrapedurl , scrapedthumbnail, scrapedplot )
				
			else:
				if match.endswith(".srt"):
					scrapedurl = scrapedurl + "|" + match 
					xbmctools.addnewvideo( CHANNELNAME ,"play2"  , category , "Directo" , title + " (V.O.S) - "+subtitle, scrapedurl , thumbnail , plot )
				if 	match.endswith(".xml"):
					sub = "[Subtitulo incompatible con xbmc]"
					xbmctools.addnewvideo( CHANNELNAME ,"play"  , category , "Directo" , title + " (V.O) - %s %s" %(subtitle,sub), scrapedurl , thumbnail , plot )
				scrapedurl = match
				print scrapedurl
	#src="http://pelisflv.net63.net/player/videos.php?x=http://pelisflv.net63.net/player/xmls/The-Lord-Of-The-Ring.xml"			
	patronvideos = '(http\:\/\/[^\/]+\/[^\/]+\/[^\/]+\/[^\.]+\.xml)'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)
	#print data
	
	if len(matches)>0:
		for match in matches:
			subtitle = "[FLV-Directo]"
					
			data2 = scrapertools.cachePage(match)
			logger.info("data2="+data2)
			patronvideos  = '<track>.*?'
			patronvideos += '<title>([^<]+)</title>.*?'
			patronvideos += '<location>([^<]+)</location>(?:[^<]+'
			patronvideos += '<meta rel="captions">([^<]+)</meta>[^<]+'
			patronvideos += '|([^<]+))</track>'
			matches2 = re.compile(patronvideos,re.DOTALL).findall(data2)
			scrapertools.printMatches(matches)
			for match2 in matches2:
				sub = ""
				playWithSubt = "play"
				if match2[2].endswith(".xml"): # Subtitulos con formato xml son incompatibles con XBMC
					sub = "[Subtitulo incompatible con xbmc]"
					
				if  match2[1].endswith(".mp4"):
					subtitle = "[MP4-Directo]"
				scrapedtitle = '%s  - (%s)  %s' %(title,match2[0],subtitle)
				
				scrapedurl = match2[1].strip()
				scrapedthumbnail = thumbnail
				scrapedplot = plot
				
				if match2[2].endswith(".srt"): 
					scrapedurl = scrapedurl + "|" + match2[2]
					playWithSubt = "play2"
						
				if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")
						
				# Añade al listado de XBMC
				xbmctools.addnewvideo( CHANNELNAME , playWithSubt , category , "Directo" , scrapedtitle, scrapedurl , scrapedthumbnail, scrapedplot )					

	# Busca enlaces en el servidor Videoweed - "el modulo servertools.findvideos() no los encuentra"
	patronvideos = '(http\:\/\/[^\.]+\.videoweed.com\/[^"]+)"'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)
	if len(matches)>0:
		logger.info(" Servidor Videoweed")
		for match in matches:
			scrapedurl = match.replace("&amp;","&")
			xbmctools.addnewvideo( CHANNELNAME ,"play"  , category , "Videoweed" , title+" - [Videoweed]", scrapedurl , thumbnail , plot )		
	
	# Busca enlaces en el servidor Gigabyteupload # http://cdn-2.gigabyteupload.com/files/207bb7b658d5068650ebabaca8ffc52d/vFuriadeTitanes_newg.es.avi
	patronvideos = '(http\:\/\/[^\.]+\.gigabyteupload.com\/[^"]+)"'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)
	if len(matches)>0:
		logger.info(" Servidor Gigabyteupload")
		for match in matches:
			
			xbmctools.addnewvideo( CHANNELNAME ,"play"  , category , "Gigabyteupload" , title+" - [Gigabyteupload]",match  , thumbnail , plot )

	## --------------------------------------------------------------------------------------##
	#            Busca enlaces de videos para el servidor vk.com                             #
	## --------------------------------------------------------------------------------------##
	'''
	var video_host = '447.gt3.vkadre.ru';
	var video_uid = '0';
	var video_vtag = '2638f17ddd39-';
	var video_no_flv = 0;
	var video_max_hd = '0';
	var video_title = 'newCine.NET+-+neWG.Es+%7C+Chicken+Little';

	'''
	patronvideos = '<iframe src="(http://vk.com/video_ext.php[^"]+)"'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	if len(matches)>0:
		print " encontro VK.COM :%s" %matches[0]
 		
		data2 = scrapertools.downloadpageGzip(matches[0])
		print data2
		regexp =re.compile(r'vkid=([^\&]+)\&')
		match = regexp.search(data2)
		vkid = ""
		print 'match %s'%str(match)
		if match is not None:
			vkid = match.group(1)
		else:
			print "no encontro vkid"
			
		patron  = "var video_host = '([^']+)'.*?"
		patron += "var video_uid = '([^']+)'.*?"
		patron += "var video_vtag = '([^']+)'.*?"
		patron += "var video_no_flv = ([^;]+);.*?"
		patron += "var video_max_hd = '([^']+)'"
		matches2 = re.compile(patron,re.DOTALL).findall(data2)
		if len(matches2)>0:    
			for match in matches2:
				if match[3].strip() == "0" and match[1] != "0":
					tipo = "flv"
					videourl = "%s/u%s/video/%s.%s" % (match[0],match[1],match[2],tipo)
					xbmctools.addnewvideo( CHANNELNAME , "play" , category , "Directo" , title + " - "+"[VK] [%s]" %tipo, videourl , thumbnail , plot )
				elif match[1]== "0" and vkid != "":     #http://447.gt3.vkadre.ru/assets/videos/2638f17ddd39-75081019.vk.flv
					tipo = "flv"
					videourl = "%s/assets/videos/%s%s.vk.%s" % (match[0],match[1],vkid,tipo)
					xbmctools.addnewvideo( CHANNELNAME , "play" , category , "Directo" , title + " - "+"[VK] [%s]" %tipo, videourl , thumbnail , plot )
				else:
					tipo = "360.mp4"
					videourl = "%s/u%s/video/%s.%s" % (match[0],match[1],match[2],tipo)
					xbmctools.addnewvideo( CHANNELNAME , "play" , category , "Directo" , title + " - "+"[VK] [%s]" %tipo, videourl , thumbnail , plot )
					tipo = "240.mp4"
					videourl = "%s/u%s/video/%s.%s" % (match[0],match[1],match[2],tipo)
					xbmctools.addnewvideo( CHANNELNAME , "play" , category , "Directo" , title + " - "+"[VK] [%s]" %tipo, videourl , thumbnail , plot )
		


	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
		
	# Disable sorting...
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )


def play(params,url,category):
	logger.info("[pelisflv.py] play")

	title = unicode( xbmc.getInfoLabel( "ListItem.Title" ), "utf-8" )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = unicode( xbmc.getInfoLabel( "ListItem.Plot" ), "utf-8" )
	server = params["server"]

	xbmctools.playvideo(CHANNELNAME,server,url,category,title,thumbnail,plot)

def play2(params,url,category):
	logger.info("[pelisflv.py] play2")
	url1 = url
	if "|" in url:
		urlsplited = url.split("|")
		url1 = urlsplited[0]
		urlsubtit = urlsplited[1]
		subt_ok = "0"
		count = 0
		while subt_ok == "0":
			if count==0:
				subt_ok = downloadstr(urlsubtit)
				count += 1 
			print "subtitulo subt_ok = %s" % str(subt_ok)
			if subt_ok is None: # si es None la descarga del subtitulo esta ok
				config.setSetting("subtitulo", "true")
				break
	play(params,url1,category)

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
        
def downloadstr(urlsub):
	
	import downloadtools
	
	fullpath = os.path.join( config.DATA_PATH , 'subtitulo.srt' )
	if os.path.exists(fullpath):
		try:
			subtitfile = open(fullpath,"w")
			subtitfile.close()
		except IOError:
			logger.info("Error al limpiar el archivo subtitulo.srt "+fullpath)
			raise
	try:		
		ok = downloadtools.downloadfile(urlsub,fullpath)
	except IOError:
		logger.info("Error al descargar el subtitulo "+urlsub)
		return -1
	return ok

        
