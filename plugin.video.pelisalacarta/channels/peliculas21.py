# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para peliculas21 by Bandavi
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
import youtube
import config
import config
import logger
import buscador
import decrypt21

CHANNELNAME = "peliculas21"

# Esto permite su ejecución en modo emulado
try:
	pluginhandle = int( sys.argv[ 1 ] )
except:
	pluginhandle = ""

# Traza el inicio del canal
logger.info("[peliculas21.py] init")

DEBUG = True
IMAGES_PATH = xbmc.translatePath( os.path.join( config.DATA_PATH, 'resources' , 'images','posters' ) )

def mainlist(params,url,category):
	logger.info("[peliculas21.py] mainlist")

	novedades = "http://www.peliculas21.com/ajaxs/ajax_periodos.php?valor=&periodo=0&idgenero=0&idactor=0&listado_style=2&pagina=&periodos_ajax=&valorperiodo=4"
	MasVistos = "http://www.peliculas21.com/ajaxs/ajax_periodos.php?valor=hits&periodo=0&idgenero=0&idactor=0&listado_style=2&pagina=&periodos_ajax=&valorperiodo=4"
	puntuacion = "http://www.peliculas21.com/ajaxs/ajax_periodos.php?valor=puntuacion&periodo=0&idgenero=0&idactor=0&listado_style=2&pagina=&periodos_ajax=&valorperiodo=4"
	# Añade al listado de XBMC

	xbmctools.addnewfolder( CHANNELNAME , "listsimpleMirror" , category , "Películas - Novedades"            ,novedades,"","")
	xbmctools.addnewfolder( CHANNELNAME , "listsimpleMirror" , category , "Películas - Mas Vistos"           ,MasVistos,"","")
	xbmctools.addnewfolder( CHANNELNAME , "listsimpleMirror" , category , "Películas - Mejor Puntuadas"      ,puntuacion,"","")
	xbmctools.addnewfolder( CHANNELNAME , "buscaporanyo"     , category , "Películas - Busqueda por Año de Estreno"             ,"http://www.peliculas21.com/estrenos/","","")
	xbmctools.addnewfolder( CHANNELNAME , "listsimple"       , category , "Trailers  - Próximos Estrenos"    ,"http://www.peliculas21.com/trailers/","","")
	xbmctools.addnewfolder( CHANNELNAME , "peliscat"         , category , "Películas - Lista por categorías" ,"http://www.peliculas21.com/","","")
	xbmctools.addnewfolder( CHANNELNAME , "pelisalfa"        , category , "Peliculas - Lista alfabética"     ,"","","")
	xbmctools.addnewfolder( CHANNELNAME , "listaActoresMasBuscados" , category , "Actores   - Lista Los Más Buscados"     ,"http://www.peliculas21.com/","","")
	xbmctools.addnewfolder( CHANNELNAME , "buscaporletraActor" , category , "Actores   - Lista Alfabética"     ,"http://www.peliculas21.com/actores/","","")	
	xbmctools.addnewfolder( CHANNELNAME , "search"           , category , "Películas - Buscar"               ,"","","")


	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )

	# Disable sorting...
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def pelisalfa(params, url, category):

	xbmctools.addnewfolder( CHANNELNAME ,"listsimpleMirror", category , "0-9","http://www.peliculas21.com/0-9/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listsimpleMirror", category , "A","http://www.peliculas21.com/a/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listsimpleMirror", category , "B","http://www.peliculas21.com/b/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listsimpleMirror", category , "C","http://www.peliculas21.com/c/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listsimpleMirror", category , "D","http://www.peliculas21.com/d/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listsimpleMirror", category , "E","http://www.peliculas21.com/e/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listsimpleMirror", category , "F","http://www.peliculas21.com/f/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listsimpleMirror", category , "G","http://www.peliculas21.com/g/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listsimpleMirror", category , "H","http://www.peliculas21.com/h/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listsimpleMirror", category , "I","http://www.peliculas21.com/i/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listsimpleMirror", category , "J","http://www.peliculas21.com/j/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listsimpleMirror", category , "K","http://www.peliculas21.com/k/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listsimpleMirror", category , "L","http://www.peliculas21.com/l/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listsimpleMirror", category , "M","http://www.peliculas21.com/m/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listsimpleMirror", category , "N","http://www.peliculas21.com/n/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listsimpleMirror", category , "O","http://www.peliculas21.com/o/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listsimpleMirror", category , "P","http://www.peliculas21.com/p/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listsimpleMirror", category , "Q","http://www.peliculas21.com/q/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listsimpleMirror", category , "R","http://www.peliculas21.com/r/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listsimpleMirror", category , "S","http://www.peliculas21.com/s/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listsimpleMirror", category , "T","http://www.peliculas21.com/t/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listsimpleMirror", category , "U","http://www.peliculas21.com/u/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listsimpleMirror", category , "V","http://www.peliculas21.com/v/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listsimpleMirror", category , "W","http://www.peliculas21.com/w/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listsimpleMirror", category , "X","http://www.peliculas21.com/x/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listsimpleMirror", category , "Y","http://www.peliculas21.com/y/","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listsimpleMirror", category , "Z","http://www.peliculas21.com/z/","","")

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )

	# Disable sorting...
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )



def search(params,url,category):
	logger.info("[peliculas21.py] search")
	buscador.listar_busquedas(params,url,category)

def searchresults(params,url,category):
	logger.info("[peliculas21.py] searchresults")
	
	buscador.salvar_busquedas(params,url,category)
	#convert to HTML
	tecleado = url.replace(" ", "+")
	searchUrl = "http://www.peliculas21.com/?palabra="+tecleado
	listsimpleMirror(params,searchUrl,category)

def performsearch(texto):
	logger.info("[peliculas.py] performsearch")
	url = "http://www.peliculas21.com/?palabra="+texto
	url1 = "http://www.peliculas21.com"

	# Descarga la página
	data = scrapertools.cachePage(url)

	# Extrae las entradas (carpetas)

	patronvideos  = '<div.+?class="filmgal"[^>]+>.*?'
	patronvideos += '<a href="([^"]+)"[^>]+'                                        # url
	patronvideos += '>.*?<img alt="([^"]+)" '                                       # Titulo

	patronvideos += 'src="([^"]+)"'                                                 # Imagen
	patronvideos += '(.*?)reproducciones'                        # Contenido

	
	resultados = []
	for match in matches:
		# Atributos
		scrapedplot = ""
		scrapedthumbnail = ""
		try:
			scrapedtitle = re.compile('<span class\="titulotool">(.*?)</div>',re.DOTALL).findall(match[3])[0]
			scrapedtitle = re.sub("<[^>]+>","",scrapedtitle).replace("\n\t\t","").strip()
			#print scrapedtitle
		except:
			scrapedtitle = match[1]		
		
		#scrapedtitle = scrapedtitle.replace("<span class='style4'>","")
		#scrapedtitle = scrapedtitle.replace("</span>","")
		scrapedurl = urlparse.urljoin(url1,match[0])
		
		scrapedthumbnail = urlparse.urljoin(url1,match[2])
		scrapedthumbnail = scrapedthumbnail.replace(" ","")
		plot = match[3]
		print plot
		try    :Sinopsis = re.compile("Sinopsis:(.*?)</div>").findall(plot)[0]
		except :Sinopsis="<>"
		print Sinopsis
		Sinopsis = " Sinopsis: " + Sinopsis.strip()
			
		try    :Genero = re.compile("Género:(.+?)</div>").findall(plot)[0]
		except :Genero = ""
		Genero = "Genero: " + Genero.strip()
		

		try    :Duracion = re.compile("Duraci&oacute;n:(.+?)</div>").findall(plot)[0]
		except :Duracion = ""
		Duracion = "Duracion: " + Duracion.strip()
		
		try    :Actores = re.compile("Actores:(.+?)</div>").findall(plot)[0]
		except :Actores = ""
		Actores = "Actores: " + Actores.strip()
									
		scrapedplot  = Genero + "\n" + Duracion + "\n" + Actores + "\n" + Sinopsis
		

		

		#scrapedplot += match[4].replace("\n","")+"\n"	
		

		#scrapedplot += match[5].replace("\n"," ")+"\n"
		
		#scrapedplot += ""
		scrapedplot  = re.sub("<[^>]+>","",scrapedplot)
		scrapedplot  = scrapedplot.replace("&aacute;","á")
		scrapedplot  = scrapedplot.replace("&iacute;","í")
		scrapedplot  = scrapedplot.replace("&eacute;","é")
		scrapedplot  = scrapedplot.replace("&oacute;","ó")
		scrapedplot  = scrapedplot.replace("&uacute;","ú")
		scrapedplot  = scrapedplot.replace("&ntilde;","ñ")
		

		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		resultados.append( [CHANNELNAME , "listvideos" , "buscador" , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot ] )
		
	return resultados

def peliscat(params,url,category):
	logger.info("[peliculas21.py] peliscat")
	
	# Descarga la página
	data = scrapertools.cachePage(url)
	
	# Extrae los Géneros de las Peliculas

	patronvideos = '<div id="textidgenero">Género:</div>(.*?)</select>'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)

	patronvideos = '<option value="([^"]+)"  >([^<]+)</option>'
	matches1 = re.compile(patronvideos,re.DOTALL).findall(matches[0])
	for match in matches1:
	
		#http://www.peliculas21.com/ajaxs/ajax_periodos.php?valor=&periodo=0&idgenero=5&idactor=0&listado_style=2&pagina=&periodos_ajax=&valorperiodo=4&num_ale=0.5685049552958528
		url	= "http://www.peliculas21.com/ajaxs/ajax_periodos.php?valor=&periodo=0&idgenero=%s&idactor=0&listado_style=2&pagina=&periodos_ajax=&valorperiodo=4" %match[0]
		genero = match[1]
	
	
		xbmctools.addnewfolder( CHANNELNAME , "listsimpleMirror" , category , genero ,url,"","")

	
	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )

	# Disable sorting...
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def listsimple(params,url,category):
	logger.info("[peliculas21.py] listsimple")
	url1 = "http://www.peliculas21.com"
	# Descarga la página
	data = scrapertools.cachePage(url)
	'''
	<div class="fichafilm" >
        <a href="/el-hombre-lobo/"  target="_blank" class="titulo">
            <img alt="El hombre lobo" src="/thumbs_95_140_85/t2_4859.jpg"  width="95" height="140" border="0" />El hombre lobo        </a> (2010)<br />
        
                    <b>Duraci&oacute;n:</b> 1h 34min<br />
                <div><b>G&eacute;nero:</b>
    Thriller y Miedo / Terror    </div>
    <div><b>Doblaje:</b>
     Espa&ntilde;ol    </div>
    <div style="text-align:justify;">
        <b>Sinopsis:</b>
		Remake del clásico de terror de 1941, que desarrolla la historia de Lawrence, un joven que debe afrontar el abandono de su madre desde muy pequeño, y quién huye de su pueblo en busca de un mejor futuro que le permita olvidar momentos tan dolorosos de su niñez. Lawrence, se ve obligado a volver despu...    </div>
    <div class="datos">
            <div class="verde">+
    613 puntos</div>
        <div class="reproducciones">
    122638 reproducciones</div>
        <br class="corte"/></div></div>
	'''
	#|<div class="fichafilm" >.*?
	# Extrae las entradas (carpetas)
	
	patronvideos  = '<div.+?class="filmgal-trailer"[^>]+>.*?'
	patronvideos += '<a href="([^"]+)"[^>]+'                                        # url
	patronvideos += '>.*?<img alt="([^"]+)" '                                       # Titulo

	patronvideos += 'src="([^"]+)"'                                                 # Imagen
	patronvideos += '(.*?)reproducciones</div>'                        # Contenido
	print patronvideos
	print data
	#logger.info("[ listsimple  patronvideos")
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)
	#logger.info("[ listsimple  matches")
	for match in matches:
		# Atributos
		scrapedplot = ""
		scrapedthumbnail = ""
		try:
			scrapedtitle = re.compile('<span class\="titulotool">(.*?)</div>',re.DOTALL).findall(match[3])[0]
			scrapedtitle = re.sub("<[^>]+>"," ",scrapedtitle).replace("  "," ").strip()
			#print scrapedtitle
		except:
			scrapedtitle = match[1]		
		
		#scrapedtitle = scrapedtitle.replace("<span class='style4'>","")
		#scrapedtitle = scrapedtitle.replace("</span>","")
		scrapedurl = urlparse.urljoin(url1,match[0])
		
		scrapedthumbnail = urlparse.urljoin(url1,match[2])
		scrapedthumbnail = scrapedthumbnail.replace(" ","")
		plot = match[3]
		print plot
		try    :Sinopsis = re.compile("Sinopsis:(.*?)</div>").findall(plot)[0]
		except :Sinopsis="<>"
		print Sinopsis
		Sinopsis = " Sinopsis: " + Sinopsis.strip()
			
		try    :Genero = re.compile("Género:(.+?)</div>").findall(plot)[0]
		except :Genero = ""
		Genero = "Genero: " + Genero.strip()
		

		try    :Duracion = re.compile("Duraci&oacute;n:(.+?)</div>").findall(plot)[0]
		except :Duracion = ""
		Duracion = "Duracion: " + Duracion.strip()
		
		try    :Actores = re.compile("Actores:(.+?)</div>").findall(plot)[0]
		except :Actores = ""
		Actores = "Actores: " + Actores.strip()
									
		scrapedplot  = Genero + "\n" + Duracion + "\n" + Actores + "\n" + Sinopsis
		

		

		#scrapedplot += match[4].replace("\n","")+"\n"	
		

		#scrapedplot += match[5].replace("\n"," ")+"\n"
		
		#scrapedplot += ""
		scrapedplot  = re.sub("<[^>]+>","",scrapedplot)
		scrapedplot  = scrapedplot.replace("&aacute;","á")
		scrapedplot  = scrapedplot.replace("&iacute;","í")
		scrapedplot  = scrapedplot.replace("&eacute;","é")
		scrapedplot  = scrapedplot.replace("&oacute;","ó")
		scrapedplot  = scrapedplot.replace("&uacute;","ú")
		scrapedplot  = scrapedplot.replace("&ntilde;","ñ")
		
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )
		#<div class="pagination" align="center" ><p><span  class='current'>1</span><a  href='/estrenos/2/'>2</a><a  href='/estrenos/2/'>Siguiente &raquo;</a><a  href='/estrenos/2/'></a>
	# Extrae la marca de siguiente página

	
	patronvideos  = "<span  class='current'>[^<]+</span><a  href='([^']+)'>"
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	if len(matches)>0:
		scrapedtitle = "Página siguiente"
		scrapedurl = urlparse.urljoin(url1,matches[0])
		scrapedthumbnail = ""
		scrapedplot = ""
		xbmctools.addnewfolder( CHANNELNAME , "listsimple" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )
	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )

	# Disable sorting...
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def listsimpleMirror(params,url,category):
	logger.info("[peliculas21.py] listsimple")
	url1 = "http://www.peliculas21.com"
	# Descarga la página
	data = scrapertools.cachePage(url)

	# Extrae las entradas (carpetas)

	patronvideos  = '<div.+?class="filmgal"[^>]+>.*?'
	patronvideos += '<a href="([^"]+)"[^>]+'                                        # url
	patronvideos += '>.*?<img alt="([^"]+)" '                                       # Titulo

	patronvideos += 'src="([^"]+)"'                                                 # Imagen
	patronvideos += '(.*?)reproducciones'                        # Contenido
	#print patronvideos
	#print data
	#logger.info("[ listsimple  patronvideos")
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)
	#logger.info("[ listsimple  matches")
	for match in matches:
		# Atributos
		scrapedplot = ""
		scrapedthumbnail = ""
		#print match[3]
		try:
			scrapedtitle = re.compile('<span class\="titulotool">(.*?)</div>',re.DOTALL).findall(match[3])[0]
			scrapedtitle = re.sub("<[^>]+>","",scrapedtitle).replace("\n\t\t","").strip()
			#print scrapedtitle
		except:
			scrapedtitle = match[1]
			
		
		#scrapedtitle = scrapedtitle.replace("<span class='style4'>","")
		#scrapedtitle = scrapedtitle.replace("</span>","")
		scrapedurl = urlparse.urljoin(url1,match[0])
		
		scrapedthumbnail = urlparse.urljoin(url1,match[2])
		scrapedthumbnail = scrapedthumbnail.replace(" ","")
		plot = match[3].replace("\n","")
		try    :Sinopsis = re.compile("Sinopsis:(.*?)</div>").findall(plot)[0]
		except :Sinopsis="<>"
		print Sinopsis
		Sinopsis = "Sinopsis: " + Sinopsis.strip()
			
		try	   :Genero = re.compile("G&eacute;nero:(.*?)</div>").findall(plot)[0]
		except :Genero = ""
		Genero = "Genero:  " + Genero.strip()
		print Genero

		try    :Duracion = re.compile("Duraci&oacute;n:(.*?)</div>").findall(plot)[0]
		except :Duracion = ""
		Duracion = "Duracion: " + Duracion.strip()
		
		try    :Actores = re.compile("Actores:(.*?)</div>").findall(plot)[0]
		except :Actores = ""
		Actores = "Actores:  " + Actores.strip()
		print Actores							
		scrapedplot  = Genero + "\n" + Duracion + "\n" + Actores + "\n" + Sinopsis
		

		

		#scrapedplot += match[4].replace("\n","")+"\n"	
		

		#scrapedplot += match[5].replace("\n"," ")+"\n"
		
		#scrapedplot += ""
		scrapedplot  = re.sub("<[^>]+>","",scrapedplot)
		scrapedplot  = scrapedplot.replace("&aacute;","á")
		scrapedplot  = scrapedplot.replace("&iacute;","í")
		scrapedplot  = scrapedplot.replace("&eacute;","é")
		scrapedplot  = scrapedplot.replace("&oacute;","ó")
		scrapedplot  = scrapedplot.replace("&uacute;","ú")
		scrapedplot  = scrapedplot.replace("&ntilde;","ñ")
		
		
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )
		#<div class="pagination" align="center" ><p><span  class='current'>1</span><a  href='/estrenos/2/'>2</a><a  href='/estrenos/2/'>Siguiente &raquo;</a><a  href='/estrenos/2/'></a>
	# Extrae la marca de siguiente página
	

	patronvideos  = "<a  href=\"#periodoslist\" onclick=\"paginaperiodo\(([^\)]+)\);\">Siguiente &raquo;</a>"
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	if len(matches)>0:
		#http://www.peliculas21.com/ajaxs/ajax_periodos.php?valor=&periodo=0&idgenero=5&idactor=0&listado_style=2&pagina=&periodos_ajax=&valorperiodo=4
		scrapedtitle = "Página siguiente"
	
		paramsurl = dict(part.split('=') for part in url.split('?')[1].split('&'))
		print paramsurl
		sigtepag = matches[0].replace("'","").split(',')
		scrapedurl = "http://www.peliculas21.com/ajaxs/ajax_periodos.php?valor=%s&periodo=%s&idgenero=%s&idactor=%s&listado_style=%s&pagina=%s&periodos_ajax=%s&valorperiodo=%s" %(paramsurl["valor"],paramsurl["periodo"],paramsurl["idgenero"],paramsurl["idactor"],paramsurl["listado_style"],sigtepag[6],paramsurl["periodos_ajax"],paramsurl["valorperiodo"])
		scrapedthumbnail = ""
		scrapedplot = ""
		xbmctools.addnewfolder( CHANNELNAME , "listsimpleMirror" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )
		
	else:
		
		
		patron = "<span  class='current'>[^<]+</span><a  href='([^']+)'>"
		matches = re.compile(patron,re.DOTALL).findall(data)
		if len(matches)>0:
			scrapedtitle = "Página siguiente"
			scrapedurl   = urlparse.urljoin(url1,matches[0])
			scrapedthumbnail = ""
			scrapedplot  = ""
			xbmctools.addnewfolder( CHANNELNAME , "listsimpleMirror" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )
			
	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )

	# Disable sorting...
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )


def listvideos(params,url,category):
	logger.info("[peliculas21.py] listvideos")

	if url=="":
		url = "http://www.peliculas21.com"
	
	# Descarga la página
	data = scrapertools.cachePage(url)
	#logger.info(data)
	#title = urllib.unquote_plus(params.get("title"))
	#thumbnail = urllib.unquote_plus(params.get("thumbnail"))
	#plot = urllib.unquote_plus(params.get("plot"))
	
	# Busca el area donde estan los videos y la descripcion
	patronvideos = '<div  class="peliculadoblaje">(.*?)<!-- FIN #content-->'
	matches      = re.compile(patronvideos,re.DOTALL).findall(data)
	
	# busca el titulo y el thumbnail
	patronvideos = '<img src="([^"]+)"[^>]+>[^<]+<[^>]+>([^<]+)</div>'
	matches2 =  re.compile(patronvideos,re.DOTALL).findall(matches[0])
	for match in matches2:
		title = match[1]
		thumbnail = urlparse.urljoin(url,match[0])
	plot = ""
	patronvideos = '<b>Duraci&oacute;n:</b>(.*?)<br />'
	duracion     = re.compile(patronvideos,re.DOTALL).findall(matches[0])
	if len(duracion)>0:plot = "Duracion:"+duracion[0] + "\n"
		
	patronvideos = '<b>G&eacute;nero:</b>(.*?)<br />'
	genero       = re.compile(patronvideos,re.DOTALL).findall(matches[0])
	if len(genero)>0:plot = plot + "Genero:  "+genero[0] +"\n"
	
	patronvideos = '<b>Sinopsis:</b>(.*?)</div>'
	sinopsis     = re.compile(patronvideos,re.DOTALL).findall(matches[0])
	
	
	  
	# Busca los actores
	matchesactores = buscactores(matches[0]) 
	if len(matchesactores)>0:
		plot = plot + "Actores:   "
		c = 0
		actores = "ACTORES DE ESTA PELICULA :\n\n"
		for match in matchesactores:
			c =  c + 1
			actores = actores + "-"+match[1] + "\n"
			if   c == 3:
				plot = plot + match[1] + "\n"
			elif c == 4:
				plot = plot + "*              "  + match[1]+" "
			else:
				plot = plot + match[1]+ " , "
		
	plot = plot	+ "\nSinopsis: " + sinopsis[0]
	plot = re.sub("<[^>]+>"," ",plot)
	# Busca el trailer 
	patronvideos = '<param name="movie" value="([^"]+)"></param>'
	matchtrailer = re.compile(patronvideos,re.DOTALL).findall(matches[0])
	if len(matchtrailer)>0:
		for match in matchtrailer:
		# Añade al listado de XBMC
			xbmctools.addnewvideo( CHANNELNAME , "youtubeplay" , category ,"Directo", "Ver El Trailer de : "+title , match , thumbnail, plot )
	else:
		import trailertools
		print title
		s = unicode( title, "latin-1" )
		# Añade al listado de XBMC

		xbmctools.addnewfolder( "trailertools" , "buscartrailer" , category , config.getLocalizedString(30110)+" "+title , url , os.path.join(IMAGES_PATH, 'trailertools.png'), plot ) # Buscar trailer para
		
		
	matchesBK = matches[0]
	# Extrae las entradas (videos) para megavideo con tipo de audio
	patronvideos  = '<span  style="font-size:12px;"><strong>(.*?)</strong></span><br/>.*?'
	patronvideos += '<span.*?>.*?<a href="http\:\/\/www.megavideo.com\/[\?v=|v/]+([A-Z0-9]{8}).*?" target="_blank">1</a>.</span><br />'
	
	matches = re.compile(patronvideos,re.DOTALL).findall(matches[0])
	scrapertools.printMatches(matches)
	encontrados = set()
	for match in matches:
		if match[1] not in encontrados:
			encontrados.add(match[1])
		
			# Titulo
			scrapedtitle = title + " -   [" +scrapertools.entityunescape(match[0])+ "]" + " (Megavideo)"

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
			xbmctools.addnewvideo( CHANNELNAME , "play" , category ,"Megavideo", scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )
	if len(matches)==0:
		listavideos = servertools.findvideos(data)
		encontrados = set()
		for titulo,scrapedurl,servidor in listavideos:
			if scrapedurl.strip() not in encontrados:
				encontrados.add(scrapedurl.strip())
				xbmctools.addnewvideo( CHANNELNAME , "play" , category ,servidor, title+ " - %s" % titulo  , scrapedurl , thumbnail, plot )		
	'''
	<span class="bloque-uploader">Anónimo</span>
	<span class="bloque-doblaje"><img src="../images/esp.gif" class="bandera" /></span>
	<span class="bloque-link">Opción 8: <a href="javascript:goTo('aHR0cDovL3d3dy5tZWdhdmlkZW8uY29tLz92PTVOM0JYOVMx', 'megavideo.com')" rel="nofollow">Ver película</a></span>
	'''
	patronvideos = '<span class="bloque-doblaje">(.+?)</span>[^<]+'
	patronvideos +='<span class="bloque-link">[^<]+<a href="javascript\:goTo\(\'([^\']+)\'\, \'([^\']+)\'\)"(.+?)</span>'
	#patronvideos +='(?:\| <a href="javascript\:goTo\(\'([^\']+)\'\, \'([^\']+)\'\)".*?)</span>'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)
	for match in matches:
	
		# URL
		if "megavideo" in match[2]:
			server = "Megavideo"
		elif "megaupload" in match[2]:
			server = "Megaupload"
		if "esp.gif" in match[0]:
			doblaje = "Español"
			
		else:
			doblaje = match[0].strip()			
		base64 = decrypt21.Base64()
		try:
			url2 = re.compile("javascript\:goTo\(\'([^\']+)\'\, \'([^\']+)\'\)").findall(match[3])[0]
			scrapedurl2 = base64._extract_code(base64.decode(url2[0]))
			scrapedurl = base64._extract_code(base64.decode(match[1]))
			part1 = " Parte 1 "
			part2 = " Parte 2 "
			scrapedtitle2 = title + part2+ " -   [" +doblaje+ "]" + " ("+server+")"
			#print match[3]
		except:
			scrapedurl = base64._extract_code(base64.decode(match[1]))
			part1 = ""
			part2 = ""			
			
		

		scrapedtitle = title + part1+ " -   [" +doblaje+ "]" + " ("+server+")"


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
		xbmctools.addnewvideo( CHANNELNAME , "play" , category ,server, scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )
		if part2:
			xbmctools.addnewvideo( CHANNELNAME , "play" , category ,server, scrapedtitle2 , scrapedurl2 , scrapedthumbnail, scrapedplot )
	# Extrae las entradas (videos) directos
	patronvideos = 'flashvars="file=([^\&]+)\&amp;controlbar=over'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)
	if len(matches)>0:
		
		data1 = scrapertools.cachePage(matches[0])
		#logger.info(data)
		patron = 'author">(.*?)</media:credit>.*?<media\:content url="([^"]+)"'
		matches = re.compile(patron,re.DOTALL).findall(data1)
		scrapertools.printMatches(matches)
		
		for match in matches:
			# Añade al listado de XBMC
			xbmctools.addnewvideo( CHANNELNAME , "play" , category , "Directo" , title +" -  ["+match[0]+"]"+ " (Directo)" , match[1] , thumbnail , plot )
			
	# Busca otras peliculas relacionadas con los actores
	if len(matchesactores)>0:
		titulo = "Busca otros Films de los actores de esta pelicula"
		xbmctools.addnewfolder( CHANNELNAME , "listaractores" , category , titulo , matchesBK , thumbnail, actores )
		
	# Lista peliculas relacionadas
	titulo = "Ver Peliculas Relacionadas" 
	matches = buscarelacionados(matchesBK)
	plot2 = "PELICULAS RELACIONADAS :\n\n"
	for match in matches:
		plot2 = plot2 + "-"+match[1]+"\n"
	xbmctools.addnewfolder( CHANNELNAME , "listarelacionados" , category , titulo , matchesBK , thumbnail, plot2 )
	
	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )

	# Disable sorting...
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )




def play(params,url,category):
	logger.info("[peliculas21.py] play")

	title = unicode( xbmc.getInfoLabel( "ListItem.Title" ), "utf-8" )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = unicode( xbmc.getInfoLabel( "ListItem.Plot" ), "utf-8" )
	server = params["server"]
	
	xbmctools.playvideo(CHANNELNAME,server,url,category,title,thumbnail,plot)

def youtubeplay(params,url,category):
        logger.info("[peliculas21.py] youtubeplay")

	title = urllib.unquote_plus( params.get("title") )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = "Ver Video"
	server = "Directo"
	id = youtube.Extract_id(url)
	videourl = youtube.geturl(id)

	if videourl == ("" or "Esc"):return
	logger.info("link directo de youtube : "+videourl)
	xbmctools.playvideo("Trailer",server,videourl,category,title,thumbnail,plot)
 

def listaractores(params,data,category):
	logger.info("[peliculas21.py] listaractores")
	
	url1 = "http://www.peliculas21.com"
	actores = buscactores(data)
	opciones = []
	actorURL = []
	for i in actores:
		opciones.append(i[1])
		actorURL.append(urlparse.urljoin(url1,i[0]))           
	dia = xbmcgui.Dialog()
	seleccion = dia.select("Selecciona uno ", opciones)
	logger.info("seleccion=%d" % seleccion)
	if seleccion == -1:return
	else:
		listsimple(params,actorURL[seleccion],category)
	return
	
def buscactores(data):
	patronvideos = ' <a href="([^"]+)">(.*?)</a>'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	return(matches)
	
def listarelacionados(params,data,category):
	logger.info("[peliculas21.py] listaractores")
	
	url1 = "http://www.peliculas21.com"
	#patronvideos = '<div><a href="([^"]+)">([^<]+)</a><br'
	matches = buscarelacionados(data) #re.compile(patronvideos,re.DOTALL).findall(data)
	
	opciones = []
	URL = []
	for i in matches:
		opciones.append(i[1])
		URL.append(urlparse.urljoin(url1,i[0]))           
	dia = xbmcgui.Dialog()
	seleccion = dia.select("Selecciona uno ", opciones)
	logger.info("seleccion=%d" % seleccion)
	if seleccion == -1:return
	else:
		listvideos(params,URL[seleccion],category)
	return
	
def buscarelacionados(data):
	patronvideos = '<div class="film"><a href="([^"]+)"><[^>]+><br />([^<]+)</a>'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	return (matches)
	
def buscaporletraActor(params,url,category):
	logger.info("[peliculas21.py] buscaporletra")
	'''
	data = scrapertools.cachePage(url)
	patron  = '<div class="title">Listado de Actores</div><br/>(.*?)<div class="subtitulo">Abecedario</div>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	patron  = '<a href="(.*?)">(.*?)</a>'
	matches = re.compile(patron,re.DOTALL).findall(matches[0])
    '''    
	letras = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        
	opciones = []

	#opciones.append("Buscar por palabras (Teclado)")
	#opciones.append("0-9")
	for letra in letras:
		opciones.append(letra)
	dia = xbmcgui.Dialog()
	
	seleccion = dia.select("Elige una letra : ", opciones)
	logger.info("seleccion=%d" % seleccion)
	if seleccion == -1 :return

	
	url   = "http://www.peliculas21.com/actores/%s/" %letras[seleccion]
	listActoresAlfab(params,url,category)
				
	
def listaActoresMasBuscados(params,url,category):
	logger.info("[peliculas21.py] listaActoresMasBuscados")
	
	url1 = "http://www.peliculas21.com"
	# Descarga la página
	data = scrapertools.cachePage(url)
	patronvideos = 'Los más buscados:(.*?)Más actores</a></div>'
	matches1 = re.compile(patronvideos,re.DOTALL).findall(data)
	patronvideos = '<a href="([^"]+)">([^<]+)</a>'
	matches =  re.compile(patronvideos,re.DOTALL).findall(matches1[0])
	scrapertools.printMatches(matches)
	for match in matches:
		# Titulo
		scrapedtitle = match[1]
		# URL
		scrapedurl = urlparse.urljoin(url1,match[0])
		# Thumbnail
		scrapedthumbnail = ""
        
		# Argumento
		scrapedplot = "Busca los Films existentes de este Actor ó Actriz"

		# Depuracion
		if (DEBUG):
			logger.info("scrapedtitle="+scrapedtitle)
			logger.info("scrapedurl="+scrapedurl)
			logger.info("scrapedthumbnail="+scrapedthumbnail)

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELNAME , "listsimple" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )
		
	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
		
	# Disable sorting...
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )


def listActoresAlfab(params,url,category):
	logger.info("[peliculas21.py] listaActoresAlfab")
	

	
	# Descarga la página
	data = scrapertools.cachePage(url)

	patronvideos = '<div class="actores_2">(.*?)</div></div>'
	matches1 = re.compile(patronvideos,re.DOTALL).findall(data)
	patronvideos = '<a href="([^"]+)">([^<]+)</a>'
	matches =  re.compile(patronvideos,re.DOTALL).findall(matches1[0])
	scrapertools.printMatches(matches)
	for match in matches:
		# Titulo
		scrapedtitle = match[1]
		# URL
	
		scrapedurl = urlparse.urljoin(url,match[0])
		# Thumbnail
		scrapedthumbnail = ""
        
		# Argumento
		scrapedplot = "Busca los Films existentes de este Actor ó Actriz"

		# Depuracion
		if (DEBUG):
			logger.info("scrapedtitle="+scrapedtitle)
			logger.info("scrapedurl="+scrapedurl)
			logger.info("scrapedthumbnail="+scrapedthumbnail)

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELNAME , "listsimple" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )
		
	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
		
	# Disable sorting...
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )
	
def buscaporanyo(params,url,category):
	logger.info("[peliculas21.py] buscaporanyo")
	#url = "http://www.peliculas21.com/%s/%s/"
	anho=2011
	anyoactual = anho
	anyoinic   = 1950
	opciones = []
	for i in range(anyoactual-anyoinic+1):
		opciones.append(str(anyoactual))
		anyoactual = anyoactual - 1           
	dia = xbmcgui.Dialog()
	seleccion = dia.select("Listar desde el Año: ", opciones)
	logger.info("seleccion=%d" % seleccion)
	if seleccion == -1 :return
	if seleccion == 0:
		url = "http://www.peliculas21.com/"+opciones[seleccion]+"/"+opciones[seleccion]+"/"
		listsimple(params,url,category)
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
		url = "http://www.peliculas21.com/"+desde+"/"+desde+"/"
		listsimple(params,url,category)
		return
	url = "http://www.peliculas21.com/"+desde+"/"+opciones2[seleccion2]+"/"
	listsimple(params,url,category)
	return	
