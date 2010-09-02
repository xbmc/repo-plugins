# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para peliculasyonkis
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
import DecryptYonkis as Yonkis
import config
import logger
import buscador

CHANNELNAME = "peliculasyonkis"
SERVER = {'pymeno2'   :'Megavideo' ,'pymeno3':'Megavideo','pymeno4':'Megavideo','pymeno5':'Megavideo','pymeno6':'Megavideo',
		  'svueno'    :'Stagevu'   ,
		  'manueno'   :'Movshare'  ,
		  'videoweed' :'Videoweed' ,
		  'veoh2'     :'Veoh'      ,
		  'megaupload':'Megaupload',
		  'pfflano'   :'Directo'   ,
		  }
CALIDAD = {'f-1':u'\u2776','f-2':u'\u2777','f-3':u'\u2778','f-4':u'\u0002\u2779\u0002','f-5':u'\u277A'}

# Esto permite su ejecución en modo emulado
try:
	pluginhandle = int( sys.argv[ 1 ] )
except:
	pluginhandle = ""

# Traza el inicio del canal
logger.info("[peliculasyonkis.py] init")

DEBUG = True

def mainlist(params,url,category):
	logger.info("[peliculasyonkis.py] mainlist")
	
	activar = config.getSetting("activar")
	print "activado como :%s" %activar
	if activar == "":
		activar = "false"
		config.setSetting("activar",activar)
	if activar == "false":
		flecha = "+"
	else:
		flecha = "-"
	# Añade al listado de XBMC
	
	xbmctools.addnewfolder( CHANNELNAME , "listnovedades"  , category , "Estrenos de cartelera" ,"http://www.peliculasyonkis.com/ultimas-peliculas/cartelera/","","")
	xbmctools.addnewfolder( CHANNELNAME , "listnovedades"  , category , "Estrenos de DVD" ,"http://www.peliculasyonkis.com/ultimas-peliculas/estrenos-dvd/","","")
	xbmctools.addnewfolder( CHANNELNAME , "listnovedades"  , category , "Ultimas Peliculas Actualizadas","http://www.peliculasyonkis.com/ultimas-peliculas/actualizadas/","","")
	xbmctools.addnewfolder( CHANNELNAME , "listnovedades"  , category , "Ultimas peliculas añadidas a la web","http://www.peliculasyonkis.com/ultimas-peliculas/estrenos-web/","","")
	xbmctools.addnewfolder( CHANNELNAME , "listcategorias" , category , "Listado por categorias","http://www.peliculasyonkis.com/","","")
	xbmctools.addnewfolder( CHANNELNAME , "listalfabetico" , category , "Listado alfabético","http://www.peliculasyonkis.com/","","")
	xbmctools.addnewfolder( CHANNELNAME , "buscaporanyo"   , category , "Busqueda por Año","http://www.peliculasyonkis.com/","","")
	xbmctools.addnewfolder( CHANNELNAME , "search"         , category , "Buscar","","","")

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )

	# Disable sorting...
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def search(params,url,category):
	logger.info("[peliculasyonkis.py] search")
	
	buscador.listar_busquedas(params,url,category)
	

def performsearch(texto):
	
	logger.info("[peliculasyonkis.py] performsearch")
	url = "http://www.peliculasyonkis.com/buscarPelicula.php?s="+texto
	
	# Descarga la página
	data = scrapertools.cachePage(url)

	# Extrae las entradas (carpetas)
	patronvideos  = '<li> <a href="([^"]+)" title="([^"]+)"><img.*?src="([^"]+)"'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)
	
	resultados = []

	for match in matches:
		# Atributos
		scrapedtitle = match[1]
		scrapedurl = match[0]
		scrapedthumbnail = match[2]
		scrapedplot = ""
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		resultados.append( [CHANNELNAME , "detailfolder" , "buscador" , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot ] )
		
	return resultados

def searchresults(params,Url,category):
	logger.info("[peliculasyonkis.py] searchresults")
	
	buscador.salvar_busquedas(params,Url,category)
	
	url = "http://www.peliculasyonkis.com/buscarPelicula.php?s="+Url.replace(" ", "+")
	
	# Descarga la página
	data = scrapertools.cachePage(url)
	#logger.info(data)

	# Extrae las entradas (carpetas)
	#<li> <a href="http://www.peliculasyonkis.com/pelicula/las-edades-de-lulu-1990/" title="Las edades de Lulú (1990)"><img width="77" height="110" src="http://images.peliculasyonkis.com/thumbs/las-edades-de-lulu-1990.jpg" alt="Las edades de Lulú (1990)" align="right" />
	
	patronvideos  = '<li> <a href="([^"]+)" title="([^"]+)"><img.*?src="([^"]+)"'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	for match in matches:
		scrapedtitle = match[1]
		scrapedurl = match[0]
		scrapedthumbnail = match[2]
		scrapedplot = ""
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")
		xbmctools.addnewvideo( CHANNELNAME , "detail" , category , "Megavideo" , scrapedtitle , scrapedurl , scrapedthumbnail , scrapedplot )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )

	# Disable sorting...
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def listalfabetico(params, url, category):

	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "0-9","http://www.peliculasyonkis.com/lista-peliculas/listaPeliculasNumeric.php","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "A","http://www.peliculasyonkis.com/lista-peliculas/listaPeliculasA.php","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "B","http://www.peliculasyonkis.com/lista-peliculas/listaPeliculasB.php","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "C","http://www.peliculasyonkis.com/lista-peliculas/listaPeliculasC.php","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "D","http://www.peliculasyonkis.com/lista-peliculas/listaPeliculasD.php","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "E","http://www.peliculasyonkis.com/lista-peliculas/listaPeliculasE.php","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "F","http://www.peliculasyonkis.com/lista-peliculas/listaPeliculasF.php","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "G","http://www.peliculasyonkis.com/lista-peliculas/listaPeliculasG.php","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "H","http://www.peliculasyonkis.com/lista-peliculas/listaPeliculasH.php","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "I","http://www.peliculasyonkis.com/lista-peliculas/listaPeliculasI.php","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "J","http://www.peliculasyonkis.com/lista-peliculas/listaPeliculasJ.php","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "K","http://www.peliculasyonkis.com/lista-peliculas/listaPeliculasK.php","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "L","http://www.peliculasyonkis.com/lista-peliculas/listaPeliculasL.php","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "M","http://www.peliculasyonkis.com/lista-peliculas/listaPeliculasM.php","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "N","http://www.peliculasyonkis.com/lista-peliculas/listaPeliculasN.php","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "O","http://www.peliculasyonkis.com/lista-peliculas/listaPeliculasO.php","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "P","http://www.peliculasyonkis.com/lista-peliculas/listaPeliculasP.php","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "Q","http://www.peliculasyonkis.com/lista-peliculas/listaPeliculasQ.php","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "R","http://www.peliculasyonkis.com/lista-peliculas/listaPeliculasR.php","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "S","http://www.peliculasyonkis.com/lista-peliculas/listaPeliculasS.php","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "T","http://www.peliculasyonkis.com/lista-peliculas/listaPeliculasT.php","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "U","http://www.peliculasyonkis.com/lista-peliculas/listaPeliculasU.php","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "V","http://www.peliculasyonkis.com/lista-peliculas/listaPeliculasV.php","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "W","http://www.peliculasyonkis.com/lista-peliculas/listaPeliculasW.php","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "X","http://www.peliculasyonkis.com/lista-peliculas/listaPeliculasX.php","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "Y","http://www.peliculasyonkis.com/lista-peliculas/listaPeliculasY.php","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listvideos", category , "Z","http://www.peliculasyonkis.com/lista-peliculas/listaPeliculasZ.php","","")

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )

	# Disable sorting...
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def listnovedades(params,url,category):
	logger.info("[peliculasyonkis.py] listnovedades")

	# Descarga la página
	data = scrapertools.cachePage(url)
	#logger.info(data)

	# Extrae las entradas (carpetas)
	patronvideos  = '<td align=\'center\'><center><span style=\'font-size: 0.7em\'><a href="([^"]+)" title="([^"]+)">'
	patronvideos += '<img.*?src=\'([^\']+)\'[^>]+>.*?<img src="(http://simages.peliculasyonkis.com/images/[^"]+)"'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	for match in matches:
		# Titulo
		try:
			scrapedtitle = unicode( match[1], "utf-8" ).encode("iso-8859-1")
		except:
			scrapedtitle = match[1]

		# URL
		scrapedurl = match[0]
		
		# Thumbnail
		scrapedthumbnail = match[2]
		
		# procesa el resto
		scrapedplot = ""

		# Depuracion
		if (DEBUG):
			logger.info("scrapedtitle="+scrapedtitle)
			logger.info("scrapedurl="+scrapedurl)
			logger.info("scrapedthumbnail="+scrapedthumbnail)

		# Añade al listado de XBMC
		xbmctools.addnewvideo( CHANNELNAME , "detail" , category , "Megavideo" , scrapedtitle , scrapedurl , scrapedthumbnail , scrapedplot )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )

	# Disable sorting...
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def listcategorias(params,url,category):
	logger.info("[peliculasyonkis.py] listcategorias")

	# Descarga la página
	data = scrapertools.cachePage(url)
	#logger.info(data)

	# Extrae las entradas (carpetas)
	patronvideos  = '<li class="page_item"><a href="(http\://www.peliculasyonkis.com/genero/[^"]+)"[^>]+>([^<]+)</a></li>'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	for match in matches:
		# Titulo
		try:
			scrapedtitle = unicode( match[1], "utf-8" ).encode("iso-8859-1")
		except:
			scrapedtitle = match[1]

		# URL
		scrapedurl = match[0]
		
		# Thumbnail
		scrapedthumbnail = match[0]
		
		# procesa el resto
		scrapedplot = ""

		# Depuracion
		if (DEBUG):
			logger.info("scrapedtitle="+scrapedtitle)
			logger.info("scrapedurl="+scrapedurl)
			logger.info("scrapedthumbnail="+scrapedthumbnail)

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , scrapedtitle , scrapedurl , scrapedthumbnail , scrapedplot )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )

	# Disable sorting...
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def buscaporanyo(params,url,category):
	logger.info("[peliculasyonkis.py] buscaporanyo")
	anho=2010
	anyoactual = anho
	anyoinic   = 1920
	opciones = []
	for i in range(anyoactual-anyoinic+1):
		opciones.append(str(anyoactual))
		anyoactual = anyoactual - 1           
	dia = xbmcgui.Dialog()
	seleccion = dia.select("Listar desde el Año: ", opciones)
	logger.info("seleccion=%d" % seleccion)
	if seleccion == -1 :return
	if seleccion == 0:
		url = "http://www.peliculasyonkis.com/estreno/"+opciones[seleccion]+"/"+opciones[seleccion]+"/0/"
		listvideos(params,url,category)
		return
	if seleccion>30:
		anyoactual = anho + 30 - seleccion
		rangonuevo = 31
	else:
		anyoactual = anho
		rangonuevo = seleccion + 1
	desde      = opciones[seleccion]
	
	opciones2 = []
	for j in range(rangonuevo):
		opciones2.append(str(anyoactual))
		anyoactual = anyoactual - 1
	dia2 = xbmcgui.Dialog()
	seleccion2 = dia2.select("Listar hasta el año:",opciones2)
	if seleccion == -1 :
		url = "http://www.peliculasyonkis.com/estreno/"+desde+"/"+desde+"/0/"
		listvideos(params,url,category)
		return
	url = "http://www.peliculasyonkis.com/estreno/"+desde+"/"+opciones2[seleccion2]+"/0/"
	listvideos(params,url,category)
	return

def listvideos(params,url,category):
	logger.info("[peliculasyonkis.py] listvideos")

	# Descarga la página
	data = scrapertools.cachePage(url)
	#logger.info(data)

	# Extrae las entradas (carpetas)
	patronvideos  = "<a href='([^']+)'>Siguiente &gt;&gt;</a>"
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	for match in matches:
		# Titulo
		scrapedtitle = "#Siguiente"

		# URL
		scrapedurl = match
		
		# Thumbnail
		scrapedthumbnail = ""
		
		# procesa el resto
		scrapedplot = ""

		# Depuracion
		if (DEBUG):
			logger.info("scrapedtitle="+scrapedtitle)
			logger.info("scrapedurl="+scrapedurl)
			logger.info("scrapedthumbnail="+scrapedthumbnail)

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , scrapedtitle , scrapedurl , scrapedthumbnail , scrapedplot )

	# Extrae las entradas (carpetas)
	patronvideos  = '<li>[^<]+<a href="([^"]+)" title="([^"]+)"><img.*?src="([^"]+)"[^>]+>.*?<span[^>]+>(.*?)</span>'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	for match in matches:
		# Titulo
		try:
			scrapedtitle = unicode( match[1], "utf-8" ).encode("iso-8859-1")
		except:
			scrapedtitle = match[1]

		# URL
		scrapedurl = match[0]
		
		# Thumbnail
		scrapedthumbnail = match[2]
		
		# procesa el resto
		try:
			scrapedplot = unicode( match[3], "utf-8" ).encode("iso-8859-1")
		except:
			scrapedplot = match[3]
		
		scrapedplot = scrapedplot.replace("\r"," ")
		scrapedplot = scrapedplot.replace("\n"," ")
		scrapedplot = scrapedplot.replace("&quot;","'")
		scrapedplot = scrapedplot.replace("<br />","|")
		patronhtml = re.compile( '<img[^>]+>' )
		scrapedplot = patronhtml.sub( "", scrapedplot )
		patronhtml = re.compile( 'Uploader:[^\|]+\|' )
		scrapedplot = patronhtml.sub( "", scrapedplot )
		patronhtml = re.compile( 'Idioma:[^\|]+\|' )
		scrapedplot = patronhtml.sub( "", scrapedplot )
		patronhtml = re.compile( 'Tiene descarga directa:[^\|]+\|' )
		scrapedplot = patronhtml.sub( "", scrapedplot )
		patronhtml = re.compile( '\W*\|\W*' )
		scrapedplot = patronhtml.sub( "|", scrapedplot )
		patronhtml = re.compile( '\|Descripci.n:' )
		scrapedplot = patronhtml.sub( "\n\n", scrapedplot )
		
		scrapedplot = scrapedplot.replace("|b>Servidor:</b|","")
		scrapedplot = re.sub('<[^>]+>',"",scrapedplot)
		scrapedplot = scrapedplot.replace("b>","\n")
		# Depuracion
		if (DEBUG):
			logger.info("scrapedtitle="+scrapedtitle)
			logger.info("scrapedurl="+scrapedurl)
			logger.info("scrapedthumbnail="+scrapedthumbnail)

		# Añade al listado de XBMC
		xbmctools.addnewvideo( CHANNELNAME , "detail" , category , "Megavideo" , scrapedtitle , scrapedurl , scrapedthumbnail , scrapedplot )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def detailfolder(params,url,category):
	logger.info("[peliculasyonkis.py] detail")

	title = urllib.unquote_plus( params.get("title") )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = unicode( xbmc.getInfoLabel( "ListItem.Plot" ), "utf-8" )

	xbmctools.addnewvideo( CHANNELNAME , "detail" , category , "Megavideo" , title , url , thumbnail , plot )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def detail(params,url,category):
	logger.info("[peliculasyonkis.py] detail")

	title = urllib.unquote_plus( params.get("title") )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = unicode( xbmc.getInfoLabel( "ListItem.Plot" ), "utf-8" )

	# Descarga la página
	data = scrapertools.cachePage(url)
	#logger.info(data)

	# ------------------------------------------------------------------------------------
	# Busca los enlaces a los videos
	# ------------------------------------------------------------------------------------
	patronvideos  = 'href="http://www.peliculasyonkis.com/player/visor_([^\.]+).php.*?'
	patronvideos += 'id=([^"]+)".*?'
	patronvideos += 'alt="([^"]+)"'
	patronvideos += '(.*?)</tr>'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)

	
	if len(matches)>0:
		scrapertools.printMatches(matches)
		id,serv = ChoiceOneVideo(matches,title)
		logger.info("[peliculasyonkis.py]  id="+id)
		url = Decrypt_Server(id,serv)
		if (serv in ["pymeno2","pymeno3"]) and (":" in url):
			match = url.split(":")
			url = choiceOnePart(match)
			if url == "": return
		print 'codigo :%s' %url
	else:
		xbmctools.alertnodisponible()
		return ""
	
	if url == "":return
	xbmctools.playvideo(CHANNELNAME,SERVER[serv],url,category,title,thumbnail,plot)

def choiceOnePart(matches):
	opciones = []
	IDlist = []
	Nro = 0
	for codigo in matches:
		Nro = Nro + 1
		opciones.append("Parte %s " % Nro)
		
	dia = xbmcgui.Dialog()
	seleccion = dia.select("Selecciona uno ", opciones)
	logger.info("seleccion=%d" % seleccion)
	if seleccion == -1 : return ""
	id = matches[seleccion]
	return id
	
def ChoiceOneVideo(matches,title):
	logger.info("[peliculasyonkis.py] ChoiceOneVideo")
	
	opciones = []
	IDlist = []
	servlist = []
	Nro = 0
	fmt=duracion=id=""
	
	for server,codigo,audio,data in matches:
		try:
			ql= ""
			servidor = SERVER[server]
			Nro = Nro + 1
			regexp = re.compile(r"title='([^']+)'")
			match = regexp.search(data)
			if match is not None:
				fmt = match.group(1)
				fmt = fmt.replace("Calidad","").strip()
			regexp = re.compile(r"Duraci\xc3\xb3n:([^<]+)<")
			match = regexp.search(data)
			if match is not None:
				duracion = match.group(1).replace(".",":")
				if len(duracion.strip())>0:
					duracion = duracion + " minutos"
			audio = audio.replace("Subt\xc3\xadtulos en Espa\xc3\xb1ol","Subtitulado") 
			audio = audio.replace("Audio","").strip()
			data2 =  re.sub("<[^>]+>",">",data)
			data2 = data2.replace(">>>","").replace(">>","<")
			data2 = re.sub("[0-9:.]+","",data2)
			print data2
			Video_info = ""
			regexp = re.compile(r"<(.+?)<")
			match = regexp.search(data2)
			if match is not None:
				
				Video_info = match.group(1)
				print Video_info 
				Video_info = "-%s" %Video_info.replace("Duraci\xc3\xb3n","").strip()
			else:
				regexp = re.compile(r">(.+?)<")
				match = regexp.search(data2)
				if match is not None:
				
					Video_info = match.group(1)
					print Video_info 
					Video_info = "-%s" %Video_info.replace("Duraci\xc3\xb3n","").strip()				
			opciones.append("%02d) [%s] - [%s] %s (%s%s)" % (Nro , audio,servidor,duracion,fmt,Video_info))
			if '&al=' in codigo:
				Nro += 1
				codigos = codigo.split('&al=')
				IDlist.append(codigos[0])
				servlist.append(server)
				opciones.append("%02d) [%s] - [%s] %s (%s-%s)" % (Nro , audio,"Megaupload",duracion,fmt,Video_info))
				IDlist.append(codigos[1])
				servlist.append("megaupload")
			else:
				IDlist.append(codigo)
				servlist.append(server)
		except urllib2.URLError,e:
			logger.info("[peliculasyonkis.py] error:%s (%s)" % (e.code,server))
	dia = xbmcgui.Dialog()
	seleccion = dia.select(title, opciones)
	logger.info("seleccion=%d" % seleccion)
	if seleccion == -1 : return "",""
	id = IDlist[seleccion]
	serv = servlist[seleccion]
	print "ID :%s  Servidor :%s" %(id,serv)
	return id,serv
	
	
def Decrypt_Server(id_encoded,servidor):
	id = id_encoded
	DEC       = Yonkis.DecryptYonkis()
	
	if   'pymeno2'   == servidor: idd=DEC.decryptID(DEC.charting(DEC.unescape(id)))   
	elif 'pymeno3'   == servidor: idd=DEC.decryptID(DEC.charting(DEC.unescape(id)))   
	elif 'pymeno4'   == servidor: idd=DEC.decryptID(DEC.charting(DEC.unescape(id)))   
	elif 'pymeno5'   == servidor: idd=DEC.decryptID_series(DEC.unescape(id))          
	elif 'pymeno6'   == servidor: idd=DEC.decryptID_series(DEC.unescape(id))      
	elif 'svueno'    == servidor:
		idd=DEC.decryptALT(DEC.charting(DEC.unescape(id)))
		if ":" in idd:
			ids = idd.split(":")
			idd = "http://stagevu.com/video/%s" %choiceOnePart(ids).strip()
		else:
			idd = "http://stagevu.com/video/%s" %idd
	elif 'manueno'   == servidor:
		idd=DEC.decryptALT(DEC.charting(DEC.unescape(id)))
		if len(idd)>50:
			ids = idd.split()
			idd = choiceOnePart(ids).strip()
		
	elif 'videoweed' == servidor:
		idd= DEC.decryptID(DEC.charting(DEC.unescape(id))) 
		if ":" in idd:
			ids = idd.split(":")
			idd = "http://www.videoweed.com/file/%s" %choiceOnePart(ids).strip()		
		else:
			idd = "http://www.videoweed.com/file/%s" %idd
	elif 'veoh2'     == servidor: idd=DEC.decryptALT(DEC.charting(DEC.unescape(id))) 
	elif 'megaupload'== servidor: 
		idd=DEC.ccM(DEC.unescape(id))
		if ":" in idd:
			idd = choiceOnePart(idd.split(":"))
		
	elif 'pfflano'   == servidor: 
		idd=DEC.decryptALT(DEC.charting(DEC.unescape(id)))
		print idd
		ids = idd.split()
		idd = choiceOnePart(ids).strip()
		return idd
		
	else:
		return ""
	
	return idd
	
	
	
	
def Activar_Novedades(params,activar,category):
	if activar == "false":
		config.setSetting("activar","true")
	else:
		config.setSetting("activar","false")
	print "opcion menu novedades :%s" %config.getSetting("activar")
	
	#xbmc.executebuiltin('Container.Update')	
	xbmc.executebuiltin('Container.Refresh')
	
