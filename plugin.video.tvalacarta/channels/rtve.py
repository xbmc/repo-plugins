# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# tvalacarta - XBMC Plugin
# Canal para RTVE
# http://blog.tvalacarta.info/plugin-xbmc/tvalacarta/
#------------------------------------------------------------

import urlparse,urllib2,urllib,re
import os
import sys
import xbmc
import xbmcgui
import xbmcplugin
import scrapertools
import binascii
import xbmctools

try:
	pluginhandle = int( sys.argv[ 1 ] )
except:
	pluginhandle = ""

xbmc.output("[rtve.py] init")

DEBUG = True
CHANNELNAME = "TVE"
CHANNELCODE = "rtve"

def mainlist(params,url,category):
	xbmc.output("[rtve.py] mainlist")

	# Añade al listado de XBMC
	xbmctools.addnewfolder( CHANNELCODE , "videolist" , CHANNELNAME , "Recomendados"   , "http://www.rtve.es/alacarta/todos/recomendados/index.html"  , "" , "" )
	xbmctools.addnewfolder( CHANNELCODE , "videolist" , CHANNELNAME , "Últimos 7 días" , "http://www.rtve.es/alacarta/todos/ultimos/index.html"       , "" , "" )
	xbmctools.addnewfolder( CHANNELCODE , "videolist" , CHANNELNAME , "Temas"          , "http://www.rtve.es/alacarta/todos/temas/index.html"         , "" , "" )
	xbmctools.addnewfolder( CHANNELCODE , "videolist" , CHANNELNAME , "Todos A-Z"      , "http://www.rtve.es/alacarta/todos/abecedario/index.html"    , "" , "" )
	xbmctools.addnewfolder( CHANNELCODE , "videolist" , CHANNELNAME , "Archivo TVE"    , "http://www.rtve.es/alacarta/archivo/index.html"             , "" , "" )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def videolist(params,url,category):
	xbmc.output("[rtve.py] videolist")

	title = urllib.unquote_plus( params.get("title") )

	# --------------------------------------------------------
	# Descarga la página
	# --------------------------------------------------------
	xbmc.output("[rtve.py] videolist descarga página principal "+url)
	data = scrapertools.cachePage(url)
	#xbmc.output(data)

	# --------------------------------------------------------
	# Extrae las categorias (carpetas)
	# --------------------------------------------------------
	patron  = '<a href="(/alacarta/todos/[^"]+)".*?>([^<]+)</a>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	if DEBUG:
		scrapertools.printMatches(matches)

	for match in matches:
		# Datos
		scrapedtitle = scrapertools.entityunescape(match[1].strip())
		scrapedurl = urlparse.urljoin("http://www.rtve.es", match[0])
		scrapedthumbnail = ""
		scrapedplot = ""
		if (DEBUG): xbmc.output("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		#addvideo( scrapedtitle , scrapedurl , category )
		if scrapedtitle=="Recomendados" or scrapedtitle=="Temas" or scrapedtitle=="Todos A-Z" or scrapedtitle=="Archivo TVE" or scrapedtitle=="Ultimos 7 dias" or scrapedtitle=="Adelante":
			pass
		else:
			xbmctools.addnewfolder( CHANNELCODE , "videolist" , CHANNELNAME , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# --------------------------------------------------------
	# Extrae los videos de la página actual
	# --------------------------------------------------------
	#patron  = '<li id="video-(\d+)">\W*<div>\W*<a rel="facebox" href="([^"]+)"><img src="([^"]+)" alt="([^"]+)"><img alt="Reproducir" src="/css/i/mediateca/play.png" class="play_mini"></a>\W+<h3>\W+<a[^<]+</a>\W+</h3>\W+<p>([^<]+)</p>[^<]+<span>([^<]+)<'
	patron  = '<li id="video-(\d+)" class="videoThumbnail">[^<]+'
	patron += '<div>[^<]+'
	patron += "<a.*?href='([^']+)'[^>]+>[^<]+"
	patron += '<img src="([^"]+)" alt="([^"]+)"[^>]+>[^<]+'
	patron += '<img alt="Reproducir"[^<]+'
	patron += '</a>[^<]+'
	patron += '<h3>[^<]+'
	patron += '<a[^>]+>([^<]+)</a>[^<]+'
	patron += '</h3>[^<]+'
	patron += '<p>([^<]+)</p>[^<]+'
	patron += '<span>([^<]+)<'
	matches = re.compile(patron,re.DOTALL).findall(data)
	anyadevideos(matches)

	# --------------------------------------------------------
	# Extrae los videos del resto de páginas
	# --------------------------------------------------------
	xbmc.output("Paginación...")
	'''
	<a href="/alacarta/todos/recomendados/2.html"  class="">
	  Adelante
	</a>
	'''
	patronpaginas = '<a href="([^"]+)"  class="">\s+Adelante\s+</a>'
	paginas = re.compile(patronpaginas,re.DOTALL).findall(data)
	if DEBUG: scrapertools.printMatches(paginas)
	print paginas

	# Hay al menos otra página
	while len(paginas)>0:
		urlpagina = urlparse.urljoin(url,paginas[0])
		xbmc.output("urlpagina="+urlpagina)
		datapagina = scrapertools.cachePage(urlpagina)
		matches = re.compile(patron,re.DOTALL).findall(datapagina)
		anyadevideos(matches)
		paginas = re.compile(patronpaginas,re.DOTALL).findall(datapagina)

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	#xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_TITLE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def anyadevideos(matches):
	if DEBUG: scrapertools.printMatches(matches)

	'''
	patron  = '<li id="video-(\d+)" class="videoThumbnail">[^<]+'   [0] 244902
	patron += '<div>[^<]+'
	patron += "<a.*?href='([^']+)'[^>]+>[^<]+"						[1] .shtml
	patron += '<img src="([^"]+)" alt="([^"]+)"[^>]+>[^<]+'			[2] .jpg [3] Telediario Internacional Edición 18 horas (10/04/10)
	patron += '<img alt="Reproducir"[^<]+'
	patron += '</a>[^<]+'
	patron += '<h3>[^<]+'
	patron += '<a[^>]+>([^<]+)</a>[^<]+'							[4] TD Internacional 18h (10/04/10)
	patron += '</h3>[^<]+'		
	patron += '<p>([^<]+)</p>[^<]+'									[5] Polonia, de luto. El presidente del Parlamento asume las funciones de Kaczynski. 
	patron += '<span>([^<]+)<'										[6] Emitido: 10/04/2010 / 18:00h
	'''

	for match in matches:
		patron = "Emitido:\s+([^\s]+)\s+\/\s+(\d+)\:(\d+)h"
		fechahora = re.compile(patron,re.DOTALL).findall(match[6])
		if DEBUG: scrapertools.printMatches(fechahora)

		if len(fechahora)>0:
			scrapedtitle = scrapertools.entityunescape(match[4] + " ("+fechahora[0][0]+") (" + fechahora[0][1]+"'"+fechahora[0][2]+'")')
		else:
			scrapedtitle = scrapertools.entityunescape(match[4])
		scrapedurl = urlparse.urljoin("http://www.rtve.es",match[1])

		scrapedthumbnail = "http://www.rtve.es%s" % match[2]
		scrapedplot = scrapertools.entityunescape(match[3].strip()+"\n"+match[5].strip())

		# Depuracion
		if (DEBUG):
			xbmc.output("scrapedtitle="+scrapedtitle)
			xbmc.output("scrapedurl="+scrapedurl)
			xbmc.output("scrapedthumbnail="+scrapedthumbnail)

		# Añade al listado de XBMC
		xbmctools.addnewvideo( CHANNELCODE , "play" , CHANNELNAME , "" , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )
'''
def play(params,url,category):
	xbmc.output("[rtve.py] play")

	title = unicode( xbmc.getInfoLabel( "ListItem.Title" ), "utf-8" )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = unicode( xbmc.getInfoLabel( "ListItem.Plot" ), "utf-8" )
	server = "Directo"

	# Abre dialogo
	dialogWait = xbmcgui.DialogProgress()
	dialogWait.create( 'Descargando datos del vídeo...', title )

	# --------------------------------------------------------
	# Descarga pagina detalle
	# --------------------------------------------------------
	data = scrapertools.cachePage(url)
	patron = '<location>([^<]+)</location>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)
	try:
		#url = matches[0].replace('rtmp://stream.rtve.es/stream/','http://www.rtve.es/')
		url = matches[0]
	except:
		url = ""
	xbmc.output("[rtve.py] url="+url)

	# Cierra dialogo
	dialogWait.close()
	del dialogWait

	xbmctools.playvideo(CHANNELNAME,server,url,category,title,thumbnail,plot)
'''
def play(params,url,category):
	xbmc.output("[rtve.py] play")

	title = unicode( xbmc.getInfoLabel( "ListItem.Title" ), "utf-8" )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = unicode( xbmc.getInfoLabel( "ListItem.Plot" ), "utf-8" )
	server = "Directo"

	# Abre dialogo
	dialogWait = xbmcgui.DialogProgress()
	dialogWait.create( 'Descargando datos del vídeo...', title )

	# Extrae el código
	#http://www.rtve.es/mediateca/videos/20100410/telediario-edicion/741525.shtml
	patron = 'http://.*?/([0-9]+).shtml'
	data = url
	matches = re.compile(patron,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)
	codigo = matches[0]
	xbmc.output("idvideo="+codigo)

	try:
		# Compone la URL
		#http://www.rtve.es/swf/data/es/videos/alacarta/5/2/5/1/741525.xml
		url = 'http://www.rtve.es/swf/data/es/videos/alacarta/'+codigo[-1:]+'/'+codigo[-2:-1]+'/'+codigo[-3:-2]+'/'+codigo[-4:-3]+'/'+codigo+'.xml'
		xbmc.output("[rtvemediateca.py] url=#"+url+"#")

		# Descarga el XML y busca el vídeo
		#<file>rtmp://stream.rtve.es/stream/resources/alacarta/flv/6/9/1270911975696.flv</file>
		data = scrapertools.cachePage(url)
		patron = '<file>([^<]+)</file>'
		matches = re.compile(patron,re.DOTALL).findall(data)
		scrapertools.printMatches(matches)
		#url = matches[0].replace('rtmp://stream.rtve.es/stream/','http://www.rtve.es/')
		url = matches[0]
	except:
		url = ""
	
	# Hace un segundo intento
	if url=="":
		try:
			# Compone la URL
			#http://www.rtve.es/swf/data/es/videos/video/0/5/8/0/500850.xml
			url = 'http://www.rtve.es/swf/data/es/videos/video/'+codigo[-1:]+'/'+codigo[-2:-1]+'/'+codigo[-3:-2]+'/'+codigo[-4:-3]+'/'+codigo+'.xml'
			xbmc.output("[rtvemediateca.py] url=#"+url+"#")

			# Descarga el XML y busca el vídeo
			#<file>rtmp://stream.rtve.es/stream/resources/alacarta/flv/6/9/1270911975696.flv</file>
			data = scrapertools.cachePage(url)
			patron = '<file>([^<]+)</file>'
			matches = re.compile(patron,re.DOTALL).findall(data)
			scrapertools.printMatches(matches)
			#url = matches[0].replace('rtmp://stream.rtve.es/stream/','http://www.rtve.es/')
			url = matches[0]
		except:
			url = ""
		
	xbmc.output("[rtve.py] url="+url)

	# Cierra dialogo
	dialogWait.close()
	del dialogWait

	if url.startswith("rtmp"):
		# Playlist vacia
		playlist = xbmc.PlayList( xbmc.PLAYLIST_VIDEO )
		playlist.clear()

		'''
		flvstreamer  -r "rtmp://stream.rtve.es/stream/resources/alacarta/flv/5/3/1270074791935.flv" -o out.flv
		FLVStreamer v1.7
		(c) 2009 Andrej Stepanchuk, license: GPL
		DEBUG: Parsing...
		DEBUG: Parsed protocol: 0
		DEBUG: Parsed host    : stream.rtve.es
		DEBUG: Parsed app     : stream/resources
		DEBUG: Parsed playpath: alacarta/flv/5/3/1270074791935
		DEBUG: Setting buffer time to: 36000000ms
		Connecting ...
		DEBUG: Protocol : RTMP
		DEBUG: Hostname : stream.rtve.es
		DEBUG: Port     : 1935
		DEBUG: Playpath : alacarta/flv/5/3/1270074791935
		DEBUG: tcUrl    : rtmp://stream.rtve.es:1935/stream/resources
		DEBUG: app      : stream/resources
		DEBUG: flashVer : LNX 9,0,124,0
		DEBUG: live     : no
		DEBUG: timeout  : 300 sec
		DEBUG: Connect, ... connected, handshaking
		DEBUG: HandShake: Type Answer   : 03
		DEBUG: HandShake: Server Uptime : 1463582178
		DEBUG: HandShake: FMS Version   : 3.5.2.1
		DEBUG: Connect, handshaked
		Connected...
		'''
		#url=rtmp://stream.rtve.es/stream/resources/alacarta/flv/5/3/1270074791935.flv
		hostname = "stream.rtve.es"
		xbmc.output("[rtve.py] hostname="+hostname)
		portnumber = "1935"
		xbmc.output("[rtve.py] portnumber="+portnumber)
		tcurl = "rtmp://stream.rtve.es/stream/resources"
		xbmc.output("[rtve.py] tcurl="+tcurl)
		#playpath = "alacarta/flv/5/3/1270074791935"
		playpath = url[39:-4]
		xbmc.output("[rtve.py] playpath="+playpath)
		app = "stream/resources"
		xbmc.output("[rtve.py] app="+app)
		
		listitem = xbmcgui.ListItem( title, iconImage="DefaultVideo.png", thumbnailImage=thumbnail )
		#listitem.setProperty("SWFPlayer", "http://www.plus.es/plustv/carcasa.swf")
		listitem.setProperty("Hostname",hostname)
		listitem.setProperty("Port",portnumber)
		listitem.setProperty("tcUrl",tcurl)
		listitem.setProperty("Playpath",playpath)
		listitem.setProperty("app",app)
		listitem.setProperty("flashVer","LNX 9,0,124,0")
		listitem.setProperty("pageUrl","LNX 9,0,124,0")

		listitem.setInfo( "video", { "Title": title, "Plot" : plot , "Studio" : CHANNELNAME , "Genre" : category } )
		playlist.add( url, listitem )

		# Reproduce
		xbmcPlayer = xbmc.Player( xbmc.PLAYER_CORE_AUTO )
		xbmcPlayer.play(playlist)   
	elif url.startswith("http"):
		xbmctools.playvideo(CHANNELNAME,server,url,category,title,thumbnail,plot)
	else:
		xbmctools.alertnodisponible()