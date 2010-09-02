# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para nolomires.com by Bandavi
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

CHANNELNAME = "nolomires"

# Esto permite su ejecución en modo emulado
try:
	pluginhandle = int( sys.argv[ 1 ] )
except:
	pluginhandle = ""

# Traza el inicio del canal
logger.info("[nolomires.py] init")

DEBUG = True

def mainlist(params,url,category):
	logger.info("[nolomires.py] mainlist")

	# Añade al listado de XBMC
	xbmctools.addnewfolder( CHANNELNAME , "search" , category , "Buscar","http://www.nolomires.com/","","")
	xbmctools.addnewfolder( CHANNELNAME , "LastSearch" , category , "Peliculas Buscadas Recientemente","http://www.nolomires.com/tag/estrenos-2010/","","")
	xbmctools.addnewfolder( CHANNELNAME , "listvideosMirror" , category , "Ultimos Estrenos","http://www.nolomires.com/","","")
	xbmctools.addnewfolder( CHANNELNAME , "TagList"         , category , "Tag de Estrenos por año"    ,"http://www.nolomires.com/","","")
	xbmctools.addnewfolder( CHANNELNAME , "MostWatched" , category , "Peliculas Mas Vistas","http://www.nolomires.com/","","")
	xbmctools.addnewfolder( CHANNELNAME , "ListaCat"         , category , "Listado por Categorias"    ,"http://www.nolomires.com/","","")
	xbmctools.addnewfolder( CHANNELNAME , "listvideos"       , category , "Ultimas Películas Añadidas"    ,"http://www.nolomires.com/","","")
	
	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )

	# Disable sorting...
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def search(params,url,category):
	logger.info("[nolomires.py] search")

	keyboard = xbmc.Keyboard()
	#keyboard.setDefault('')
	keyboard.doModal()
	if (keyboard.isConfirmed()):
		tecleado = keyboard.getText()
		if len(tecleado)>0:
			#convert to HTML
			tecleado = tecleado.replace(" ", "+")
			searchUrl = "http://www.nolomires.com/?s="+tecleado+"&x=15&y=19"
			listvideos(params,searchUrl,category)




def ListaCat(params,url,category):
	logger.info("[nolomires.py] ListaCat")
	
	
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "Acción","http://www.nolomires.com/category/peliculas-de-accion/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "Animado","http://www.nolomires.com/category/peliculas-de-animacion/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "Anime","http://www.nolomires.com/category/anime/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "Aventura","http://www.nolomires.com/category/peliculas-de-aventura/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "Bèlico Guerra ","http://www.nolomires.com/category/peliculas-de-guerra/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "Ciencia-Ficción","http://www.nolomires.com/category/peliculas-de-ciencia-ficcion/","","")
	#xbmctools.addnewfolder( CHANNELNAME ,"listvideosMirror", category , "Clásicos","http://www.nolomires.com/category/peliculasclasicos/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "Comedia","http://www.nolomires.com/category/peliculas-de-comedia/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "Documentales","http://www.nolomires.com/category/peliculas-sobre-documentales/","","")
	#xbmctools.addnewfolder( CHANNELNAME ,"listvideosMirror", category , "Destacado","http://www.nolomires.com/category/peliculasdestacado/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "Documentales Online","http://www.nolomires.com/category/documentales-online-completos/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "Drama","http://www.nolomires.com/category/peliculas-de-drama/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "Entretenimiento","http://www.nolomires.com/category/entretenimiento/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "Estrenos","http://www.nolomires.com/category/ultimos-extrenos/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "General","http://www.nolomires.com/category/general/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "Intriga","http://www.nolomires.com/category/peliculas-de-intriga/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "Musicales","http://www.nolomires.com/category/peliculas-musicales/","","")
	#xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "Peliculas HD","http://www.nolomires.com/category/peliculaspeliculas-hd-categorias/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "Romance","http://www.nolomires.com/category/peliculas-sobre-romance/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "Suspenso","http://www.nolomires.com/category/peliculas-de-suspenso/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "Terror","http://www.nolomires.com/category/peliculas-de-terror/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "Thriller","http://www.nolomires.com/category/peliculas-de-thriller/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "Todas las Peliculas","http://www.nolomires.com/category/peliculas-en-nolomires/","","")
	
	
	
	# Asigna el título, desactiva la ordenación, y cierra el directorio
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )



        
def TagList(params,url,category):
	logger.info("[nolomires.py] TagList")

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
		scrapedtitle = acentos(match[1])
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
        
def MostWatched(params,url,category):
	logger.info("[nolomires.py] MostWatched")

	# Descarga la página
	data = scrapertools.cachePage(url)
	#logger.info(data)


	# Patron de las entradas
	patronvideos  = '<li><a href="([^"]+)"  '      # URL
	patronvideos += 'title="([^"]+)">[^<]+'        # TITULO
	patronvideos += '</a>([^<]+)</li>'             # Cantidad de Vistos
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	# Añade las entradas encontradas
	for match in matches:
		# Atributos
		scrapedtitle = acentos(match[1] + match[2])
		scrapedurl = match[0]
		scrapedthumbnail = ""
		scrapedplot = ""
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELNAME , "detail" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )


	# Asigna el título, desactiva la ordenación, y cierra el directorio
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def LastSearch(params,url,category):
	logger.info("[nolomires.py] LastSearch")

	# Descarga la página
	data = scrapertools.cachePage(url)
	#logger.info(data)


	# Patron de las entradas
	patronvideos  = '<li><a href="([^"]+)" '      # URL
	patronvideos += 'title="([^"]+)" >[^<]+'       # TITULO
	patronvideos += '</a></li>'                    # Basura
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	# Añade las entradas encontradas
	for match in matches:
		# Atributos
		scrapedtitle = acentos(match[1])
		scrapedtitle = scrapedtitle.replace("online","").replace("ver ","")
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
	logger.info("[nolomires.py] listvideos")

	if url=="":
		url = "http://www.nolomires.com/"
                
	# Descarga la página
	data = scrapertools.cachePage(url)
	#logger.info(data)


	# Extrae las entradas (carpetas)
	patronvideos  =  '<div class="videoitem">.*?<a href="([^"]+)" '     # URL 0
	patronvideos +=  'title="([^"]+)">'                                 # TITULO 1
	patronvideos +=  '<img style="background: url\(([^\)]+)\)"'         # IMAGEN  2
	#patronvideos += '</div>[^<]+<div class=[^>]+>.*?href="[^"]+"><img '                    
	#patronvideos += 'style=.*?src="([^"]+)".*?alt=.*?bold.*?>(.*?)</div>'                  # IMAGEN , DESCRIPCION
	#patronvideos += '.*?flashvars="file=(.*?flv)\&amp'                                      # VIDEO FLV 
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	for match in matches:
		# Titulo
		
		scrapedtitle = acentos(match[1])
		# URL
		scrapedurl = match[0]
		# Thumbnail
		scrapedthumbnail = match[2]
		# Argumento
		scrapedplot = ""
		

		# Depuracion
		if (DEBUG):
			logger.info("scrapedtitle="+scrapedtitle)
			logger.info("scrapedurl="+scrapedurl)
			logger.info("scrapedthumbnail="+scrapedthumbnail)

		
			# Añade al listado de XBMC
			xbmctools.addnewfolder( CHANNELNAME , "detail" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	#Extrae la marca de siguiente página
	patronvideos  = '<a href="([^"]+)" class="nextpostslink">'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	if len(matches)>0:
		pag = re.compile("http.*?/page/([^/]+)/").findall(matches[0])
		scrapedtitle = "Página siguiente (Nro.%s)" %pag[0]
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

def listvideosMirror(params,url,category):
	logger.info("[nolomires.py] listvideosMirror")

	if url=="":
		url = "http://www.nolomires.com/"
                
	# Descarga la página
	data = scrapertools.cachePage(url)
	#logger.info(data)


	# Extrae las entradas (carpetas)
	patronvideos  =  '<div class="panel" id="[^"]+" style="background: url\(([^\)]+)\).*?'      # IMAGEN   0
	patronvideos +=  '<h2><a href="([^"]+)" '                                                  # URL      1
	patronvideos +=  'title="([^"]+)">[^<]+</a>'                                               # TITULO   2
	patronvideos += '</h2>(.*?)</div>'                                                         # SINOPSIS 3
	#patronvideos += 'style=.*?src="([^"]+)".*?alt=.*?bold.*?>(.*?)</div>'                 
	#patronvideos += '.*?flashvars="file=(.*?flv)\&amp'                                     
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	for match in matches:
		# Titulo
		
		scrapedtitle = acentos(match[2])
		# URL
		scrapedurl = match[1]
		# Thumbnail
		scrapedthumbnail = match[0]
		# Argumento
		scrapedplot = match[3]
		

		# Depuracion
		if (DEBUG):
			logger.info("scrapedtitle="+scrapedtitle)
			logger.info("scrapedurl="+scrapedurl)
			logger.info("scrapedthumbnail="+scrapedthumbnail)

		
			# Añade al listado de XBMC
			xbmctools.addnewfolder( CHANNELNAME , "detail" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	#Extrae la marca de siguiente página
	patronvideos  = '<a href="([^"]+)" class="nextpostslink">'
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
	logger.info("[nolomires.py] detail")

	title = acentos(urllib.unquote_plus( params.get("title") ))
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = ""
	scrapedurl = ""
	# Descarga la página
	data = scrapertools.cachePage(url)
	#logger.info(data)
    # Extrae el argumento
	patronarg = '<h[2-3]>(<span style.*?)</p>'
	matches   = re.compile(patronarg,re.DOTALL).findall(data)
	if len(matches)>0:
		plot  = re.sub("<[^>]+>"," ",matches[0])
	patronthumb = '<div id="textimg"><img src="([^"]+)"'
	matches   = re.compile(patronthumb,re.DOTALL).findall(data)
	if len(matches)>0:
		thumbnail = matches[0]
	# ------------------------------------------------------------------------------------
	# Busca los enlaces a los videos en los servidores habilitados
	# ------------------------------------------------------------------------------------
	
	listavideos = servertools.findvideos(data)

	for video in listavideos:
		
		videotitle = video[0]
		url = video[1]
		server = video[2]
		xbmctools.addnewvideo( CHANNELNAME , "play" , category , server , title.strip() + " - " + videotitle , url , thumbnail , plot )
	
   
			
	## --------------------------------------------------------------------------------------##
	#               Busca enlaces a videos .flv o (.mp4 dentro de un xml)                     #
	## --------------------------------------------------------------------------------------##
	patronvideos = 'file=(http\:\/\/[^\&]+)\&'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)
	playWithSubt = "play"
	c = 0
	if len(matches)>0:
		for match in matches:
			print "link xml :%s" %match
			subtitle = "[FLV-Directo]"
			c += 1
			sub = ""
			if ("/xml" in match):
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
				if len(matches2)==0:
					newpatron = '<title>([^<]+)</title>[^<]+<location>([^<]+)</location>'
					matches2 = re.compile(newpatron,re.DOTALL).findall(data2)
					sub = "None"
				for match2 in matches2:
					
					try:
						if match2[2].endswith(".xml"): # Subtitulos con formato xml son incompatibles con XBMC
							sub = "[Subtitulo incompatible con xbmc]"
							playWithSubt = "play"
					except:
						pass
					if ".mp4" in match2[1]:
						subtitle = "[MP4-Directo]"
					scrapedtitle = '%s (castellano) - %s  %s' %(title,match2[0],subtitle)
					
					scrapedurl = match2[1].strip()
					scrapedthumbnail = thumbnail
					scrapedplot = plot
					if ("cast.xml" or "mirror.xml") not in match and sub == "":
						scrapedtitle = '%s (V.O.S) - %s  %s %s' %(title,match2[0],subtitle,sub)
						try:
							if not match2[2].endswith("cine-adicto2.srt") and (sub == ""): 
								scrapedurl = scrapedurl + "|" + match2[2]
								playWithSubt = "play2"
						except:pass	
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
	
	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
		
	# Disable sorting...
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )



def play(params,url,category):
	logger.info("[nolomires.py] play")

	title = unicode( xbmc.getInfoLabel( "ListItem.Title" ), "utf-8" )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = unicode( xbmc.getInfoLabel( "ListItem.Plot" ), "utf-8" )
	server = params["server"]

	xbmctools.playvideo(CHANNELNAME,server,url,category,title,thumbnail,plot)

def play2(params,url,category):
	logger.info("[nolomires.py] play2")
	url1 = url
	if "|" in url:
		urlsplited = url.split("|")
		url1 = urlsplited[0]
		urlsubtit = urlsplited[1]
		subt_ok = "0"
		while subt_ok == "0":
			subt_ok = downloadstr(urlsubtit)
			print "subtitulo subt_ok = %s" % str(subt_ok)
			if subt_ok is None: # si es None la descarga del subtitulo esta ok
				config.setSetting("subtitulo", "true")
				break
	play(params,url1,category)


def acentos(title):

        title = title.replace("&#8211;","-")
        title = title.replace("&nbsp;"," ")
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
	
	fullpath = os.path.join( config.DATA_PATH, 'subtitulo.srt' )
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

def getpost(url,values): # Descarga la pagina con envio de un Form
	
	#url=url
	try:
		data = urllib.urlencode(values)          
		req = urllib2.Request(url, data)
		response = urllib2.urlopen(req)
		the_page = response.read() 
		return the_page 
	except Exception: 
		return "Err " 	
