# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para tumejortv
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
import buscador

CHANNELNAME = "descargapelis"

# Esto permite su ejecución en modo emulado
try:
	pluginhandle = int( sys.argv[ 1 ] )
except:
	pluginhandle = ""

# Traza el inicio del canal
logger.info("[descargapelis.py] init")

DEBUG = True

def mainlist(params,url,category):
	logger.info("[descargapelis.py] mainlist")
	xbmctools.addnewfolder( CHANNELNAME , "newlist"        , CHANNELNAME , "Nuevas incorporaciones" , "http://www.descargapelis.net/" , "", "" )
	xbmctools.addnewfolder( CHANNELNAME , "moviecategorylist" , CHANNELNAME , "Películas - Por categorías" , "http://www.descargapelis.net/" , "", "" )
	xbmctools.addnewfolder( CHANNELNAME , "moviealphalist" , CHANNELNAME , "Películas - Por orden alfabético" , "http://www.descargapelis.net/" , "", "" )
	xbmctools.addnewfolder( CHANNELNAME , "estrenos"   , CHANNELNAME , "Películas de estreno" , "http://www.descargapelis.net/estreno.php" , "", "" )
	xbmctools.addnewfolder( CHANNELNAME , "hayquever"   , CHANNELNAME , "Películas que hay que ver" , "http://www.descargapelis.net/estreno.php" , "", "" )
	xbmctools.addnewfolder( CHANNELNAME , "recomendadas" , CHANNELNAME , "Recomendadas" , "http://www.descargapelis.net/recomendadas.php" , "", "" )
	#xbmctools.addnewfolder( CHANNELNAME , "search"         , CHANNELNAME , "Buscar" , "" , "", "" )
	#el buscador es una ruina, usa google para funcionar
	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def search(params,url,category):
	logger.info("[descargapelis.py] search")

	buscador.listar_busquedas(params,url,category)
	
	

# Listado de novedades de la pagina principal
def searchresults(params,tecleado,category):
	logger.info("[descargapelis.py] searchresults")
	
	buscador.salvar_busquedas(params,tecleado,category)
	resultados = performsearch(tecleado)

	for match in resultados:
		targetchannel = match[0]
		action = match[1]
		category = match[2]
		scrapedtitle = match[3]
		scrapedurl = match[4]
		scrapedthumbnail = match[5]
		scrapedplot = match[6]
		
		# Añade al listado de XBMC
		xbmctools.addnewfolder( targetchannel , action , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def performsearch(texto):
	logger.info("[descargapelis.py] performsearch")
	url = "http://www.descargapelis.net/buscar/?s="+texto+"&x=0&y=0"
	
	# ------------------------------------------------------
	# Descarga la página
	# ------------------------------------------------------
	resultados = []
	data = scrapertools.cachePage(url)
	#logger.info(data)

	# ------------------------------------------------------
	# Extrae las películas
	# ------------------------------------------------------
	patron  = "<h3>Pel.iacute.culas online</h3><ul class='alphaList'>(.*?)</ul>"
	matches = re.compile(patron,re.DOTALL).findall(data)
	if DEBUG: scrapertools.printMatches(matches)
	data2 = ""
	if len(matches)>0:
		data2 = matches[0]
	
	patron  = '<li><div class="movieTitle">[^<]+</div><div class="covershot"><a href="([^"]+)" title="([^"]+)"><img src="([^"]+)"'
	matches = re.compile(patron,re.DOTALL).findall(data2)
	if DEBUG: scrapertools.printMatches(matches)

	for match in matches:
		scrapedtitle = match[1]
		scrapedurl = match[0]
		scrapedthumbnail = match[2]
		scrapedplot = ""
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")
		
		# Añade al listado de XBMC
		resultados.append( [CHANNELNAME , "detail" , "buscador" , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot ] )

	# ------------------------------------------------------
	# Extrae las películas
	# ------------------------------------------------------
	patron  = "<h3>Series online</h3><ul class='alphaList'>(.*?)</ul>"
	matches = re.compile(patron,re.DOTALL).findall(data)
	if DEBUG: scrapertools.printMatches(matches)
	if len(matches)>0:
		data2 = matches[0]
	
	patron  = '<li><div class="movieTitle">[^<]+</div><div class="covershot"><a href="([^"]+)" title="([^"]+)"><img src="([^"]+)"'
	matches = re.compile(patron,re.DOTALL).findall(data2)
	if DEBUG: scrapertools.printMatches(matches)

	for match in matches:
		scrapedtitle = match[1]
		scrapedurl = match[0]
		scrapedthumbnail = match[2]
		scrapedplot = ""
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")
		
		# Añade al listado de XBMC
		resultados.append( [CHANNELNAME , "detailserie" , "buscador" , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot ] )

	return resultados

# Listado de novedades de la pagina principal

def recomendadas(params,url,category):
	logger.info("[descargapelis.py] movielist")
	logger.info(category)
	data = scrapertools.cachePage(url)
	if (category == "descargapelis") :
		#xbmctools.addnewfolder( CHANNELNAME , "recomendadas" , "todas" , "Todas" , url , "todas", "" )
		xbmctools.addnewfolder( CHANNELNAME , "recomendadas" , "todas" , "Todas" , url , "", "" )


		patron  = 'PELICULAS DE .+?>(.+?)</a>'
	#<td align="center" colspan="3" height="25" class="titulo_peli"><a title="megaupload peliculas descarga directa español" href="p408noche-y-dia.php" class="titulo_peli">Noche y dia<br /><br /><img class="foto_prin" src="http://www.bestwebmaker.com/blog/wp-content/uploads/2010/08/Noche-Y-Dia-2010.jpg" width="135" height="195" alt="Noche y dia descarga directa megaupload" title="Noche y dia" /><br /><br /></a></td>
				#class="titulo_peli"><a href="p404origen-inception.php" class="titulo_peli">Origen Inception</a></td>
	#xbmc.output(url + "es la url")
	#url=url[0:url.index(".net/")+5]


	#patron += '<div class="covershot[^<]+'
	#patron += '<a href="([^"]+)"[^<]+<img src="([^"]+)"[^<]+</a>[^<]+'
	#patron += '</div>[^<]+'
	#patron += '<div class="post-title">[^<]+'
	#patron += '<h3><a[^<]+>(.*?)</a>'
		matches = re.compile(patron,re.DOTALL).findall(data)
		if DEBUG:
			scrapertools.printMatches(matches)

		for match in matches:
			xbmctools.addnewfolder( CHANNELNAME , "recomendadas" , match , match , url , "", "" )
	else:
		url=url[0:url.index(".net/")+5]
		if category != "todas":
			data=data[data.index(category):data.index("PHP***",data.index(category))]
			logger.info(data)
			
		patron  = '<td align=".+?" colspan="\d+" valign="top" height="\d+" width="\d+"><a href="(.+?)" class="titulo_peli"><img class="foto_prin" width="\d+" height="\d+" src="(.+?)" title="(.+?)"'
		matches = re.compile(patron,re.DOTALL).findall(data)
		if len(matches) > 0 :
			for match in matches:
			
			#scrapedtitle = match[1]
			#scrapedtitle = scrapedtitle.replace("<span class=\'smallTitle'>","(")
			#scrapedtitle = scrapedtitle.replace("</span>",")")
			#scrapedurl = url + match[0]
			
			#scrapedthumbnail = ""
			#scrapedplot = match[1]
			#if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")
	
			# Añade al listado de XBMC
				xbmctools.addnewfolder( CHANNELNAME , "detail" , category , match[2] ,url + match[0] , match[1], "" )

	# ------------------------------------------------------
	# Extrae la página siguiente
	# ------------------------------------------------------
	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )



def estrenos(params,url,category):
	logger.info("[descargapelis.py] movielist")

	# ------------------------------------------------------
	# Descarga la página
	# ------------------------------------------------------
	data = scrapertools.cachePage(url)
	data=data[data.index("PELICULAS DE ESTRENO"):data.index("</table>",data.index("PELICULAS DE ESTRENO"))]
	logger.info(data)
	#data = data[data.index("PHP"):]
	# ------------------------------------------------------
	# Extrae las películas
	# ------------------------------------------------------
	#<td colspan="3" height="25" class="titulo_peli"><a href="p43el-valiente-despereaux.php" class="titulo_peli">El valiente Despereaux</a></td>
#<td colspan="3" height="25" class="titulo_peli"><a title="Los tres entierros de Melquiades Estrada" href="p416los-tres-entierros-de-melquiades-estrada.php" class="titulo_peli">Los tres entierros de Melquiades Estrada (drama)</a></td>

	patron  = 'colspan="3" height="25" class="titulo_peli"><a[^<]+?href="(.+?php)" class="titulo_peli">([^<]+?)<br />.+?src="(.+?)".+?</a>'
	#<td align="center" colspan="3" height="25" class="titulo_peli"><a title="megaupload peliculas descarga directa español" href="p408noche-y-dia.php" class="titulo_peli">Noche y dia<br /><br /><img class="foto_prin" src="http://www.bestwebmaker.com/blog/wp-content/uploads/2010/08/Noche-Y-Dia-2010.jpg" width="135" height="195" alt="Noche y dia descarga directa megaupload" title="Noche y dia" /><br /><br /></a></td>
				#class="titulo_peli"><a href="p404origen-inception.php" class="titulo_peli">Origen Inception</a></td>
	#xbmc.output(url + "es la url")
	url=url[0:url.index(".net/")+5]


	#patron += '<div class="covershot[^<]+'
	#patron += '<a href="([^"]+)"[^<]+<img src="([^"]+)"[^<]+</a>[^<]+'
	#patron += '</div>[^<]+'
	#patron += '<div class="post-title">[^<]+'
	#patron += '<h3><a[^<]+>(.*?)</a>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	if DEBUG:
		scrapertools.printMatches(matches)

	for match in matches:
		scrapedtitle = match[1]
		#scrapedtitle = scrapedtitle.replace("<span class=\'smallTitle'>","(")
		#scrapedtitle = scrapedtitle.replace("</span>",")")
		scrapedurl = url + match[0]
		
		scrapedthumbnail = ""
		scrapedplot = match[1]
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELNAME , "detail" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# ------------------------------------------------------
	# Extrae la página siguiente
	# ------------------------------------------------------
	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )


def hayquever(params,url,category):
	logger.info("[descargapelis.py] movielist")

	# ------------------------------------------------------
	# Descarga la página
	# ------------------------------------------------------
	data = scrapertools.cachePage(url)
	data=data[data.index("PELICULAS QUE HAY QUE VER"):data.index("</table>",data.index("PELICULAS QUE HAY QUE VER"))]
	logger.info(data)
	#data = data[data.index("PHP"):]
	# ------------------------------------------------------
	# Extrae las películas
	# ------------------------------------------------------
	#<td colspan="3" height="25" class="titulo_peli"><a href="p43el-valiente-despereaux.php" class="titulo_peli">El valiente Despereaux</a></td>
#<td colspan="3" height="25" class="titulo_peli"><a title="Los tres entierros de Melquiades Estrada" href="p416los-tres-entierros-de-melquiades-estrada.php" class="titulo_peli">Los tres entierros de Melquiades Estrada (drama)</a></td>

	patron  = 'colspan="3".+?height="25" class="titulo_peli"><a[^<]+?href="(.+?php)" class="titulo_peli">([^<]+?)<br />.+?src="(.+?)".+?</a>'
	#<td colspan="3" align="center" height="25" class="titulo_peli"><a title="descargar peliculas megaupload español" href="p92rockanrolla.php" class="titulo_peli">Rock n rolla<br /><br /><img class="foto_prin" src="http://www.fersvideo.com.ar/Peliculas_Imagen/1252247713_rocknrolla.jpg" width="135" height="195" alt="Rock n rolla megaupload descarga directa" /><br /><br /></a></td>
	#<td align="center" colspan="3" height="25" class="titulo_peli"><a title="megaupload peliculas descarga directa español" href="p408noche-y-dia.php" class="titulo_peli">Noche y dia<br /><br /><img class="foto_prin" src="http://www.bestwebmaker.com/blog/wp-content/uploads/2010/08/Noche-Y-Dia-2010.jpg" width="135" height="195" alt="Noche y dia descarga directa megaupload" title="Noche y dia" /><br /><br /></a></td>
				#class="titulo_peli"><a href="p404origen-inception.php" class="titulo_peli">Origen Inception</a></td>
	#xbmc.output(url + "es la url")
	url=url[0:url.index(".net/")+5]


	#patron += '<div class="covershot[^<]+'
	#patron += '<a href="([^"]+)"[^<]+<img src="([^"]+)"[^<]+</a>[^<]+'
	#patron += '</div>[^<]+'
	#patron += '<div class="post-title">[^<]+'
	#patron += '<h3><a[^<]+>(.*?)</a>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	if DEBUG:
		scrapertools.printMatches(matches)

	for match in matches:
		scrapedtitle = match[1]
		#scrapedtitle = scrapedtitle.replace("<span class=\'smallTitle'>","(")
		#scrapedtitle = scrapedtitle.replace("</span>",")")
		scrapedurl = url + match[0]
		
		scrapedthumbnail = ""
		scrapedplot = match[1]
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELNAME , "detail" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# ------------------------------------------------------
	# Extrae la página siguiente
	# ------------------------------------------------------
	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )


def newlist(params,url,category):
	logger.info("[descargapelis.py] movielist")

	# ------------------------------------------------------
	# Descarga la página
	# ------------------------------------------------------
	data = scrapertools.cachePage(url)
	#logger.info(data)
	#data = data[data.index("PHP"):]
	# ------------------------------------------------------
	# Extrae las películas
	# ------------------------------------------------------
	#<td colspan="3" height="25" class="titulo_peli"><a href="p43el-valiente-despereaux.php" class="titulo_peli">El valiente Despereaux</a></td>
#<td colspan="3" height="25" class="titulo_peli"><a title="Los tres entierros de Melquiades Estrada" href="p416los-tres-entierros-de-melquiades-estrada.php" class="titulo_peli">Los tres entierros de Melquiades Estrada (drama)</a></td>

	patron  = '<td colspan="3" height="25" class="titulo_peli"><a[^<]+?href="(.+?php)" class="titulo_peli">([^<]+?)</a>'
				#class="titulo_peli"><a href="p404origen-inception.php" class="titulo_peli">Origen Inception</a></td>
	xbmc.output(url + "es la url")
	url=url[0:url.index(".net/")+5]


	#patron += '<div class="covershot[^<]+'
	#patron += '<a href="([^"]+)"[^<]+<img src="([^"]+)"[^<]+</a>[^<]+'
	#patron += '</div>[^<]+'
	#patron += '<div class="post-title">[^<]+'
	#patron += '<h3><a[^<]+>(.*?)</a>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	if DEBUG:
		scrapertools.printMatches(matches)

	for match in matches:
		scrapedtitle = match[1]
		#scrapedtitle = scrapedtitle.replace("<span class=\'smallTitle'>","(")
		#scrapedtitle = scrapedtitle.replace("</span>",")")
		scrapedurl = url + match[0]
		
		scrapedthumbnail = ""
		scrapedplot = match[1]
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELNAME , "detail" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# ------------------------------------------------------
	# Extrae la página siguiente
	# ------------------------------------------------------
	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )


# Listado de categorias de películas, de la caja derecha de la home
def moviecategorylist(params,url,category):
	
	logger.info("[descargapelis.py] moviecategorylist")

	# ------------------------------------------------------
	# Descarga la página
	# ------------------------------------------------------
	data = scrapertools.cachePage(url)
	#logger.info(data)

	# ------------------------------------------------------
	# Extrae las películas
	# ------------------------------------------------------
	#<li class="cat-item cat-item-94"><a href="http://www.descargapelis.net/peliculas-online-es/accion" title="Ver todas las entradas de Acción">Acción</a>
	patron  = '<a class="menu_cat" href="(cat_.+?)">-?(.+?)</a>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	if DEBUG:
		scrapertools.printMatches(matches)

	for match in matches:
		scrapedtitle = match[1]
		scrapedurl = url + match[0]
		scrapedthumbnail = ""
		scrapedplot = ""
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELNAME , "newlist" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

# Listado de letras iniciales de película, de la caja derecha de la home
def moviealphalist(params,url,category):
	
	logger.info("[descargapelis.py] moviealphalist")

	# ------------------------------------------------------
	# Descarga la página
	# ------------------------------------------------------
	data = scrapertools.cachePage(url)
	#logger.info(data)

	# ------------------------------------------------------

	# Extrae las películas
	# ------------------------------------------------------
	#<a href="http://www.descargapelis.net/peliculas-es-con-letra-a" title="Pel&iacute;culas - Es con la letra a" class="listados_letras">a</a> - 
	patron  = '<a class="listado_alfabetico" href="(alfa(.)\.php)"'
	matches = re.compile(patron,re.DOTALL).findall(data)
	if DEBUG:
		scrapertools.printMatches(matches)

	for match in matches:
		scrapedtitle = match[1]
		scrapedurl = url + match[0]
		scrapedthumbnail = ""
		scrapedplot = ""
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELNAME , "newlist" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

# Listado de letras iniciales de series, de la caja derecha de la home

# Detalle de un vídeo (peli o capitulo de serie), con los enlaces
def detail(params,url,category):
	logger.info("[descargapelis.py] detail")

	title = urllib.unquote_plus( params.get("title") )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = ""

	# Descarga la página
	data = scrapertools.cachePage(url)
	#logger.info(data)

	patron = '<table width="100%" cellpadding="0" cellspacing="0">[^<]+?'
	patron +='<tr>[^<]+?<td align="center"><img src="(.+?)".+?'
	patron +='<td align="justify" valign="top" class="texto_peli"><b>Sinopsis de (.+?):</b>(.+?)<br />'
	matches = re.compile(patron,re.DOTALL).findall(data)
	if len(matches)>0:
		if DEBUG:
			scrapertools.printMatches(matches)
			#xbmc.output('test')

	listavideos = servertools.findvideos(data)
	thumbnail=matches[0][0]
	plot=matches[0][2]
	title=matches[0][1]
	for video in listavideos:
		xbmctools.addnewvideo( CHANNELNAME , "play" , CHANNELNAME , video[2] , title + " (" + video[2] + ")" , video[1] , thumbnail, plot )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

# Reproducir un vídeo
def play(params,url,category):
	logger.info("[descargapelis.py] play")

	title = urllib.unquote_plus( params.get("title") )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = urllib.unquote_plus( params.get("plot") )
	server = urllib.unquote_plus( params.get("server") )

	xbmctools.playvideo(CHANNELNAME,server,url,category,title,thumbnail,plot)
