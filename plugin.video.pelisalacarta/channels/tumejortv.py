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

CHANNELNAME = "tumejortv"

# Esto permite su ejecución en modo emulado
try:
	pluginhandle = int( sys.argv[ 1 ] )
except:
	pluginhandle = ""

# Traza el inicio del canal
logger.info("[tumejortv.py] init")

DEBUG = True

def mainlist(params,url,category):
	logger.info("[tumejortv.py] mainlist")
	xbmctools.addnewfolder( CHANNELNAME , "newlist"        , CHANNELNAME , "Novedades" , "http://www.tumejortv.com/" , "", "" )
	xbmctools.addnewfolder( CHANNELNAME , "moviecategorylist" , CHANNELNAME , "Películas - Por categorías" , "http://www.tumejortv.com/" , "", "" )
	xbmctools.addnewfolder( CHANNELNAME , "moviealphalist" , CHANNELNAME , "Películas - Por orden alfabético" , "http://www.tumejortv.com/" , "", "" )
	xbmctools.addnewfolder( CHANNELNAME , "serienewlist"   , CHANNELNAME , "Series - Novedades" , "http://www.tumejortv.com/" , "", "" )
	xbmctools.addnewfolder( CHANNELNAME , "seriealllist"   , CHANNELNAME , "Series - Todas" , "http://www.tumejortv.com/" , "", "" )
	xbmctools.addnewfolder( CHANNELNAME , "seriealphalist" , CHANNELNAME , "Series - Por orden alfabético" , "http://www.tumejortv.com/" , "", "" )
	xbmctools.addnewfolder( CHANNELNAME , "search"         , CHANNELNAME , "Buscar" , "" , "", "" )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def search(params,url,category):
	logger.info("[tumejortv.py] search")

	keyboard = xbmc.Keyboard('')
	keyboard.doModal()
	if (keyboard.isConfirmed()):
		tecleado = keyboard.getText()
		if len(tecleado)>0:
			#convert to HTML
			tecleado = tecleado.replace(" ", "+")
			searchresults(params,tecleado)

'''
<h3>Pel&iacute;culas online</h3><ul class='alphaList'><li><div class="movieTitle">Avatar 3D [Spanish Line][2009]   - ...</div><div class="covershot"><a href="http://www.tumejortv.com/peliculas-online-es/accion/avatar-3d-spanish-line2009-dvd-rip-06-03-2010.html" title="Avatar 3D [Spanish Line][2009]   - DVD-RIP"><img src="http://imagenes.tumejortv.com/32888.jpg" alt="Avatar 3D [Spanish Line][2009]   - DVD-RIP"/></a></div></li>
<li><div class="movieTitle">Avatar [2CDs][Spanish ...</div><div class="covershot"><a href="http://www.tumejortv.com/peliculas-online-es/accion/avatar-2cdsspanish-line2009proper-dvd-rip-07-02-2010.html" title="Avatar [2CDs][Spanish Line][2009][Proper] - DVD-RIP"><img src="http://imagenes.tumejortv.com/29890.jpg" alt="Avatar [2CDs][Spanish Line][2009][Proper] - DVD-RIP"/></a></div></li>
<li><div class="movieTitle">Avatar [3CDs][Spanish Line][2009]     </div><div class="covershot"><a href="http://www.tumejortv.com/peliculas-online-es/accion/avatar-3cdsspanish-line2009-dvd-rip-05-02-2010.html" title="Avatar [3CDs][Spanish Line][2009]     "><img src="http://imagenes.tumejortv.com/29871.jpg" alt="Avatar [3CDs][Spanish Line][2009]     "/></a></div></li></ul><div class="wp-pagenavi">
<span class="pages">Página 1 de 1</span><span class="current">1</span></div>
<br style='clear: both;' /><br style='clear: both;' /><h3>Series online</h3><ul class='alphaList'><li><div class="movieTitle">Avatar La Leyenda de Aang</div><div class="covershot"><a href="http://www.tumejortv.com/series-tv-online/avatar-la-leyenda-de-aang" title="Avatar La Leyenda de Aang"><img src="http://imagenes.tumejortv.com/series/1978.jpg" alt="Avatar La Leyenda de Aang"/></a></div></li></ul><br style='clear: both;' />      </div>
'''

# Listado de novedades de la pagina principal
def searchresults(params,tecleado):
	logger.info("[tumejortv.py] searchresults")

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
	logger.info("[tumejortv.py] performsearch")
	url = "http://www.tumejortv.com/buscar/?s="+texto+"&x=0&y=0"
	
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
def newlist(params,url,category):
	logger.info("[tumejortv.py] movielist")

	# ------------------------------------------------------
	# Descarga la página
	# ------------------------------------------------------
	data = scrapertools.cachePage(url)
	#logger.info(data)

	# ------------------------------------------------------
	# Extrae las películas
	# ------------------------------------------------------
	patron  = '<div class="item " style="clear:both;">[^<]+'
	patron += '<div class="covershot[^<]+'
	patron += '<a href="([^"]+)"[^<]+<img src="([^"]+)"[^<]+</a>[^<]+'
	patron += '</div>[^<]+'
	patron += '<div class="post-title">[^<]+'
	patron += '<h3><a[^<]+>(.*?)</a>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	if DEBUG:
		scrapertools.printMatches(matches)

	for match in matches:
		scrapedtitle = match[2]
		scrapedtitle = scrapedtitle.replace("<span class=\'smallTitle'>","(")
		scrapedtitle = scrapedtitle.replace("</span>",")")
		scrapedurl = match[0]
		scrapedthumbnail = match[1]
		scrapedplot = ""
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELNAME , "detail" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# ------------------------------------------------------
	# Extrae la página siguiente
	# ------------------------------------------------------
	patron = '<a href="([^"]+)" >&raquo;</a>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	if DEBUG:
		scrapertools.printMatches(matches)

	if len(matches)>0:
		scrapedtitle = "!Pagina siguiente"
		scrapedurl = matches[0]
		scrapedthumbnail = ""
		scrapeddescription = ""
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELNAME , "newlist" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

# Listado de películas de una categoria / letra
def shortlist(params,url,category):
	logger.info("[tumejortv.py] shortlist")

	# ------------------------------------------------------
	# Descarga la página
	# ------------------------------------------------------
	data = scrapertools.cachePage(url)
	#logger.info(data)

	# ------------------------------------------------------
	# Extrae las películas
	# ------------------------------------------------------
	#<li><div class="movieTitle">Doraemon Y Los 7 Magos (2008) - DVD-RIP</div><div class="covershot"><a href="http://www.tumejortv.com/peliculas-online-es/infantiles/doraemon-y-los-7-magos-2008-dvd-rip-31-07-2009.html" title="Doraemon Y Los 7 Magos (2008) - DVD-RIP"><img src="http://imagenes.tumejortv.com//8098.jpg" alt="Doraemon Y Los 7 Magos (2008) - DVD-RIP"/></a></div></li>
	patron  = '<li><div class="movieTitle">[^<]+</div><div class="covershot">'
	patron += '<a href="([^"]+)" title="([^"]+)"><img src="([^"]+)"[^>]+></a></div></li>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	if DEBUG:
		scrapertools.printMatches(matches)

	for match in matches:
		scrapedtitle = match[1]
		scrapedurl = match[0]
		scrapedthumbnail = match[2]
		scrapedplot = ""
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELNAME , "detail" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# ------------------------------------------------------
	# Extrae la página siguiente
	# ------------------------------------------------------
	patron = '<a href="([^"]+)" >&raquo;</a>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	if DEBUG:
		scrapertools.printMatches(matches)

	if len(matches)>0:
		scrapedtitle = "!Pagina siguiente"
		scrapedurl = matches[0]
		scrapedthumbnail = ""
		scrapedplot = ""
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELNAME , "shortlist" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

# Listado de series de una letra
def shortlistserie(params,url,category):
	logger.info("[tumejortv.py] shortlistserie")

	# ------------------------------------------------------
	# Descarga la página
	# ------------------------------------------------------
	data = scrapertools.cachePage(url)
	#logger.info(data)

	# ------------------------------------------------------
	# Extrae las películas
	# ------------------------------------------------------
	#<li><div class="covershot"><a href="http://www.tumejortv.com/series-tv-online/abducidos-taken" title="Abducidos (Taken)"><img src="http://imagenes.tumejortv.com/series/157.jpg" alt="Abducidos (Taken)"/></a></div></li>
	patron  = '<li><div class="covershot"><a href="([^"]+)" title="([^"]+)"><img src="([^"]+)"[^>]+></a></div></li>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	if DEBUG:
		scrapertools.printMatches(matches)

	for match in matches:
		scrapedtitle = match[1]
		scrapedurl = match[0]
		scrapedthumbnail = match[2]
		scrapedplot = ""
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELNAME , "detailserie" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# ------------------------------------------------------
	# Extrae la página siguiente
	# ------------------------------------------------------
	patron = '<a href="([^"]+)" >&raquo;</a>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	if DEBUG:
		scrapertools.printMatches(matches)

	if len(matches)>0:
		scrapedtitle = "Pagina siguiente"
		scrapedurl = matches[0]
		scrapedthumbnail = ""
		scrapedplot = ""
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELNAME , "shortlist" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

# Listado de categorias de películas, de la caja derecha de la home
def moviecategorylist(params,url,category):
	
	logger.info("[tumejortv.py] moviecategorylist")

	# ------------------------------------------------------
	# Descarga la página
	# ------------------------------------------------------
	data = scrapertools.cachePage(url)
	#logger.info(data)

	# ------------------------------------------------------
	# Extrae las películas
	# ------------------------------------------------------
	#<li class="cat-item cat-item-94"><a href="http://www.tumejortv.com/peliculas-online-es/accion" title="Ver todas las entradas de Acción">Acción</a>
	patron  = '<li class="cat-item[^<]+<a href="(http\:\/\/www\.tumejortv\.com\/peliculas\-online\-es\/[^"]+)"[^>]+>([^<]+)</a>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	if DEBUG:
		scrapertools.printMatches(matches)

	for match in matches:
		scrapedtitle = match[1]
		scrapedurl = match[0]
		scrapedthumbnail = ""
		scrapedplot = ""
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELNAME , "shortlist" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

# Listado de letras iniciales de película, de la caja derecha de la home
def moviealphalist(params,url,category):
	
	logger.info("[tumejortv.py] moviealphalist")

	# ------------------------------------------------------
	# Descarga la página
	# ------------------------------------------------------
	data = scrapertools.cachePage(url)
	#logger.info(data)

	# ------------------------------------------------------

	# Extrae las películas
	# ------------------------------------------------------
	#<a href="http://www.tumejortv.com/peliculas-es-con-letra-a" title="Pel&iacute;culas - Es con la letra a" class="listados_letras">a</a> - 
	patron  = '<a href="(http\:\/\/www\.tumejortv\.com\/peliculas-es-con-letra-[^"]+)".*?class="listados_letras">([^<]+)</a>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	if DEBUG:
		scrapertools.printMatches(matches)

	for match in matches:
		scrapedtitle = match[1]
		scrapedurl = match[0]
		scrapedthumbnail = ""
		scrapedplot = ""
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELNAME , "shortlist" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

# Listado de letras iniciales de series, de la caja derecha de la home
def seriealphalist(params,url,category):
	
	logger.info("[tumejortv.py] seriealphalist")

	# ------------------------------------------------------
	# Descarga la página
	# ------------------------------------------------------
	data = scrapertools.cachePage(url)
	#logger.info(data)

	# ------------------------------------------------------
	# Extrae las películas
	# ------------------------------------------------------
	#<a href="http://www.tumejortv.com/series-con-letra-a" title="Series con la letra a" class="listados_letras">a</a>
	patron  = '<a href="(http\:\/\/www\.tumejortv\.com\/series-con-letra-[^"]+)".*?class="listados_letras">([^<]+)</a>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	if DEBUG:
		scrapertools.printMatches(matches)

	for match in matches:
		scrapedtitle = match[1]
		scrapedurl = match[0]
		scrapedthumbnail = ""
		scrapedplot = ""
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELNAME , "shortlistserie" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

# Listado de series actualizadas, de la caja derecha de la home
def serienewlist(params,url,category):
	
	logger.info("[tumejortv.py] serienewlist")

	# ------------------------------------------------------
	# Descarga la página
	# ------------------------------------------------------
	data = scrapertools.cachePage(url)
	#logger.info(data)

	# ------------------------------------------------------
	# Extrae las películas
	# ------------------------------------------------------
	#<span><a href="http://www.tumejortv.com/series-tv-online/ranma-%c2%bd/ranma-%c2%bd-temporada-1" title="Ranma ½"><img src="http://imagenes.tumejortv.com//series/948.jpg" alt="Ranma ½"  /></a></span>
	patron  = '<span><a href="([^"]+)" title="([^"]+)"><img src="([^"]+)".*?</span>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	if DEBUG:
		scrapertools.printMatches(matches)

	for match in matches:
		scrapedtitle = match[1]
		scrapedurl = match[0]
		scrapedthumbnail = match[2]
		scrapedplot = ""
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELNAME , "detailserie" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

# Listado de todas las series, de la caja derecha de la home
def seriealllist(params,url,category):
	
	logger.info("[tumejortv.py] seriealllist")

	# ------------------------------------------------------
	# Descarga la página
	# ------------------------------------------------------
	data = scrapertools.cachePage(url)
	#logger.info(data)

	# ------------------------------------------------------
	# Extrae las películas
	# ------------------------------------------------------
	#<li class='cat-item cat-item-1929'><a href='http://www.tumejortv.com/series-tv-online/2-de-mayo' title='Todas las temporadas de 2 de Mayo'>2 de Mayo</a></li>

	patron  = "<li class='cat-item[^<]+<a href='(http\:\/\/www\.tumejortv\.com\/series\-tv\-online\/[^']+)'[^>]+>([^<]+)</a></li>"
	matches = re.compile(patron,re.DOTALL).findall(data)
	if DEBUG:
		scrapertools.printMatches(matches)

	for match in matches:
		scrapedtitle = match[1]
		scrapedurl = match[0]
		scrapedthumbnail = ""
		scrapedplot = ""
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELNAME , "detailserie" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

# Detalle de un vídeo (peli o capitulo de serie), con los enlaces
def detail(params,url,category):
	logger.info("[tumejortv.py] detail")

	title = urllib.unquote_plus( params.get("title") )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = ""

	# Descarga la página
	data = scrapertools.cachePage(url)
	#logger.info(data)

	patron = '<div id="blogitem">[^<]+<p>([^<]+)</p>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	if len(matches)>0:
		plot = matches[0]

	listavideos = servertools.findvideos(data)
	
	for video in listavideos:
		xbmctools.addnewvideo( CHANNELNAME , "play" , CHANNELNAME , video[2] , title + " (" + video[2] + ")" , video[1] , thumbnail, plot )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

# Detalle de una serie, con sus capítulos
def detailserie(params,url,category):
	logger.info("[tumejortv.py] detailserie")

	title = urllib.unquote_plus( params.get("title") )

	# ------------------------------------------------------
	# Descarga la página
	# ------------------------------------------------------
	data = scrapertools.cachePage(url)
	#logger.info(data)

	# ------------------------------------------------------
	#<ul class="linksListados">
	#<li><a href="http://www.tumejortv.com/series-tv-online/babylon-5/babylon-5-temporada-1/capitulo-122-15-15-04-2009.html">Babylon 5, Babylon 5 Temporada 1, Capitulo 122</a></li>
	patron  = '<ul class="linksListados">(.*?)</ul>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	if DEBUG:
		scrapertools.printMatches(matches)

	for match in matches:
		patron2 = '<li><a href="([^"]+)"[^>]+>([^<]+)</a></li>'
		matches2 = re.compile(patron2,re.DOTALL).findall(match)
		if DEBUG:
			scrapertools.printMatches(matches2)

		for match2 in matches2:
			scrapedtitle = match2[1]
			scrapedtitle = scrapedtitle.replace("Temporada ","")
			scrapedtitle = scrapedtitle.replace(", Capitulo ","x")
			scrapedtitle = scrapedtitle.replace("&#215;","x")

			if scrapedtitle.startswith(title+", "):
				scrapedtitle = scrapedtitle[ len(title)+2 : ]
			
			scrapedurl = match2[0]
			scrapedthumbnail = ""
			scrapedplot = ""

			# Depuracion
			if DEBUG:
				logger.info("scrapedtitle="+scrapedtitle)
				logger.info("scrapedurl="+scrapedurl)
				logger.info("scrapedthumbnail="+scrapedthumbnail)
				logger.info("scrapedplot="+scrapedplot)

			# Añade al listado de XBMC
			xbmctools.addnewfolder( CHANNELNAME , "detail" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

# Reproducir un vídeo
def play(params,url,category):
	logger.info("[tumejortv.py] play")

	title = urllib.unquote_plus( params.get("title") )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = urllib.unquote_plus( params.get("plot") )
	server = urllib.unquote_plus( params.get("server") )

	xbmctools.playvideo(CHANNELNAME,server,url,category,title,thumbnail,plot)
