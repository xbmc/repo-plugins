# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para cine-adicto.com by Bandavi
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

CHANNELNAME = "cineadicto"

# Esto permite su ejecución en modo emulado
try:
	pluginhandle = int( sys.argv[ 1 ] )
except:
	pluginhandle = ""

# Traza el inicio del canal
logger.info("[cineadicto.py] init")

DEBUG = True

def mainlist(params,url,category):
	logger.info("[cineadicto.py] mainlist")

	# Añade al listado de XBMC
	xbmctools.addnewfolder( CHANNELNAME , "listvideos"       , category , "Ultimas Películas Añadidas"    ,"http://www.cine-adicto.com/","","")
	xbmctools.addnewfolder( CHANNELNAME , "ListaCat"         , category , "Listado por Genero"    ,"http://www.cine-adicto.com/","","")
	xbmctools.addnewfolder( CHANNELNAME , "ListaAlfa"         , category , "Listado Alfanumerico"    ,"http://www.cine-adicto.com/","","")
	xbmctools.addnewfolder( CHANNELNAME , "ListvideosMirror" , category , "Estrenos","http://www.cine-adicto.com/category/categorias/estrenos","","")
	xbmctools.addnewfolder( CHANNELNAME , "ListvideosMirror" , category , "Documentales","http://www.cine-adicto.com/category/categorias/documentales/","","")
	xbmctools.addnewfolder( CHANNELNAME , "ListvideosMirror" , category , "Peliculas en HD","http://www.cine-adicto.com/category/categorias/peliculas-hd-categorias","","")
	xbmctools.addnewfolder( CHANNELNAME , "search" , category , "Buscar","http://www.cine-adicto.com/","","")

	if config.getSetting("singlechannel")=="true":
		xbmctools.addSingleChannelOptions(params,url,category)

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )

	# Disable sorting...
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def search(params,url,category):
	logger.info("[cineadicto.py] search")

	keyboard = xbmc.Keyboard()
	#keyboard.setDefault('')
	keyboard.doModal()
	if (keyboard.isConfirmed()):
		tecleado = keyboard.getText()
		if len(tecleado)>0:
			#convert to HTML
			tecleado = tecleado.replace(" ", "+")
			searchUrl = "http://www.cine-adicto.com/?s="+tecleado
			searchresults(params,searchUrl,category)

def searchresults(params,url,category):
	logger.info("[cineadicto.py] SearchResult")
	
	
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
			

def ListaCat(params,url,category):
	logger.info("[cineadicto.py] ListaCat")
	import downloadtools
	nombrefichero = ""
	fullpath = os.path.join( downloadtools.getDownloadPath(),"subtitulos" , nombrefichero )
	urlfile = "http://www.subtitulos.es/updated/5/10855/0"
	fullnombrefichero = downloadtools.downloadfileGzipped(urlfile,fullpath)
	print fullnombrefichero
	fichero = os.path.basename(fullnombrefichero).encode('utf-8')
	print fichero
	fichero = u'%s' %fichero
	print fichero
	
	
	
	xbmctools.addnewfolder( CHANNELNAME ,"ListvideosMirror", category , "Acción","http://www.cine-adicto.com/category/categorias/accion/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"ListvideosMirror", category , "Animado","http://www.cine-adicto.com/category/categorias/animado/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"ListvideosMirror", category , "Anime","http://www.cine-adicto.com/category/categorias/anime/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"ListvideosMirror", category , "Asiáticas","http://www.cine-adicto.com/category/categorias/asiaticas/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"ListvideosMirror", category , "Aventuras","http://www.cine-adicto.com/category/categorias/aventura/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"ListvideosMirror", category , "Ciencia-Ficción","http://www.cine-adicto.com/category/categorias/ciencia-ficcion/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"ListvideosMirror", category , "Clásicos","http://www.cine-adicto.com/category/categorias/clasicos/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideosMirror", category , "Comedia","http://www.cine-adicto.com/category/categorias/comedia/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideosMirror", category , "Comedias Romanticas","http://www.cine-adicto.com/category/categorias/comedias-romanticas/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideosMirror", category , "Destacado","http://www.cine-adicto.com/category/categorias/destacado/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideosMirror", category , "Documentales","http://www.cine-adicto.com/category/categorias/documentales/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"ListvideosMirror", category , "Drama","http://www.cine-adicto.com/category/categorias/drama/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"ListvideosMirror", category , "Español Latino","http://www.cine-adicto.com/category/categorias/espanol-latino/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"ListvideosMirror", category , "Estreno","http://www.cine-adicto.com/category/categorias/estreno/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"ListvideosMirror", category , "Infantil","http://www.cine-adicto.com/category/categorias/infantil/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideosMirror", category , "Intriga","http://www.cine-adicto.com/category/categorias/intriga/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"ListvideosMirror", category , "Musicales","http://www.cine-adicto.com/category/categorias/musicales/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideosMirror", category , "Peliculas HD","http://www.cine-adicto.com/category/categorias/peliculas-hd-categorias/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"ListvideosMirror", category , "Romance","http://www.cine-adicto.com/category/categorias/romance/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideosMirror", category , "Suspenso","http://www.cine-adicto.com/category/categorias/suspenso/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"ListvideosMirror", category , "Terror","http://www.cine-adicto.com/category/categorias/terror/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"ListvideosMirror", category , "Thriller","http://www.cine-adicto.com/category/categorias/thriller/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"ListvideosMirror", category , "Western","http://www.cine-adicto.com/category/categorias/western/","","")
	
	# Asigna el título, desactiva la ordenación, y cierra el directorio
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def ListaAlfa(params, url, category):

	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "0-9","http://www.cine-adicto.com/tag/9/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "A","http://www.cine-adicto.com/tag/a/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "B","http://www.cine-adicto.com/tag/b/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "C","http://www.cine-adicto.com/tag/c/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "D","http://www.cine-adicto.com/tag/d/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "E","http://www.cine-adicto.com/tag/e/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "F","http://www.cine-adicto.com/tag/f/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "G","http://www.cine-adicto.com/tag/g/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "H","http://www.cine-adicto.com/tag/h/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "I","http://www.cine-adicto.com/tag/i/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "J","http://www.cine-adicto.com/tag/j/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "K","http://www.cine-adicto.com/tag/k/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "L","http://www.cine-adicto.com/tag/l/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "M","http://www.cine-adicto.com/tag/m/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "N","http://www.cine-adicto.com/tag/n/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "O","http://www.cine-adicto.com/tag/o/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "P","http://www.cine-adicto.com/tag/p/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "Q","http://www.cine-adicto.com/tag/q/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "R","http://www.cine-adicto.com/tag/r/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "S","http://www.cine-adicto.com/tag/s/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "T","http://www.cine-adicto.com/tag/t/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "U","http://www.cine-adicto.com/tag/u/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "V","http://www.cine-adicto.com/tag/v/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "W","http://www.cine-adicto.com/tag/w/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "X","http://www.cine-adicto.com/tag/x/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "Y","http://www.cine-adicto.com/tag/y/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "Z","http://www.cine-adicto.com/tag/z/","","")

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )



        
def ListvideosMirror(params,url,category):
	logger.info("[cineadicto.py] ListvideosMirror")

	# Descarga la página
	data = scrapertools.cachePage(url)
	#logger.info(data)


	# Patron de las entradas
	patronvideos  = '<div class="poster">[^<]+<a href="([^"]+)"'                          # URL
	patronvideos += '><img src="([^"]+)" width=[^\/]+\/>'                                # TUMBNAIL
	patronvideos += '</a>[^<]+<[^>]+>[^<]+<[^>]+>[^<]+<a href="[^"]+">([^<]+)</a>'        # TITULO 
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	# Añade las entradas encontradas
	for match in matches:
		# Atributos
		scrapedtitle = match[2]
		scrapedurl = match[0]
		scrapedthumbnail = match[1]
		scrapedplot = ""
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELNAME , "detail" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	#Extrae la marca de siguiente página
	patronvideos  = '</span><a href="(http://www.cine-adicto.com/.*?page/[^"]+)"'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	if len(matches)>0:
		scrapedtitle = "Página siguiente"
		scrapedurl = matches[0]
		scrapedthumbnail = ""
		scrapedplot = ""
		xbmctools.addnewfolder( CHANNELNAME , "ListvideosMirror" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# Asigna el título, desactiva la ordenación, y cierra el directorio
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )
        

def listvideos(params,url,category):
	logger.info("[cineadicto.py] listvideos")

	if url=="":
		url = "http://www.cine-adicto.com/"
                
	# Descarga la página
	data = scrapertools.cachePage(url)
	#logger.info(data)


	# Extrae las entradas (carpetas)
	patronvideos  =  '<div class="poster">[^<]+<a href="([^"]+)"'     # URL
	patronvideos +=  '><img src="([^"]+)" '                             # TUMBNAIL
	patronvideos +=  'width=.*?title="([^"]+)" /></a>'                  # TITULO 
	#patronvideos += '</div>[^<]+<div class=[^>]+>.*?href="[^"]+"><img '                    
	#patronvideos += 'style=.*?src="([^"]+)".*?alt=.*?bold.*?>(.*?)</div>'                  # IMAGEN , DESCRIPCION
	#patronvideos += '.*?flashvars="file=(.*?flv)\&amp'                                      # VIDEO FLV 
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	for match in matches:
		# Titulo
		
		scrapedtitle = match[2]
		# URL
		scrapedurl = match[0]
		# Thumbnail
		scrapedthumbnail = match[1]
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
	patronvideos  = '</span><a href="(http://www.cine-adicto.com/page/[^"]+)"'
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
	logger.info("[cineadicto.py] detail")

	title = urllib.unquote_plus( params.get("title") )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = ""
	scrapedurl = ""
	# Descarga la página
	data = scrapertools.cachePage(url)
	#logger.info(data)
    # Extrae el argumento
	patronarg = '</p><p>.*?<strong>([^<]+</strong> <strong>.*?)<p></p>'
	matches   = re.compile(patronarg,re.DOTALL).findall(data)
	if len(matches)>0:
		plot  = re.sub("<[^>]+>"," ",matches[0])
  
	# ------------------------------------------------------------------------------------
	# Busca los enlaces a los videos en los servidores habilitados
	# ------------------------------------------------------------------------------------
	'''
	listavideos = servertools.findvideos(data)

	for video in listavideos:
		if "stagevu.com/embed" not in video[1]:
			videotitle = video[0]
			url = video[1]
			server = video[2]
			xbmctools.addnewvideo( CHANNELNAME , "play" , category , server , title.strip() + " - " + videotitle , url , thumbnail , plot )
	'''
   
			
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
			subtitle = "[FLV-Directo]"
			c += 1
			if ("playlist" in match):
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
					if match2[2].endswith(".xml"): # Subtitulos con formato xml son incompatibles con XBMC
						sub = "[Subtitulo incompatible con xbmc]"
						playWithSubt = "play"
					if ".mp4" in match2[1]:
						subtitle = "[MP4-Directo]"
					scrapedtitle = '%s (castellano) - %s  %s' %(title,match2[0],subtitle)
					
					scrapedurl = match2[1].strip()
					scrapedthumbnail = thumbnail
					scrapedplot = plot
					if ("cast.xml" or "mirror.xml") not in match:
						scrapedtitle = '%s (V.O.S) - %s  %s %s' %(title,match2[0],subtitle,sub)
						if not match2[2].endswith("cine-adicto2.srt") and (sub == ""): 
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
	
	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
		
	# Disable sorting...
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )



def play(params,url,category):
	logger.info("[cineadicto.py] play")

	title = unicode( xbmc.getInfoLabel( "ListItem.Title" ), "utf-8" )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = unicode( xbmc.getInfoLabel( "ListItem.Plot" ), "utf-8" )
	server = params["server"]

	xbmctools.playvideo(CHANNELNAME,server,url,category,title,thumbnail,plot)

def play2(params,url,category):
	logger.info("[cineadicto.py] play2")
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
