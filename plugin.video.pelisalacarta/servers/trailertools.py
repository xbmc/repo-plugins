# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Buscador de Trailers en youtube
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------

import urlparse,urllib2,urllib,re
import os.path
import sys
import xbmc
import scrapertools
import string
import xbmcgui
import xbmcplugin
import xbmctools
import gdata.youtube
import gdata.youtube.service
import youtube
import config

CHANNELNAME = "trailertools"
# Esto permite su ejecución en modo emulado
try:
	pluginhandle = int( sys.argv[ 1 ] )
except:
	pluginhandle = ""

DEBUG = True
IMAGES_PATH = xbmc.translatePath( os.path.join( os.getcwd(), 'resources' , 'images'  ) )
def mainlist(params,url,category):
	xbmc.output("[trailertools.py] mainlist")
	titulo = ""
	listavideos = GetTrailerbyKeyboard(titulo,category)
	if len(listavideos)>0:
		for video in listavideos:
			titulo = video[1]
			url        = video[0]
			thumbnail  = video[2]
			xbmctools.addnewvideo( "trailertools" , "youtubeplay" , category , "Directo" ,  titulo , url , thumbnail , "Ver Video" )
			
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )		
	
def buscartrailer(params,url,category):
	print "[trailertools.py] Modulo: buscartrailer()"
	thumbnail = ""
	videotitle = title = urllib.unquote_plus( params.get("title") ).strip()
	if config.getLocalizedString(30110) in videotitle: #"Buscar tailer para"
		videotitle = videotitle.replace(config.getLocalizedString(30110),"").strip()
	if config.getLocalizedString(30111) in videotitle: #"Insatisfecho?, busca otra vez : "
		videotitle = videotitle.replace(config.getLocalizedString(30111),"").strip()
	
		listavideos = GetTrailerbyKeyboard(videotitle.strip(),category)
	else:
		listavideos = gettrailer(videotitle.strip().strip(),category)
	if len(listavideos)>0:
		for video in listavideos:
			titulo = video[1]
			url        = video[0]
			thumbnail  = video[2]
			xbmctools.addnewvideo( "trailertools" , "youtubeplay" , category , "Directo" ,  titulo , url , thumbnail , "Ver Video" )
	
	xbmctools.addnewfolder( CHANNELNAME , "buscartrailer" , category , config.getLocalizedString(30111)+" "+videotitle , url , os.path.join(IMAGES_PATH, 'trailertools.png'), "" ) #"Insatisfecho?, busca otra vez : "		
	# Propiedades
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )
	
	
def GetFrom_Trailersdepeliculas(titulovideo):
    print "[trailertools.py] Modulo: GetFrom_Trailersdepeliculas(titulo = %s)"  % titulovideo
    devuelve = []
    
    
    titulo = LimpiarTitulo(titulovideo)
    # ---------------------------------------
    #  Busca el video en la pagina de www.trailerdepeliculas.org,
    #  la busqueda en esta pagina es porque a veces tiene los
    #  trailers en ingles y que no existen en español
    # ----------------------------------------
    c = 0
    url1 ="http://www.trailersdepeliculas.org/"
    url  ="http://www.trailersdepeliculas.org/buscar.html"
    urldata=getpost(url,{'busqueda': titulo})
    #xbmc.output("post url  :  "+urldata)
    patronvideos = "<td><h2><a href='([^']+)'>(.*?)<.*?src='([^']+)'.*?"
    matches  = re.compile(patronvideos,re.DOTALL).findall(urldata)
    if len(matches)>0:
		patronvideos = 'movie" value="http://www.youtube.com([^"]+)"'
		for match in matches:
			xbmc.output("Trailers encontrados en www.trailerdepeliculas.org :  "+match[1])
			if titulo in (string.lower(LimpiarTitulo(match[1]))):
				urlpage = urlparse.urljoin(url1,match[0])
				thumbnail = urlparse.urljoin(url1,match[2])
				data     = scrapertools.cachePage(urlpage)
				xbmc.output("Trailer elegido :  "+match[1])
				matches2 = re.compile(patronvideos,re.DOTALL).findall(data)
				for match2 in matches2:
					xbmc.output("link yt del Trailer encontrado :  "+match2)
					c=c+1
					devuelve.append( [match2, match[1] , thumbnail] )
					#scrapedthumbnail = match[2]
					#scrapedtitle     = match[1]
					#scrapedurl       = match[0]
			
			
		xbmc.output(" lista de links encontrados U "+str(len(match)))
    print '%s Trailers encontrados en Modulo: GetFrom_Trailersdepeliculas()' % str(c)
    return devuelve
def GetFromYoutubePlaylist(titulovideo):
	print "[trailertools.py] Modulo: GetFromYoutubePlaylist(titulo = %s)"  % titulovideo
	devuelve = []	
    #
    # ---------------------------------------
    #  Busca el video en las listas de youtube
    # ---------------------------------------
	c = 0
    #http://www.youtube.com/results?search_type=search_playlists&search_query=luna+nueva+trailer&uni=1
	for i in ["+trailer+espa%C3%B1ol","+trailer"]:
		listyoutubeurl  = "http://www.youtube.com/results?search_type=search_playlists&search_query="
		listyoutubeurl += titulovideo.replace(" ","+")+i+"&uni=1"
		listyoutubeurl = listyoutubeurl.replace(" ","")
		xbmc.output("Youtube url parametros de busqueda  :"+listyoutubeurl)
		data = scrapertools.cachePage(listyoutubeurl)

		thumbnail=""
		patronyoutube  = '<span><a class="hLink" title="(.*?)" href="(.*?)">.*?'
		#patronyoutube += '<span class="playlist-video-duration">(.*?)</span>'
		matches  = re.compile(patronyoutube,re.DOTALL).findall(data)
		if len(matches)>0:
			for match in matches:
				xbmc.output("Trailer Titulo encontrado :"+match[0])
				xbmc.output("Trailer Url    encontrado :"+match[1])
				xbmc.output("Trailer Titulo Recortado  :"+string.lower(LimpiarTitulo(match[0])))
				if (titulovideo) in (string.lower(LimpiarTitulo(match[0]))):
					campo = match[1]
					longitud = len(campo)
					campo = campo[-11:]
					xbmc.output("codigo del video :  "+campo)
					scrapedurl = "http://www.youtube.com/watch?v="+campo
					patron    = "(http\:\/\/i[^/]+/vi/"+campo+"/default.jpg)"
					matches2  = re.compile(patron,re.DOTALL).findall(data)
					if len(matches2)>0:
						thumbnail = matches2[0]
					c = c + 1
					xbmc.output("Trailer elegido :  "+match[1])
					devuelve.append( [scrapedurl, match[0] , thumbnail] )
					#scrapedthumbnail = thumbnail
					#scrapedtitle     = match[0]
					#scrapedurl       = match[1]
					if c == 6 :
						break
			#xbmc.output(" Total de links encontrados U "+str(len(match)))
		if c == 6:break
	print '%s Trailers encontrados en Modulo: GetFromYoutubePlaylist()' % str(c)
	return devuelve
def gettrailer(titulovideo,category):
	print "[trailertools.py] Modulo: gettrailer(titulo = %s , category = %s)"  % (titulovideo,category)
	titulo = re.sub('\([^\)]+\)','',titulovideo)
	titulo = title = re.sub('\[[^\]]+\]','',titulo)

	sopa_palabras_invalidas = ("dvdrip" ,  "dvdscreener2" ,"tsscreener" , "latino" ,     # Esto es para peliculasyonkis o parecidos
							   "dvdrip1",  "dvdscreener"  ,"tsscreener1", "latino1",
							   "latino2",  "dvdscreener1" ,"screener"    ,
							   "mirror" ,  "megavideo"    ,"vose"    	, "subtitulada"
							   )
							   
	titulo = LimpiarTitulo(titulo)
	print "el tituloooo es :%s" %titulo
	trozeado = titulo.split()
	for trozo in trozeado:
		if trozo in sopa_palabras_invalidas:
			titulo = titulo.replace(trozo ,"")
	titulo = re.sub(' $','',titulo)
	titulo = titulo.replace("ver pelicula online vos","").strip()
	titulo = titulo.replace("ver pelicula online","").strip()
	titulo = titulo.replace("mirror 1","").strip()
	titulo = titulo.replace("parte 1","").strip()
	titulo = titulo.replace("part 1","").strip()
	titulo = titulo.replace("pt 1","").strip()		
	titulo = titulo.replace("peliculas online","").strip()
	encontrados = []
	if len(titulo)==0:
		titulo = "El_video_no_tiene_titulo"

	encontrados = GetFrom_Trailersdepeliculas(titulo)      # Primero busca en www.trailerdepeliculas.org
	encontrados  = encontrados + GetVideoFeed(titulo)      # luego busca con el API de youtube 
	if len(encontrados)>0:						           # si encuentra algo, termina
		return encontrados
	else:
		encontrados = GetFromYoutubePlaylist(titulo)       # si no encuentra, busca en las listas de la web de youtube
		if len(encontrados)>0:
			return encontrados
		else:
			respuesta = alertnoencontrado(titulo)          # si aun no encuentra,lanza mensaje de alerta y pregunta si quiere 
			if respuesta:                                  # buscar, modificando el titulo, con el teclado 
				encontrados = GetTrailerbyKeyboard(titulo,category) # si respuesta es afirmativa este entrara en un bucle 
				if len(encontrados)>0:					   # de autollamadas hasta encontrar el trailer o la respuesta 
					return encontrados		               # del mensaje alerta sea negativo.
				else:return []
			else:
				xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
				xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
				xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )
	
	return encontrados
def GetTrailerbyKeyboard(titulo,category):
	print "[trailertools.py] Modulo: GetTrailerbyKeyboard(titulo = %s , category = %s)"  % (titulo,category)
	devuelve = []
	keyboard = xbmc.Keyboard('default','heading')
	keyboard.setDefault(titulo)
	if titulo == "":
		keyboard.setHeading(config.getLocalizedString(30112)) #"Introduce el Titulo a buscar"
	else:
		keyboard.setHeading(config.getLocalizedString(30113)) #'Puedes recortar el titulo ó bien cambiar a otro idioma'
	keyboard.doModal()
	if (keyboard.isConfirmed()):
		tecleado = keyboard.getText()
		if len(tecleado)>0:
			devuelve = gettrailer(tecleado,category)
			return devuelve
		else:return []
	else:return []	
def alertnoencontrado(titulo):
	advertencia = xbmcgui.Dialog()
	#'Trailer no encontrado'
	#'El Trailer para "%s"'
	#'no se ha podido localizar.'
	#'¿Deseas seguir buscando con el teclado?'
	tituloq = '"'+titulo+'"'
	resultado = advertencia.yesno(config.getLocalizedString(30114), config.getLocalizedString(30115) % tituloq, config.getLocalizedString(30116),config.getLocalizedString(30117))
	return(resultado)
def LimpiarTitulo(title):
        title = string.lower(title)
        #title = re.sub('\([^\)]+\)','',title)
        title = re.sub(' $','',title)
        title = title.replace("Ã‚Â", "")
        title = title.replace("ÃƒÂ©","e")
        title = title.replace("ÃƒÂ¡","a")
        title = title.replace("ÃƒÂ³","o")
        title = title.replace("ÃƒÂº","u")
        title = title.replace("ÃƒÂ­","i")
        title = title.replace("ÃƒÂ±","ñ")
        title = title.replace("Ã¢â‚¬Â", "")
        title = title.replace("Ã¢â‚¬Å“Ã‚Â", "")
        title = title.replace("Ã¢â‚¬Å“","")
        title = title.replace("Ã©","e")
        title = title.replace("Ã¡","a")
        title = title.replace("Ã³","o")
        title = title.replace("Ãº","u")
        title = title.replace("Ã­","i")
        title = title.replace("Ã±","ñ")
        title = title.replace("Ãƒâ€œ","O")
        title = title.replace("@","")
        title = title.replace("é","e")
        title = title.replace("á","a")
        title = title.replace("ó","o")
        title = title.replace("ú","u")
        title = title.replace("í","i")
        title = title.replace('ñ','n')
        title = title.replace('Á','a')
        title = title.replace('É','e')
        title = title.replace('Í','i')
        title = title.replace('Ó','o')
        title = title.replace('Ú','u')
        title = title.replace('Ñ','n')
        title = title.replace(":"," ")
        title = title.replace("&","")
        title = title.replace('#','')
        title = title.replace('-','')
        title = title.replace('?','')
        title = title.replace('¿','')
        title = title.replace(",","")
        title = title.replace("*","")
        title = title.replace("\\","")
        title = title.replace("/","")
        title = title.replace("'","")
        title = title.replace('"','')
        title = title.replace("<","")
        title = title.replace(">","")
        title = title.replace(".","")
        title = title.replace("_"," ")
        title = title.replace("\("," ")
        title = title.replace("\)"," ")
        title = title.replace('|','')
        title = title.replace('!','')
        title = title.replace('¡','')
        title = title.replace("  "," ")
        title = title.replace("\Z  ","")
        return(title)

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
####################################################################################################
# Buscador de Trailer : mediante el servicio de Apis de Google y Youtube                           #
####################################################################################################
		
def GetVideoFeed(titulo):
	print "[trailertools.py] Modulo: GetVideoFeed(titulo = %s)"  % titulo
	devuelve = []
	encontrados = set()
	c = 0
	yt = gdata.youtube.service.YouTubeService()
	query = gdata.youtube.service.YouTubeVideoQuery()
	query.vq = titulo+" trailer espanol"
	print query.vq
	query.orderby = 'viewCount'
	query.racy = 'include'
	#query.client = 'ytapi-youtube-search'
	#query.alt = 'rss'
	#query.v = '2'
	feed = yt.YouTubeQuery(query)
	
	
	for entry in feed.entry:
		print 'Video title: %s' % entry.media.title.text
		titulo2 = str(entry.media.title.text)
		url = entry.media.player.url
		duracion = int(entry.media.duration.seconds)
		duracion = " (%02d:%02d)" % ( int( duracion / 60 ), duracion % 60, )
		if titulo in (string.lower(LimpiarTitulo(titulo2))): 
			for thumbnail in entry.media.thumbnail:
				url_thumb = thumbnail.url
			if url not in encontrados:
				devuelve.append([url,titulo2+duracion,url_thumb])
				encontrados.add(url)
				c = c + 1
			if c > 10:
				return (devuelve)
	if c < 6:
		query.vq =titulo+" trailer"
		feed = yt.YouTubeQuery(query)
		for entry in feed.entry:
			print 'Video title: %s' % entry.media.title.text
			titulo2 = str(entry.media.title.text)
			url = entry.media.player.url
			duracion = int(entry.media.duration.seconds)
			duracion = " (%02d:%02d)" % ( int( duracion / 60 ), duracion % 60, )
			if titulo in (string.lower(LimpiarTitulo(titulo2))):
				for thumbnail in entry.media.thumbnail:
					url_thumb = thumbnail.url
				
				if url not in encontrados:
					devuelve.append([url,titulo2+duracion,url_thumb])
					encontrados.add(url)
					c = c + 1
				if c > 10:
					return (devuelve)
	if c < 6:
		query.vq =titulo
		feed = yt.YouTubeQuery(query)
		for entry in feed.entry:
			print 'Video title: %s' % entry.media.title.text
			titulo2 = str(entry.media.title.text)
			url = entry.media.player.url
			duracion = int(entry.media.duration.seconds)
			duracion = " (%02d:%02d)" % ( int( duracion / 60 ), duracion % 60, )
			if titulo in (string.lower(LimpiarTitulo(titulo2))):
				for thumbnail in entry.media.thumbnail:
					url_thumb = thumbnail.url
				
				if url not in encontrados:
					devuelve.append([url,titulo2+duracion,url_thumb])
					encontrados.add(url)
					c = c + 1
				if c > 10:
					return (devuelve)



	print '%s Trailers encontrados en Modulo: GetVideoFeed()' % str(c)
	return (devuelve)
	
def youtubeplay(params,url,category):
	xbmc.output("[trailertools.py] youtubeplay")
	#http://www.youtube.com/watch?v=byvXidWNf2A&feature=youtube_gdata
	title = urllib.unquote_plus( params.get("title") )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = "Ver Video"
	server = "Directo"
	id = youtube.Extract_id(url)
	videourl = youtube.geturl(id)
	if len(videourl)>0:
		xbmc.output("link directo de youtube : "+videourl)
		xbmctools.playvideo("Trailer",server,videourl,category,title,thumbnail,plot)
	elif videourl is None:
		alertaerror()
		return
	else:
		return ""
	
def alertaerror():
	ventana = xbmcgui.Dialog()
	ok= ventana.ok ("Plugin Pelisalacarta", "Uuppss...la calidad elegida en configuracion",'no esta disponible o es muy baja',"elijá otra calidad distinta y vuelva a probar")
'''
	# Abre el diálogo de selección
	opciones = []
	opciones.append("(FLV) Baja calidad")
	opciones.append("(MP4) Alta calidad")
	dia = xbmcgui.Dialog()
	seleccion = dia.select("tiene 2 formatos elige uno", opciones)
	xbmc.output("seleccion=%d" % seleccion)
	if seleccion==-1:
		return("")
	if seleccion == 0:
		videourl,videoinfo = youtube.GetYoutubeVideoInfo(id)
	else:



def youtubeplay(params,url,category):
        xbmc.output("[trailertools.py] youtubeplay")

	title = urllib.unquote_plus( params.get("title") )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = "Ver Video"
	server = "Directo"
	if "www.youtube" in url:
		youtubeurlcatch  = 'http://www.flashvideodownloader.org/download.php?u='+url
	else:
		youtubeurlcatch  = 'http://www.flashvideodownloader.org/download.php?u=http://www.youtube.com'+url
        data2 = scrapertools.cachePage(youtubeurlcatch)
        patronlinkdirecto = '<div class="mod_download"><a href="([^"]+)"'
        linkdirectoyoutube = re.compile(patronlinkdirecto,re.DOTALL).findall(data2)
        if len(linkdirectoyoutube)>0:
               xbmc.output(" link directos encontrados  "+str(len(linkdirectoyoutube)))
               if len(linkdirectoyoutube)>1:

                  # Abre el diálogo de selección
                  opciones = []
	          opciones.append("FLV")
	          opciones.append("MP4")
               
	          dia = xbmcgui.Dialog()
	          seleccion = dia.select("tiene 2 formatos elige uno", opciones)
	          xbmc.output("seleccion=%d" % seleccion)        
                  if seleccion==-1:
	             return("")
	       
                  youtubeurl = linkdirectoyoutube[seleccion]
               else:
                  youtubeurl = linkdirectoyoutube[0]   
            
               xbmc.output("link directo de youtube : "+youtubeurl) 


               xbmctools.playvideo("Trailer",server,youtubeurl,category,title,thumbnail,plot)
               


  yt_service = gdata.youtube.service.YouTubeService()
  query = gdata.youtube.service.YouTubeVideoQuery()
  query.vq = search_terms
  query.orderby = 'viewCount'
  query.racy = 'include'
  feed = yt_service.YouTubeQuery(query)
  PrintVideoFeed(feed)
	
  print 'Video title: %s' % entry.media.title.text
  print 'Video published on: %s ' % entry.published.text
  print 'Video description: %s' % entry.media.description.text
  print 'Video category: %s' % entry.media.category[0].text
  print 'Video tags: %s' % entry.media.keywords.text
  print 'Video watch page: %s' % entry.media.player.url
  print 'Video flash player URL: %s' % entry.GetSwfUrl()
  print 'Video duration: %s' % entry.media.duration.seconds

  # non entry.media attributes
  print 'Video geo location: %s' % entry.geo.location()
  print 'Video view count: %s' % entry.statistics.view_count
  print 'Video rating: %s' % entry.rating.average

  # show alternate formats
  for alternate_format in entry.media.content:
    if 'isDefault' not in alternate_format.extension_attributes:
      print 'Alternate format: %s | url: %s ' % (alternate_format.type,
                                                 alternate_format.url)

  # show thumbnails
  for thumbnail in entry.media.thumbnail:
    print 'Thumbnail url: %s' % thumbnail.url
'''
