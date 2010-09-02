# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para peliculasid
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

CHANNELNAME = "peliculasid"

# Esto permite su ejecución en modo emulado
try:
	pluginhandle = int( sys.argv[ 1 ] )
except:
	pluginhandle = ""

# Traza el inicio del canal
logger.info("[peliculasid.py] init")

DEBUG = True

def mainlist(params,url,category):
	logger.info("[peliculasid.py] mainlist")

	# Añade al listado de XBMC
	xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , "Ultimas Películas Subidas"    ,"http://www.peliculasid.com/","","")
	#xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , "Estrenos","http://www.peliculasid.net/index.php?module=estrenos","","")
	#xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , "Series","http://www.peliculasid.net/index.php?module=series","","")
	xbmctools.addnewfolder( CHANNELNAME , "listcategorias" , category , "Categorias"        ,"http://www.peliculasid.com/","","")
	#xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , "Buscar","http://www.peliculasid.net/index.php?module=documentales","","")

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )

	# Disable sorting...
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def listcategorias(params,url,category):
        logger.info("[peliculas.py] listcategorias")
		
        xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , "2008"    ,"http://peliculasid.com/2008-1.html","","")
        xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , "2009"    ,"http://peliculasid.com/2009-1.html","","")
        xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , "2010"    ,"http://peliculasid.com/2010-1.html","","")
        xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , "Acción"    ,"http://www.peliculasid.com/accion-1.html","","")
        xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , "Animación"    ,"http://www.peliculasid.com/animacion-1.html","","")
        xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , "Aventura"    ,"http://www.peliculasid.com/aventura-1.html","","")
        xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , "Ciencia Ficción"    ,"http://www.peliculasid.com/ciencia_ficcion-1.html","","")
        xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , "Cine Indio"    ,"http://www.peliculasid.com/cine_indio-1.html","","")
        xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , "Comedia"    ,"http://www.peliculasid.com/comedia-1.html","","")
        xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , "Crimen"    ,"http://www.peliculasid.com/crimen-1.html","","")
        xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , "Documentales y mas"    ,"http://www.peliculasid.com/documentales-1.html","","")
        xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , "Drama"    ,"http://www.peliculasid.com/drama-1.html","","")
        xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , "Fantasia"    ,"http://www.peliculasid.com/fantasia-1.html","","")
        xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , "Horror"    ,"http://www.peliculasid.com/horror-1.html","","")
        xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , "Misterio"    ,"http://www.peliculasid.com/misterio-1.html","","")
        xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , "Romance"    ,"http://www.peliculasid.com/romance-1.html","","")
        xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , "Thriller"    ,"http://www.peliculasid.com/thriller-1.html","","")
        
        # Label (top-right)...
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )

	# Disable sorting...
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )
        

def listvideos(params,url,category):
	logger.info("[peliculasid.py] listvideos")

	if url=="":
		url = "http://www.peliculasid.com/"
                
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
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )

	# Disable sorting...
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

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
        if DEBUG:
          if len(matches)>0:
		descripcion = matches[0]
                descripcion = descripcion.replace('&#8220;','"')
                descripcion = descripcion.replace('&#8221;','"')
                descripcion = descripcion.replace('&#8230;','...')
                descripcion = descripcion.replace('&#8217;',"'")
                descripcion = descripcion.replace("&nbsp;","")
		descripcion = descripcion.replace("<br/>","")
		descripcion = descripcion.replace("\r","")
		descripcion = descripcion.replace("\n"," ")
                descripcion = descripcion.replace("\t"," ")
		descripcion = re.sub("<[^>]+>"," ",descripcion)
#                logger.info("descripcion="+descripcion)
                descripcion = acentos(descripcion)
#                logger.info("descripcion="+descripcion)
                try :
                    plot = unicode( descripcion, "utf-8" ).encode("iso-8859-1")
                except:
                    plot = descripcion

        #--- Busca los videos Directos
        patronvideos = 'flashvars" value="file=([^\&]+)\&amp'
        matches = re.compile(patronvideos,re.DOTALL).findall(data)
        
        if len(matches)>0:
          if ("xml" in matches[0]):  
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
	patronvideos = '<a href="(http://peliculasid.com/iframeplayer.php[^"]+)" target="[^"]+">([^<]+)</a>'
	#patronvideos2 = 'file=([^\&]+)\&'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	if len(matches)>0:
		for match in matches:
			#data2 = scrapertools.cachePage(match[0])
			#matches2 = re.compile(patronvideos2,re.DOTALL).findall(data2)
			xbmctools.addnewvideo( CHANNELNAME , "play" , category , "Directo" , title+" - "+match[1], match[0] , thumbnail , plot )
	
	## --------------------------------------------------------------------------------------##
	#            Busca enlaces de videos para el servidor vkontakte.ru                        #
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
		if len(matches2)>0:    #http://cs12385.vkontakte.ru/u88260894/video/d09802a95b.360.mp4
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
			
	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def play(params,url,category):
	logger.info("[peliculasid.py] play")
	
	
	title = unicode( xbmc.getInfoLabel( "ListItem.Title" ), "utf-8" )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	try:
		plot = unicode( xbmc.getInfoLabel( "ListItem.Plot" ), "utf-8" )
	except:
		plot = xbmc.getInfoLabel( "ListItem.Plot" )
	server = params["server"]
	
	if "iframeplayer.php" in url:      #"http://peliculasid.com/iframeplayer.php?url=aHR0cDovL3ZpZGVvLmFrLmZhY2Vib29rLmNvbS9jZnMtYWstc25jNC80MjIxNi82MS8xMjgxMTI4ODgxOTUwXzM5NTAwLm1wNA=="
		data = scrapertools.cachePage(url)
		patronvideos = 'file=([^\&]+)\&'
		matches = re.compile(patronvideos,re.DOTALL).findall(data)
		if len(matches)>0:
			url = matches[0]
	
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
