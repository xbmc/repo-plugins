# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para newdivx.net by Bandavi
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

CHANNELNAME = "newdivx"

# Esto permite su ejecución en modo emulado
try:
	pluginhandle = int( sys.argv[ 1 ] )
except:
	pluginhandle = ""

# Traza el inicio del canal
logger.info("[newdivx.py] init")

DEBUG = True

def mainlist(params,url,category):
	logger.info("[newdivx.py] mainlist")

	# Añade al listado de XBMC
	xbmctools.addnewfolder( CHANNELNAME , "listvideos"       , category , "Ultimas Películas Añadidas"    ,"http://www.newdivx.net/","","")
	xbmctools.addnewfolder( CHANNELNAME , "ListaCat"         , category , "Listado por Categorias"    ,"http://www.newdivx.net/","","")
	xbmctools.addnewfolder( CHANNELNAME , "ListvideosMirror" , category , "Estrenos","http://www.newdivx.net/peliculas-online/estrenos/","","")
	xbmctools.addnewfolder( CHANNELNAME , "ListvideosMirror" , category , "Documentales","http://www.newdivx.net/peliculas-online/documentales/","","")
	xbmctools.addnewfolder( CHANNELNAME , "ListvideosMirror" , category , "Peliculas V.O.S.","http://www.newdivx.net/peliculas-online/peliculas-vos/","","")
	xbmctools.addnewfolder( CHANNELNAME , "search" , category , "Buscar","http://www.newdivx.net/index.php","","")

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )

	# Disable sorting...
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def search(params,url,category):
	logger.info("[newdivx.py] search")

	keyboard = xbmc.Keyboard()
	#keyboard.setDefault('')
	keyboard.doModal()
	if (keyboard.isConfirmed()):
		tecleado = keyboard.getText()
		if len(tecleado)>0:
			#convert to HTML
			tecleado = tecleado.replace(" ", "+")
			searchUrl = "http://www.newdivx.net/index.php?do=search&subaction=search&story="+tecleado
			searchresults(params,searchUrl,category)

def searchresults(params,url,category):
	logger.info("[newdivx.py] SearchResult")
	
	#post = {"do": "search","subaction":"search","story":tecleado}
	# Descarga la página
	data = scrapertools.cachePage(url)
	#print data
	# Extrae las entradas (carpetas)
	patronvideos  = '<td class="copy" valign="top" colspan="2"><a href="([^"]+)" >'
	patronvideos += '<[^>]+><[^>]+><img src="([^"]+)" '
	patronvideos += "alt=.*?title='([^']+)' /></div>"
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
	logger.info("[newdivx.py] ListaCat")
	
	xbmctools.addnewfolder( CHANNELNAME ,"ListvideosMirror", category , "Acción","http://www.newdivx.net/peliculas-online/accion/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"ListvideosMirror", category , "Adolescencia","http://www.newdivx.net/peliculas-online/adolescencia/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"ListvideosMirror", category , "Animación","http://www.newdivx.net/peliculas-online/animacion/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"ListvideosMirror", category , "Aventuras","http://www.newdivx.net/peliculas-online/aventuras/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"ListvideosMirror", category , "Belico","http://www.newdivx.net/peliculas-online/belico/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"ListvideosMirror", category , "Ciencia-Ficción","http://www.newdivx.net/peliculas-online/ciencia-ficcion/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideosMirror", category , "Comedia","http://www.newdivx.net/peliculas-online/comedia/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"ListvideosMirror", category , "Drama","http://www.newdivx.net/peliculas-online/drama/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"ListvideosMirror", category , "Fantastico","http://www.newdivx.net/peliculas-online/fantastico/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"ListvideosMirror", category , "Intriga","http://www.newdivx.net/peliculas-online/intriga/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"ListvideosMirror", category , "Infantil","http://www.newdivx.net/peliculas-online/infantil/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"ListvideosMirror", category , "Musical","http://www.newdivx.net/peliculas-online/musical/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"ListvideosMirror", category , "Romantico","http://www.newdivx.net/peliculas-online/romantico/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"ListvideosMirror", category , "Terror","http://www.newdivx.net/peliculas-online/terror/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"ListvideosMirror", category , "Thriller","http://www.newdivx.net/peliculas-online/thriller/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"ListvideosMirror", category , "Western","http://www.newdivx.net/peliculas-online/western/","","")

	# Asigna el título, desactiva la ordenación, y cierra el directorio
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )
        
def ListvideosMirror(params,url,category):
	logger.info("[newdivx.py] ListvideosMirror")

	# Descarga la página
	data = scrapertools.cachePage(url)
	#logger.info(data)


	# Patron de las entradas
	patronvideos  = '<td class="copy" align="left" valign="top" ><[^>]+><[^>]+><a href="([^"]+)"' # URL
	patronvideos += '></span><[^>]+><[^>]+><img src="([^"]+)" '                                   # TUMBNAIL
	patronvideos += "alt=.*?title='([^']+)' /></div>"                                             # TITULO 
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
	patronvideos  = '</span> <a href="(http://www.newdivx.net/peliculas-online/[^\/]+/page/[^"]+)"'
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
	logger.info("[newdivx.py] listvideos")

	if url=="":
		url = "http://www.newdivx.com/"
                
	# Descarga la página
	data = scrapertools.cachePage(url)
	#logger.info(data)


	# Extrae las entradas (carpetas)
	patronvideos  = '<div class="news"[^>]+><span class="title">[^<]+<a href="([^"]+)"></span><img src="([^"]+)".*?alt="([^"]+)"'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	for match in matches:
		scrapedtitle = match[2]
		scrapedurl = match[0]
		scrapedthumbnail = match[1]
		scrapedplot = ""

		# Depuracion
		if (DEBUG):
			logger.info("scrapedtitle="+scrapedtitle)
			logger.info("scrapedurl="+scrapedurl)
			logger.info("scrapedthumbnail="+scrapedthumbnail)

		
			# Añade al listado de XBMC
			xbmctools.addnewfolder( CHANNELNAME , "detail" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	#Extrae la marca de siguiente página
	patronvideos  = '</span> <a href="(http://www.newdivx.net/videos/page/[^"]+)"'
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
	logger.info("[newdivx.py] detail")

	title = urllib.unquote_plus( params.get("title") )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = urllib.unquote_plus( params.get("plot") )

	# Descarga la página
	data = scrapertools.cachePage(url)
	#logger.info(data)
	patronvideos = '<p class="Estilo2">([^<]+)</p>'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	if len(matches)>0:
		title = matches[0]   
	# ------------------------------------------------------------------------------------
	# Busca los enlaces a los videos en los servidores habilitados
	# ------------------------------------------------------------------------------------
	listavideos = servertools.findvideos(data)

	for video in listavideos:
		if "stagevu.com/embed" not in video[1]:
			videotitle = video[0]
			url = video[1]
			server = video[2]
			xbmctools.addnewvideo( CHANNELNAME , "play" , category , server , title.strip() + " - " + videotitle , url , thumbnail , plot )
	# ------------------------------------------------------------------------------------
        #--- Busca los videos Directos
    ## ------------------------------------------------------------------------------------##
    #               Busca  enlaces en el servidor  przeklej                                 #
    ## ------------------------------------------------------------------------------------## 
        patronvideos = '<param name="src" value="([^"]+)"'
        matches = re.compile(patronvideos,re.DOTALL).findall(data)
        
        if len(matches)>0:
			if len(matches)==1:
				subtitle = "[Divx-Directo-Przeklej]"
				xbmctools.addnewvideo( CHANNELNAME , "play" , category , "Directo" , title + " - "+subtitle, matches[0] , thumbnail , plot )
                 
			else:
				parte = 0
				subtitle = "[Divx-Directo-Przeklej]"
				for match in matches:
					logger.info(" matches = "+match)
					parte = parte + 1
					xbmctools.addnewvideo( CHANNELNAME , "play" , category , "Directo" , title + " - "+subtitle+" "+str(parte), match , thumbnail , plot )
					
   ## --------------------------------------------------------------------------------------##
   #  				 Busca enlaces en el servidor Fishker                                    #
   ## --------------------------------------------------------------------------------------##
	patronvideos = '<a href="(http\:\/\/www.fishker.com\/[^"]+)"'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	if len(matches)>0:
		data2 = scrapertools.cachePage(matches[0])
		#print data2
		#<param name="flashvars" value="comment=Q&amp;m=video&amp;file=http://fish14.st.fishker.com/videos/1249504.flv?c=3948597662&amp;st=/plstyle.txt?video=1"
		patron = 'file=([^"]+)"'
		matches2 = re.compile(patron,re.DOTALL).findall(data2)
		if len(matches2)>0:
			videourl = matches2[0].replace("&amp;","&")
			subtitle = "[FLV-Directo-Fishker]"
			xbmctools.addnewvideo( CHANNELNAME , "play" , category , "Directo" , title + " - "+subtitle, videourl , thumbnail , plot )
			
   ## --------------------------------------------------------------------------------------##
   #  				 Busca enlaces en el servidor Cinshare                                  #
   ## --------------------------------------------------------------------------------------##
	
	patronvideos = '<iframe src="(http://www.cinshare.com/[^"]+)"'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	if len(matches)>0:
		####
		'''
		data2 = scrapertools.cachePage(matches[0])
		#print data2
		
		patron = '<param name="src" value="([^"]+)"'
		matches2 = re.compile(patron,re.DOTALL).findall(data2)
		if len(matches2)>0:
		'''
		####
		import cinshare
		videourl = matches[0]
		subtitle = "[divx-Directo-Cinshare]"
		xbmctools.addnewvideo( CHANNELNAME , "play" , category ,"Cinshare", title + " - "+subtitle, videourl , thumbnail , plot )
			
	## --------------------------------------------------------------------------------------##
	#               Busca enlaces a videos .flv o (.mp4 dentro de un xml)                     #
	## --------------------------------------------------------------------------------------##
	patronvideos = 'file=(http\:\/\/[^\&]+)\&'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	if len(matches)>0:
		subtitle = "[FLV-Directo]"
		if ("xml" in matches[0]):
			data2 = scrapertools.cachePage(matches[0])
			logger.info("data2="+data2)
			patronvideos  = '<track>.*?'
			patronvideos += '<title>([^<]+)</title>(?:[^<]+'
			patronvideos += '<annotation>([^<]+)</annotation>[^<]+|[^<]+)'
			patronvideos += '<location>([^<]+)</location>[^<]+'
			patronvideos += '</track>'
			matches = re.compile(patronvideos,re.DOTALL).findall(data2)
			scrapertools.printMatches(matches)

			for match in matches:
				if ".mp4" in match[2]:
					subtitle = "[MP4-Directo]"
				scrapedtitle = '%s (%s) - %s  %s' %(title,match[1].strip(),match[0],subtitle)
				scrapedurl = match[2].strip()
				scrapedthumbnail = thumbnail
				scrapedplot = plot
				if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

				# Añade al listado de XBMC
				xbmctools.addnewvideo( CHANNELNAME , "play" , category , "Directo" , scrapedtitle, scrapedurl , scrapedthumbnail, scrapedplot )
		else:
			
			xbmctools.addnewvideo( CHANNELNAME , "play" , category , "Directo" , title + " - "+subtitle, matches[0] , thumbnail , plot )
			
	## --------------------------------------------------------------------------------------##
	#            Busca enlaces a video en el servidor Dailymotion                             #
	## --------------------------------------------------------------------------------------##
	patronvideos = '<param name="movie" value="http://www.dailymotion.com/swf/video/([^\_]+)\_[^"]+"'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	playWithSubt = "play"
	if len(matches)>0:
		daily = 'http://www.dailymotion.com/video/%s'%matches[0]
		data2 = scrapertools.cachePage(daily)
		
		# Busca los subtitulos en español 
		subtitulo = re.compile('%22es%22%3A%22(.+?)%22').findall(data2)
		subtit = urllib.unquote(subtitulo[0])
		subtit = subtit.replace("\/","/")
		#subt_ok = downloadstr(subtit,title)
		#print "subtitulo subt_ok = %s" % str(subt_ok)
				
		# Busca el enlace al video con formato FLV 	
		Lowres=re.compile('%22sdURL%22%3A%22(.+?)%22').findall(data2)
		if len(Lowres)>0:
			videourl = urllib.unquote(Lowres[0])
			videourl = videourl.replace("\/","/")
			if len(subtit)>0:
				videourl = videourl + "|" + subtit
				playWithSubt = "play2"
			subtitle = "[FLV-Directo-Dailymotion]"
			xbmctools.addnewvideo( CHANNELNAME , playWithSubt , category , "Directo" , title + " - "+subtitle, videourl , thumbnail , plot )
		
		# Busca el enlace al video con formato HQ (H264)		
		Highres=re.compile('%22hqURL%22%3A%22(.+?)%22').findall(data2)
		if len(Highres)>0:
			videourl = urllib.unquote(Highres[0])
			videourl = videourl.replace("\/","/")
			if len(subtit)>0:
				videourl = videourl + "|" + subtit
				playWithSubt = "play2"			
			subtitle = "[h264-Directo-Dailymotion-este video no es soportado en versiones antiguas o xbox plataforma]"
			xbmctools.addnewvideo( CHANNELNAME , playWithSubt , category , "Directo" , title + " - "+subtitle, videourl , thumbnail , plot )
	## --------------------------------------------------------------------------------------##
	#            Busca enlaces a video en el servidor Gigabyteupload.com                      #
	## --------------------------------------------------------------------------------------##

	patronvideos = '<a href="(http://www.gigabyteupload.com/[^"]+)"'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	if len(matches)>0:
		print " encontro: %s" %matches[0]
		import gigabyteupload as giga
		videourl = giga.geturl(matches[0])
		if len(videourl)>0:
			subtitle = "[Divx-Directo-Gigabyteupload]"
			xbmctools.addnewvideo( CHANNELNAME , "play" , category , "Directo" , title + " - "+subtitle, videourl , thumbnail , plot )
	## --------------------------------------------------------------------------------------##
	#            Busca enlaces de videos para el servidor vk.com                             #
	## --------------------------------------------------------------------------------------##
	'''
	var video_host = 'http://cs12644.vk.com/';
	var video_uid = '87155741';
	var video_vtag = 'fc697084d3';
	var video_no_flv = 1;
	var video_max_hd = '1'
	'''
	patronvideos = '<iframe src="(http://vk.com/video_ext.php[^"]+)"'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	if len(matches)>0:
		print " encontro VK.COM :%s" %matches[0]
 		
		data2 = scrapertools.cachePage(matches[0])
		print data2
		patron  = "var video_host = '([^']+)'.*?"
		patron += "var video_uid = '([^']+)'.*?"
		patron += "var video_vtag = '([^']+)'.*?"
		patron += "var video_no_flv = ([^;]+);.*?"
		patron += "var video_max_hd = '([^']+)'"
		matches2 = re.compile(patron,re.DOTALL).findall(data2)
		if len(matches2)>0:    #http://cs12387.vk.com/u87155741/video/fe5ee11ddb.360.mp4
			for match in matches2:
				if match[3].strip() == "0":
					tipo = "flv"
					videourl = "%s/u%s/video/%s.%s" % (match[0],match[1],match[2],tipo)
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
	logger.info("[newdivx.py] play")
	strmplay = False
	title = unicode( xbmc.getInfoLabel( "ListItem.Title" ), "utf-8" )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = unicode( xbmc.getInfoLabel( "ListItem.Plot" ), "utf-8" )
	server = params["server"]
	
	xbmctools.playvideo(CHANNELNAME,server,url,category,title,thumbnail,plot)

def play2(params,url,category):
	logger.info("[newdivx.py] play")
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
	ok = downloadtools.downloadfile(urlsub,fullpath)
	#xbmc.setSubtitles(fullpath)
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
def geturl(url):
	
	try:
		response = urllib.urlopen(url)
		trulink = response.geturl()
		return truelink
	except:
		return ""
