# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# tvalacarta - XBMC Plugin
# Canal para hogarutil.com
# http://blog.tvalacarta.info/plugin-xbmc/tvalacarta/
#------------------------------------------------------------
#
# TODO patronvideos  = '"paramVideoPubli", "([^"]+)"'
#

import urlparse,urllib2,urllib,re
import os
import sys
import xbmc
import xbmcgui
import xbmcplugin
import scrapertools
import binascii
import logger

try:
	pluginhandle = int( sys.argv[ 1 ] )
except:
	pluginhandle = ""

logger.info("[hogarutil.py] init")

DEBUG = True
CHANNELNAME = "hogarutil.com"
CHANNELCODE = "hogarutil"

def mainlist(params,url,category):
	logger.info("[hogarutil.py] mainlist")

	# Añade al listado de XBMC
	addfolder("Cocina","http://www.hogarutil.com/Cocina/Recetas+en+v%C3%ADdeo","videococinalist")
	addfolder("Bricolaje","http://www.hogarutil.com/Bricomania/Trabajos+en+v%C3%ADdeo","videobricolajelist")
	addfolder("Decoración","http://www.hogarutil.com/Decogarden/Trabajos+en+v%C3%ADdeo","videobricolajelist")
	addfolder("Jardineria","http://www.hogarutil.com/Jardineria/Trabajos+en+v%C3%ADdeo","videobricolajelist")
	addfolder("Buscar","","search")
	#addvideodirecto("¡En directo!","rtmp://aialanetlivefs.fplive.net/aialanetlive-live/hogarutil","")

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def search(params,url,category):
	logger.info("[hogarutil.py] search")

	keyboard = xbmc.Keyboard('')
	keyboard.doModal()
	if (keyboard.isConfirmed()):
		tecleado = keyboard.getText()
		if len(tecleado)>0:
			#convert to HTML
			tecleado = tecleado.replace(" ", "+")
			searchUrl = "http://www.hogarutil.com/fwk_googleminitools/GoogleServlet?tipoBusqueda=cabecera&cadenaABuscar="+urllib.quote_plus("vídeo "+tecleado)+"&siteDondeBuscar=&urlBuscador=http%3A%2F%2Fwww.hogarutil.com%2Fportal%2Fsite%2FPortalUtil%2Fmenuitem.c4c49aecb2a32733c4a69810843000a0"
			#searchUrl = "http://www.hogarutil.com/portal/site/PortalUtil/menuitem.c4c49aecb2a32733c4a69810843000a0?cadenaABuscarCabecera="+tecleado+"&cadenaABuscar="+tecleado
			searchresults(params,searchUrl,category)

def searchresults(params,url,category):
	logger.info("[hogarutil.py] searchresults")

	# Descarga la página
	data = scrapertools.cachePage(url)
	#logger.info(data)

	# Extrae las entradas (carpetas)
	#<li><font size="-2"><b></b></font> <a href="http://www.hogarutil.com/Jardineria/Trabajos+en+v%C3%ADdeo/Palmera+de+Roebelen?q=palmera&start=0&urlBuscador=http://www.hogarutil.com/portal/site/PortalUtil/menuitem.c4c49aecb2a32733c4a69810843000a0&site=Delivery"><span>Palmera de Roebelen</span></a>
	patronvideos  = '<li[^>]+><font size="-2"><b></b></font> <a href="([^\?]+)\?[^"]+"><span>([^<]+)</span></a>'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	for match in matches:
		scrapedtitle = match[1]
		scrapedurl = match[0]
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")
			
		if scrapedurl.find("Trabajos+en+v%C3%ADdeo")!=-1 or scrapedurl.find("Recetas+en+v%C3%ADdeo")!=-1:
			addvideo( scrapedtitle , scrapedurl , category )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )


def videococinalist(params,url,category):
	logger.info("[hogarutil.py] videolist")

	if (params.has_key("baseurl")):
		baseurl = urllib.unquote_plus( params.get("baseurl") )
	else:
		baseurl = url
	logger.info("[hogarutil.py] baseurl="+baseurl)

	# Descarga la página
	data = scrapertools.cachePage(url)
	#logger.info(data)

	# Extrae el enlace a la página siguiente
	#<span style="color:white" class="pagActual">2</span><a onmouseout="javascript:setDefaultColor(this);" onmouseover="javascript:setWhiteColor(this);" style="color:#5C758C; font-weight:normal;" href="?vgnextoid=550c8fc16b4bd110VgnVCM100000720d1ec2RCRD&vgnextrefresh=1&nextItem=40" class="pagRef">3</a>
	#patronvideos  = '<a.*?href="([^"]+)"[^>]+> siguiente'
	patronvideos = '<span.*?class="pagActual">[^<]+</span><a.*?href="([^"]+)".*?>([^<]+)</a>'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	for match in matches:
		scrapedtitle = "Ir a página "+match[1]
		scrapedurl = baseurl+match[0]
		scrapedthumbnail = ""

		# Depuracion
		if (DEBUG):
			logger.info("scrapedtitle="+scrapedtitle)
			logger.info("scrapedurl="+scrapedurl)
			logger.info("scrapedthumbnail="+scrapedthumbnail)

		# Añade al listado de XBMC
		addpagina( scrapedtitle , scrapedurl , baseurl , "videococinalist" )

	# Extrae las entradas (carpetas)
	#patronvideos  = '<li(?: class="par")?><a href="(/[^/]+/Trabajos\+en\+v[^"]+)">([^<]+)<'
	#patronvideos = '<li><span style="text-align:left; width:165px; margin-right:1px;" class="floatright"><img style="float:right;" src="/staticFiles/logo-hogarutil-video.gif"/>Karlos Arguiñano</span><a title="Bacalao fresco con puerros y vinagreta de sepia" href="/Cocina/Recetas+en+v%C3%ADdeo/Bacalao+fresco+con+puerros+y+vinagreta+de+sepia">Bacalao fresco con puerros y vinagreta de...</a></li>'
	#<li class="par"><span style="text-align:left; width:165px; margin-right:1px;" class="floatright"><img style="float:right;" src="/staticFiles/logo-hogarutil-video.gif"/>Karlos Arguiñano</span><a title="Acelgas guisadas en hojaldre" href="/Cocina/Recetas+en+v%C3%ADdeo/Acelgas+guisadas+en+hojaldre">Acelgas guisadas en hojaldre</a></li><li><span style="text-align:left; width:165px; margin-right:1px;" class="floatright"><img style="float:right;" src="/staticFiles/logo-hogarutil-video.gif"/>Karlos Arguiñano</span><a title="Albóndigas a la jardinera" href="/Cocina/Recetas+en+v%C3%ADdeo/Alb%C3%B3ndigas+a+la+jardinera">Albóndigas a la jardinera</a></li>
	patronvideos = '<li.*?><span[^>]+><img.*?src="/staticFiles/logo-hogarutil-video.gif"[^>]+>([^<]+)</span><a title="([^"]+)" href="([^"]+)">[^<]+</a></li>'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	for match in matches:
		# Titulo
		scrapedtitle = match[1]+" ("+match[0]+")"
		try:
			scrapedtitle = unicode( scrapedtitle, "utf-8" ).encode("iso-8859-1")
		except:
			pass

		# URL
		scrapedurl = urlparse.urljoin("http://www.hogarutil.com",urllib.quote(match[2]))
		
		# Thumbnail
		scrapedthumbnail = ""
		
		# procesa el resto
		scrapeddescription = ""

		# Depuracion
		if (DEBUG):
			logger.info("scrapedtitle="+scrapedtitle)
			logger.info("scrapedurl="+scrapedurl)
			logger.info("scrapedthumbnail="+scrapedthumbnail)

		# Añade al listado de XBMC
		addvideo( scrapedtitle , scrapedurl , category )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )

	# Disable sorting...
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def videobricolajelist(params,url,category):
	logger.info("[hogarutil.py] videolist")

	if (params.has_key("baseurl")):
		baseurl = urllib.unquote_plus( params.get("baseurl") )
	else:
		baseurl = url

	# Descarga la página
	data = scrapertools.cachePage(url)
	#logger.info(data)
	
	# Extrae el enlace a la página siguiente
	#<span style="color:white" class="pagActual">2</span><a onmouseout="javascript:setDefaultColor(this);" onmouseover="javascript:setWhiteColor(this);" style="color:#5C758C; font-weight:normal;" href="?vgnextoid=550c8fc16b4bd110VgnVCM100000720d1ec2RCRD&vgnextrefresh=1&nextItem=40" class="pagRef">3</a>
	#patronvideos  = '<a.*?href="([^"]+)"[^>]+> siguiente'
	#patronvideos = '<span.*?class="pagActual">[^<]+</span><a.*?href="([^"]+)".*?>([^<]+)</a>'
	patronvideos = '<span.*?class="pagActual">[^<]+</span><a.*?href="([^"]+)".*?>([^<]+)</a>'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	for match in matches:
		scrapedtitle = "Ir a página "+match[1]
		scrapedurl = baseurl+match[0]
		scrapedthumbnail = ""

		# Depuracion
		if (DEBUG):
			logger.info("scrapedtitle="+scrapedtitle)
			logger.info("scrapedurl="+scrapedurl)
			logger.info("scrapedthumbnail="+scrapedthumbnail)

		# Añade al listado de XBMC
		addpagina( scrapedtitle , scrapedurl , baseurl , "videobricolajelist" )

	# Extrae las entradas (carpetas)
	#<li class="par"><span class="floatrightVideo"><img src="/staticFiles/logo-hogarutil-video.gif"/></span><a href="/Bricomania/Trabajos+en+v%C3%ADdeo/Actualizar+mueble+cl%C3%A1sico">Actualizar mueble clásico</a></li><li><span class="floatrightVideo"><img src="/staticFiles/logo-hogarutil-video.gif"/></span><a href="/Bricomania/Trabajos+en+v%C3%ADdeo/Ahorro+consumo+de+ducha">Ahorro consumo de ducha</a></li><li class="par"><span class="floatrightVideo"><img src="/staticFiles/logo-hogarutil-video.gif"/></span><a href="/Bricomania/Trabajos+en+v%C3%ADdeo/Ahorro+energ%C3%A9tico">Ahorro energético</a></li>
	#<li class="par"><span class="floatrightVideo"><img src="/staticFiles/logo-hogarutil-video.gif"/></span><a href="/Bricomania/Trabajos+en+v%C3%ADdeo/Asiento+para+ba%C3%B1era">Asiento para bañera</a></li><li><span class="floatrightVideo"><img src="/staticFiles/logo-hogarutil-video.gif"/></span><a href="/Bricomania/Trabajos+en+v%C3%ADdeo/Balda+decorativa+infantil">Balda decorativa infantil</a></li><li class="par"><span class="floatrightVideo"><img src="/staticFiles/logo-hogarutil-video.gif"/></span><
	patronvideos = '<li.*?><span.*?><img src="/staticFiles/logo-hogarutil-video.gif"/></span><a href="([^"]+)">([^<]+)</a></li>'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	for match in matches:
		# Titulo
		scrapedtitle = match[1]
		try:
			scrapedtitle = unicode( scrapedtitle, "utf-8" ).encode("iso-8859-1")
		except:
			pass

		# URL
		scrapedurl = urlparse.urljoin("http://www.hogarutil.com",urllib.quote(match[0]))
		
		# Thumbnail
		scrapedthumbnail = ""
		
		# procesa el resto
		scrapeddescription = ""

		# Depuracion
		if (DEBUG):
			logger.info("scrapedtitle="+scrapedtitle)
			logger.info("scrapedurl="+scrapedurl)
			logger.info("scrapedthumbnail="+scrapedthumbnail)

		# Añade al listado de XBMC
		addvideo( scrapedtitle , scrapedurl , category )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )

	# Disable sorting...
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def play(params,url,category):
	logger.info("[hogarutil.py] play")

	logger.info("url="+url)
	infotitle = unicode( xbmc.getInfoLabel( "ListItem.Title" ), "utf-8" )
	#logger.info("[hogarutil.py] infotitle="+infotitle)
	
	# Abre dialogo
	dialogWait = xbmcgui.DialogProgress()
	dialogWait.create( 'Descargando datos del vídeo...', infotitle )

	# Averigua la descripcion (plot)
	data = scrapertools.cachePage(url)
	patronvideos = '<meta name="BNT_RECETA_DESC" content="([^"]+)" />'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)
	try:
		infoplot = matches[0]
	except:
		infoplot = ""
	logger.info("[hogarutil.py] infoplot="+infoplot)

	# Averigua el thumbnail
	patronvideos = '<img class="fotoreceta" alt="[^"]*" src="([^"]+)"/>'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)
	try:
		infothumbnail = scrapedurl = urlparse.urljoin("http://www.hogarutil.com",urllib.quote(matches[0]))
	except:
		infothumbnail = ""
	logger.info("[hogarutil.py] infothumbnail="+infothumbnail)

	# Averigua la URL del video
	patronvideos = '\&urlVideo=([^\&]+)\&'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)
	try:
		mediaurl = matches[0]
	except:
		mediaurl = ""
	logger.info("[hogarutil.py] mediaurl="+mediaurl)

	# Playlist vacia
	playlist = xbmc.PlayList( xbmc.PLAYLIST_VIDEO )
	playlist.clear()

	# Crea la entrada y la añade al playlist
	listitem = xbmcgui.ListItem( infotitle, iconImage="DefaultVideo.png", thumbnailImage=infothumbnail )
	listitem.setProperty("SWFPlayer", "http://www.hogarutil.com/staticFiles/static/player/BigBainetPlayer.swf")
	listitem.setInfo( "video", { "Title": infotitle, "Plot" : infoplot , "Studio" : CHANNELNAME , "Genre" : category } )
	playlist.add( mediaurl, listitem )
	#xbmc.Player(xbmc.PLAYER_CORE_DVDPLAYER).play("rtmp://aialanetfs.fplive.net/aialanet?slist=Jardineria/palmera-roebelen.flv", nuevoitem)

	# Cierra dialogo
	dialogWait.close()
	del dialogWait

	# Reproduce
	xbmcPlayer = xbmc.Player( xbmc.PLAYER_CORE_AUTO )
	xbmcPlayer.play(playlist)   

def directplay(params,url,category):

	# Playlist vacia
	playlist = xbmc.PlayList( xbmc.PLAYLIST_VIDEO )
	playlist.clear()

	# Crea la entrada y la añade al playlist
	listitem = xbmcgui.ListItem( "Emision en directo", iconImage="DefaultVideo.png" )
	listitem.setProperty("SWFPlayer", "http://www.hogarutil.com/staticFiles/static/player/BigBainetPlayer.swf")
	listitem.setInfo( "video", { "Title": "Emision en directo", "Studio" : CHANNELNAME , "Genre" : category } )
	playlist.add( url, listitem )

	# Reproduce
	xbmcPlayer = xbmc.Player( xbmc.PLAYER_CORE_AUTO )
	xbmcPlayer.play(playlist)   

def addfolder(nombre,url,accion):
	logger.info('[hogarutil.py] addfolder( "'+nombre+'" , "' + url + '" , "'+accion+'")"')
	listitem = xbmcgui.ListItem( nombre , iconImage="DefaultFolder.png")
	itemurl = '%s?channel=hogarutil&action=%s&category=%s&url=%s' % ( sys.argv[ 0 ] , accion , urllib.quote_plus(nombre) , urllib.quote_plus(url) )
	xbmcplugin.addDirectoryItem( handle = pluginhandle, url = itemurl , listitem=listitem, isFolder=True)

def addpagina(nombre,url,baseurl,accion):
	logger.info('[hogarutil.py] addfolder( "'+nombre+'" , "' + url + '" , "'+accion+'")"')
	listitem = xbmcgui.ListItem( nombre , iconImage="DefaultFolder.png")
	itemurl = '%s?channel=hogarutil&action=%s&category=%s&url=%s&baseurl=%s' % ( sys.argv[ 0 ] , accion , urllib.quote_plus(nombre) , urllib.quote_plus(url)  , urllib.quote_plus(baseurl) )
	xbmcplugin.addDirectoryItem( handle = pluginhandle, url = itemurl , listitem=listitem, isFolder=True)

def addvideo(nombre,url,category):
	logger.info('[hogarutil.py] addvideo( "'+nombre+'" , "' + url + '" , "'+category+'")"')
	listitem = xbmcgui.ListItem( nombre, iconImage="DefaultVideo.png" )
	listitem.setInfo( "video", { "Title" : nombre, "Plot" : nombre } )
	itemurl = '%s?channel=hogarutil&action=play&category=%s&url=%s' % ( sys.argv[ 0 ] , category , urllib.quote_plus(url) )
	xbmcplugin.addDirectoryItem( handle=pluginhandle, url=itemurl, listitem=listitem, isFolder=False)

def addvideodirecto(nombre,url,category):
	logger.info('[hogarutil.py] addvideodirecto( "'+nombre+'" , "' + url + '" , "'+category+'")"')
	listitem = xbmcgui.ListItem( nombre, iconImage="DefaultVideo.png" )
	listitem.setInfo( "video", { "Title" : nombre, "Plot" : "Emision en directo" } )
	itemurl = '%s?channel=hogarutil&action=directplay&category=%s&url=%s' % ( sys.argv[ 0 ] , category , urllib.quote_plus(url) )
	xbmcplugin.addDirectoryItem( handle=pluginhandle, url=itemurl, listitem=listitem, isFolder=False)

def addthumbnailfolder( scrapedtitle , scrapedurl , scrapedthumbnail , accion ):
	logger.info('[hogarutil.py] addthumbnailfolder( "'+scrapedtitle+'" , "' + scrapedurl + '" , "'+scrapedthumbnail+'" , "'+accion+'")"')
	listitem = xbmcgui.ListItem( scrapedtitle, iconImage="DefaultFolder.png", thumbnailImage=scrapedthumbnail )
	itemurl = '%s?channel=hogarutil&action=%s&category=%s&url=%s' % ( sys.argv[ 0 ] , accion , urllib.quote_plus( scrapedtitle ) , urllib.quote_plus( scrapedurl ) )
	xbmcplugin.addDirectoryItem( handle = pluginhandle, url = itemurl , listitem=listitem, isFolder=True)

#mainlist(None,"","mainlist")
#videolist(None,"http://www.hogarutil.com/Cocina/Recetas+en+vídeo","Cocina")
#play(None,"http://www.hogarutil.com/Cocina/Recetas+en+v%C3%ADdeo/Sepia+con+arroz+negro","")
