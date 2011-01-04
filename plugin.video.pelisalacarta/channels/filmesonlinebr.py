# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para - Filmes Online BR
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
import string
import config
import logger

CHANNELNAME = "filmesonlinebr"

# Esto permite su ejecución en modo emulado
try:
	pluginhandle = int( sys.argv[ 1 ] )
except:
	pluginhandle = ""

# Traza el inicio del canal
logger.info("[filmesonlinebr.py] init")

DEBUG = True

def mainlist(params,url,category):
	logger.info("[filmesonlinebr.py] mainlist")

	# Añade al listado de XBMC
	xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , "Ultimos Filmes Subidos"    ,"http://www.filmesonlinebr.com/","","")
	#xbmctools.addnewfolder( CHANNELNAME , "listalfa" , category , "Lista Alfabética","http://www.filmesonlinebr.com/","","")
	#xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , "Series","http://www.filmesonlinebr.com/","","")
	xbmctools.addnewfolder( CHANNELNAME , "listcategorias" , category , "Categorias"        ,"http://www.filmesonlinebr.com/","","")
	if config.getSetting("enableadultmode") == "true":
		xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , "Filmes Adulto (+18)","http://www.filmesonlinebr.com/category/filmes-porno-xxx/","","")

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )

	# Disable sorting...
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def listcategorias(params,url,category):
	logger.info("[filmeonlinebr.py] listcategorias")


	xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , "Animações e Animes"    ,"http://www.filmesonlinebr.com/category/filmes-animacoes-e-animes/","","")
	xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , "Aventura"    ,"http://www.filmesonlinebr.com/category/filmes-aventura/","","")
	xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , "Comédia Romântica"    ,"http://www.filmesonlinebr.com/category/filmes-comedia-romantica/","","")
	xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , "Comédia"    ,"http://www.filmesonlinebr.com/category/filmes-comedia/","","")
	xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , "Documentário"    ,"http://www.filmesonlinebr.com/category/filmes-documentarios/","","")
	xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , "Fantasia"    ,"http://www.filmesonlinebr.com/category/filmes-fantasia/","","")
	#xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , "Ficção Científica*"    ,"http://www.filmesonlinebr.com/search/label/Fic%C3%A7%C3%A3o%20Cient%C3%ADfica","","")
	xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , "Guerra"    ,"http://www.filmesonlinebr.com/category/filmes-guerra/","","")
	xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , "Lançamentos 2010"    ,"http://www.filmesonlinebr.com/category/filmes-lancamentos-2010","","")
	#xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , "Musical e Shows*"    ,"http://www.filmesonlinebr.com/search/label/Musical","","")
	xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , "Filmes Brasileiros"    ,"http://www.filmesonlinebr.com/category/filmes-nacional/","","")
	#xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , "Policial*"    ,"http://www.filmesonlinebr.com/search/label/Policial","","")
	xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , "Romance"    ,"http://www.filmesonlinebr.com/category/filmes-romance/","","")
	xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , "Suspense"    ,"http://www.filmesonlinebr.com/category/filmes-suspense/","","")
	xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , "Terror"    ,"http://www.filmesonlinebr.com/category/filmes-terror/","","")
	xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , "Series"    ,"http://www.filmesonlinebr.com/category/series-online/","","")
	
    # Label (top-right)...
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )

	# Disable sorting...
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )
        
def listalfa(params,url,category):
	logger.info("[filmesonlinebr.py] listalfa")
	
	xbmctools.addnewfolderextra( CHANNELNAME ,"listvideos", category , "0-9","http://www.filmesonlinebr.com/search/label/0-9/","","","")
	xbmctools.addnewfolderextra( CHANNELNAME ,"listvideos", category , "A","http://www.filmesonlinebr.com/search/label/a/","","","")
	xbmctools.addnewfolderextra( CHANNELNAME ,"listvideos", category , "B","http://www.filmesonlinebr.com/search/label/B/","","","")
	xbmctools.addnewfolderextra( CHANNELNAME ,"listvideos", category , "C","http://www.filmesonlinebr.com/search/label/C/","","","")
	xbmctools.addnewfolderextra( CHANNELNAME ,"listvideos", category , "D","http://www.filmesonlinebr.com/search/label/D/","","","")
	xbmctools.addnewfolderextra( CHANNELNAME ,"listvideos", category , "E","http://www.filmesonlinebr.com/search/label/E/","","","")
	xbmctools.addnewfolderextra( CHANNELNAME ,"listvideos", category , "F","http://www.filmesonlinebr.com/search/label/F/","","","")
	xbmctools.addnewfolderextra( CHANNELNAME ,"listvideos", category , "G","http://www.filmesonlinebr.com/search/label/G/","","","")
	xbmctools.addnewfolderextra( CHANNELNAME ,"listvideos", category , "H","http://www.filmesonlinebr.com/search/label/H/","","","")
	xbmctools.addnewfolderextra( CHANNELNAME ,"listvideos", category , "I","http://www.filmesonlinebr.com/search/label/I/","","","")
	xbmctools.addnewfolderextra( CHANNELNAME ,"listvideos", category , "J","http://www.filmesonlinebr.com/search/label/J/","","","")
	xbmctools.addnewfolderextra( CHANNELNAME ,"listvideos", category , "K","http://www.filmesonlinebr.com/search/label/K/","","","")
	xbmctools.addnewfolderextra( CHANNELNAME ,"listvideos", category , "L","http://www.filmesonlinebr.com/search/label/L/","","","")
	xbmctools.addnewfolderextra( CHANNELNAME ,"listvideos", category , "M","http://www.filmesonlinebr.com/search/label/M/","","","")
	xbmctools.addnewfolderextra( CHANNELNAME ,"listvideos", category , "N","http://www.filmesonlinebr.com/search/label/N/","","","")
	xbmctools.addnewfolderextra( CHANNELNAME ,"listvideos", category , "O","http://www.filmesonlinebr.com/search/label/O/","","","")
	xbmctools.addnewfolderextra( CHANNELNAME ,"listvideos", category , "P","http://www.filmesonlinebr.com/search/label/P/","","","")
	xbmctools.addnewfolderextra( CHANNELNAME ,"listvideos", category , "Q","http://www.filmesonlinebr.com/search/label/Q/","","","")
	xbmctools.addnewfolderextra( CHANNELNAME ,"listvideos", category , "R","http://www.filmesonlinebr.com/search/label/R/","","","")
	xbmctools.addnewfolderextra( CHANNELNAME ,"listvideos", category , "S","http://www.filmesonlinebr.com/search/label/S/","","","")
	xbmctools.addnewfolderextra( CHANNELNAME ,"listvideos", category , "T","http://www.filmesonlinebr.com/search/label/T/","","","")
	xbmctools.addnewfolderextra( CHANNELNAME ,"listvideos", category , "U","http://www.filmesonlinebr.com/search/label/U/","","","")
	xbmctools.addnewfolderextra( CHANNELNAME ,"listvideos", category , "V","http://www.filmesonlinebr.com/search/label/V/","","","")
	xbmctools.addnewfolderextra( CHANNELNAME ,"listvideos", category , "W","http://www.filmesonlinebr.com/search/label/W/","","","")
	xbmctools.addnewfolderextra( CHANNELNAME ,"listvideos", category , "X","http://www.filmesonlinebr.com/search/label/X/","","","")
	xbmctools.addnewfolderextra( CHANNELNAME ,"listvideos", category , "Y","http://www.filmesonlinebr.com/","","","")
	xbmctools.addnewfolderextra( CHANNELNAME ,"listvideos", category , "Z","http://www.filmesonlinebr.com/search/label/Z/","","","")

        # Label (top-right)...
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )

	# Disable sorting...
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )
	
def listvideos(params,url,category):
	logger.info("[filmesonlinebr.py] listvideos")
	adulto = config.getSetting("enableadultmode")
	if url=="":
		url = "http://www.filmesonlinebr.com/"
                
	# Descarga la página
	data = scrapertools.cachePage(url)
	# Extrae la parte localizada del filme
	patronfilme  ='<div class="item">.*?<div class="thumbnail" style="background: url\(([^\)]+\)) top left no-repeat;">.*?'
	patronfilme  +='<h2><a href="([^"]+)">([^<]+)</a></h2>'
	matchesfilme = re.compile(patronfilme,re.DOTALL).findall(data)	

	for match in matchesfilme:
		# Titulo
		
		scrapedtitle = match[2]
		# URL
		scrapedurl = match[1]
		# Thumbnail
		scrapedthumbnail = match[0]
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
	patronvideos  = "<li><a class='next page-numbers' href='([^']+)'>"
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
	logger.info("[filmesonlinebr.py] detail")
	adulto = config.getSetting("enableadultmode")
	title = xbmc.getInfoLabel( "ListItem.Title" )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = unicode( xbmc.getInfoLabel( "ListItem.Plot" ), "utf-8" )
	if url=="":
		url = "http://www.filmesonlinebr.com/"
                
	# Descarga la página
	data = scrapertools.cachePage(url)


	# Extrae las entradas (videos) #
	patron = '<div id="article">[^<]+<h2>(.*?)<h2>Comments:</h2>'
	matchtype = re.compile(patron,re.DOTALL).findall(data)
	print "matchtype :%s" %matchtype[0]
	if ("porno"or"pornÃ´"or"xxx") in string.lower(matchtype[0]):
		if adulto == "false":
			advertencia()
			return
		matches = megasearch(matchtype,data)
		listar(title,thumbnail,plot,matches,category)
	else:
		patron = "<h2(.*?)</h2>"
		matchtemp = re.compile(patron,re.DOTALL).findall(data)
		print matchtemp
		if len(matchtemp)>0:
			patron = "<h2(.*?)</h2>"
			matchtemp = re.compile(patron,re.DOTALL).findall(matchtype[0])
			try:		
				if "Temporada " in matchtemp[0]:
					for match in matchtemp:
						patron = "<h2%s(.*?)</p>" %match[0]
						matchesdata = re.compile(patron,re.DOTALL).findall(matchtype[0])
						print matchesdata[0]
						matches = megasearch(matchtype,matchesdata[0])
						titulo = re.sub("<[^>]+>"," ",match).replace(">","")
						listar(titulo,thumbnail,plot,matches,category)
			except:
				matches = megasearch(matchtype,data)
				listar(title,thumbnail,plot,matches,category)
		
	close_directory(params,url,category)	
	# patron para: thumbnail , idioma , sinopsis y titulo

	#patronIdioma   = '<p>(.*?)Sinopse:'
	#patronSinopsis = "(Sinopse:.*?)</p>"


def play(params,url,category):
	logger.info("[filmesonlinebr.py] play")

	title = unicode( xbmc.getInfoLabel( "ListItem.Title" ), "utf-8" )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = unicode( xbmc.getInfoLabel( "ListItem.Plot" ), "utf-8" )
	server = params["server"]
	
	xbmctools.playvideo(CHANNELNAME,server,url,category,title,thumbnail,plot)

def listar(title,thumbnail,plot,matches,category):
	
	for match in matches:
		# Titulo
		
		scrapedtitle = title + match[0]
		# URL
		scrapedurl = match[1]
		# Thumbnail
		scrapedthumbnail = thumbnail
		# Argumento
		scrapedplot = plot
		

		# Depuracion
		if (DEBUG):
			logger.info("scrapedtitle="+scrapedtitle)
			logger.info("scrapedurl="+scrapedurl)
			logger.info("scrapedthumbnail="+scrapedthumbnail)

		
			# Añade al listado de XBMC
			xbmctools.addnewvideo( CHANNELNAME , "play" , category , match[2], scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

def close_directory(params,url,category):
	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )

	# Disable sorting...
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )
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
def megasearch(matchtype,data):
	
	if "Temporada" in matchtype[0]:
		patron = 'http\:\/\/www.megavideo.com\/([\?v=|v/|\?d=]+)([A-Z0-9]{8})" target="_blank">([^<]+)<'
	else:
		patron = 'http\:\/\/www.megavideo.com\/([\?v=|v/|\?d=]+)([A-Z0-9]{8}).*?'
	matches = re.compile(patron,re.DOTALL).findall(data)
	devuelve = []
	if len(matches)>0:
		if len(matches)>1:
			if ("s\xc3\xa9ries"or"serie"or"anime"or"desenhos"or"episÃ³dio") in string.lower(matchtype[0]):
				cd = " - Episódio %d "
			else:
				cd = " - (%d) "
		else:
			cd = ""
		c = 0
   
		for match in matches:
			c +=1
			if "v" in match[0]:
				server = "Megavideo"
			elif "d" in match[0]:
				server = "Megaupload"
			if "Temporada" in matchtype[0]:
				if "Assistir" == match[2].strip():
					titulo = " - " +match[2] + cd %c
				else:
					titulo = " - " +match[2]
			else:
				if cd == "":
					titulo = ""
				else:
					titulo = cd %c 
			devuelve.append( [ titulo , match[1] , server ] )
	return devuelve

def advertencia():
	dialog = xbmcgui.Dialog()
	dialog.ok('!Advertencia!','pelisalacarta - Modo Adulto','El video seleccionado es solo para mayores 18 años')
	return
