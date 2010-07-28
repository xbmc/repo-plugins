# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para gratisdocumentales
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

CHANNELNAME = "gratisdocumentales"
 
# Esto permite su ejecución en modo emulado
try:
	pluginhandle = int( sys.argv[ 1 ] )
except:
	pluginhandle = ""

# Traza el inicio del canal
logger.info("[gratisdocumentales.py] init")
 
DEBUG = True
 
def mainlist(params,url,category):
	logger.info("[gratisdocumentales.py] mainlist")

	# Añade al listado de XBMC
	xbmctools.addnewfolder( CHANNELNAME , "parseweb" , category, "Novedades" , "http://www.gratisdocumentales.com/" , "" , "")
	xbmctools.addnewfolder( CHANNELNAME , "buscacategorias" , category, "Categorias" , "http://www.gratisdocumentales.com/" , "" , "")
	xbmctools.addnewfolder( CHANNELNAME , "buscatags" , category, "Tags" , "http://www.gratisdocumentales.com/" , "" , "")
	xbmctools.addnewfolder( CHANNELNAME , "search" , category, "Búsqueda" , "" , "" , "")

	if config.getSetting("singlechannel")=="true":
		xbmctools.addSingleChannelOptions(params,url,category)

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
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
			searchUrl = "http://www.gratisdocumentales.com/?s="+tecleado+"&searchsubmit="
			parseweb(params,searchUrl,category)

def buscacategorias(params,url,category):
	logger.info("[gratisdocumentales.py] buscacategorias")
	data = scrapertools.cachePage(url)
	#href='http://www.gratisdocumentales.com/category/arte/' title="ARTE">ARTE</a></li><li><a
	patronvideos  = 'href=\'(.+?/category/.+?/)\' title="(.+?)">.*?</a></li><li><a'

	#logger.info("web"+data)
	matches = re.compile(patronvideos).findall(data)
	if DEBUG:
		scrapertools.printMatches(matches)
	if len(matches)>0:
		for i in range(len(matches)):
			xbmctools.addnewfolder( CHANNELNAME , "parseweb" , category, matches[i][1] , matches[i][0] , "" , "")
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def buscatags(params,url,category):
	logger.info("[gratisdocumentales.py] buscacategorias")
	data = scrapertools.cachePage(url)
	#href='http://www.gratisdocumentales.com/category/arte/' title="ARTE">ARTE</a></li><li><a
	patronvideos  = 'href="(http://www.gratisdocumentales.com/tag/.*?/)" id="tag-link-.+?>(.+?)</a> <a'

	#logger.info("web"+data)
	matches = re.compile(patronvideos).findall(data)
	if DEBUG:
		scrapertools.printMatches(matches)
	if len(matches)>0:
		for i in range(len(matches)):
			xbmctools.addnewfolder( CHANNELNAME , "parseweb" , category, matches[i][1] , matches[i][0] , "" , "")
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def parseweb(params,url,category):
	logger.info("[gratisdocumentales.py] parseweb")

	# ------------------------------------------------------
	# Descarga la página
	# ------------------------------------------------------
	data = scrapertools.cachePage(url)
	#logger.info(data)

	patronvideos  = '<h2  class="posttitle"><a\s+href="(.+?)" rel="bookmark" title="Permanent Link to .*?">(.+?)</a>'

	#logger.info("web"+data)
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	if DEBUG:
		scrapertools.printMatches(matches)
	#scrapertools.printMatches(matches)

	patronvideos1 = 'src="http://www.megavideo.com/v/(.{8}).+?".+?></embed>.*?<p>(.+?)</p><div'
	matches1 = re.compile(patronvideos1,re.DOTALL).findall(data)
	if DEBUG:
		scrapertools.printMatches(matches1)

	for i in range(len(matches)):
		xbmctools.addnewvideo( CHANNELNAME , "play" , category , "Megavideo" , matches[i][1] , matches1[i][0] , "thumbnail" , matches1[i][1])

	patronvideos  = 'href=\'(.+?/page/[0-9]+?/.*?)\' class=\'.*?page\'>(\d+?)</a>'

	#logger.info("web"+data)
	matches = re.compile(patronvideos).findall(data)
	if DEBUG:
		scrapertools.printMatches(matches)
	if len(matches)>0:
		for i in range(len(matches)):
			xbmctools.addnewfolder( CHANNELNAME , "parseweb" , category, matches[i][1] , matches[i][0] , "" , "")
	#scrapertools.printMatches(matches)	

	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def listmirrors(params,url,category):
	logger.info("[gratisdocumentales.py] detail")

	title = urllib.unquote_plus( params.get("title") )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	#plot = unicode( xbmc.getInfoLabel( "ListItem.Plot" ), "utf-8" )
	plot = urllib.unquote_plus( params.get("plot") )

	# ------------------------------------------------------------------------------------
	# Descarga la página
	# ------------------------------------------------------------------------------------
	data = scrapertools.cachePage(url)
	#logger.info(data)

	# ------------------------------------------------------------------------------------
	# Busca el argumento
	# ------------------------------------------------------------------------------------
	patronvideos  = '<div class="ficha_des">(.*?)</div>'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	if len(matches)>0:
		plot = scrapertools.htmlclean(matches[0])

	# ------------------------------------------------------------------------------------
	# Busca el thumbnail
	# ------------------------------------------------------------------------------------
	patronvideos  = '<div class="ficha_img pelicula_img">[^<]+'
	patronvideos += '<img src="([^"]+)"'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	if len(matches)>0:
		thumbnail = matches[0]

	# ------------------------------------------------------------------------------------
	# Busca los enlaces a los mirrors, o a los capítulos de las series...
	# ------------------------------------------------------------------------------------
	#	url = "http://www.gratisdocumentales.es/inc/mostrar_contenido.php?sec=pelis_ficha&zona=online&id=video-4637"
	patronvideos  = '<div class="ver_des_peli iframe2">[^<]+'
	patronvideos += '<ul class="tabs-nav" id="([^"]+)">'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)

	'''
	<div id="ficha_ver_peli">
	<div class="v_online">
	<h2>Ver online <span>El destino de Nunik</span></h2>
	<div class="opstions_pelicula_list">
	<div class="tit_opts" style="cursor:pointer;" onclick="location.href='http://www.gratisdocumentales.es/peliculas/drama/el-destino-de-nunik_espanol-dvd-rip-megavideo-6026.html'">
	<p>Mirror 1: Megavideo</p>
	<p><span>CALIDAD: DVD-RIP | IDIOMA: ESPA&Ntilde;OL</span></p>
	<p class="v_ico"><img src="http://caratulas.gratisdocumentales.es/img/cont/megavideo.png" alt="Megavideo" /></p>
	</div>
	<div class="tit_opts" style="cursor:pointer;" onclick="location.href='http://www.gratisdocumentales.es/peliculas/drama/el-destino-de-nunik_espanol-dvd-rip-megavideo-6027.html'">
	<p>Mirror 2: Megavideo</p>
	<p><span>CALIDAD: DVD-RIP | IDIOMA: ESPA&Ntilde;OL</span></p>
	<p class="v_ico"><img src="http://caratulas.gratisdocumentales.es/img/cont/megavideo.png" alt="Megavideo" /></p>
	</div>
	</div>
	</div>
	</div> 
	'''
	data = scrapertools.cachePage("http://www.gratisdocumentales.es/inc/mostrar_contenido.php?sec=pelis_ficha&zona=online&id="+matches[0])
	patronvideos  = '<div class="tit_opts" style="cursor:pointer;" onclick="location.href=\'([^\']+)\'">[^<]+'
	patronvideos += '<p>([^<]+)</p>[^<]+'
	patronvideos += '<p><span>([^<]+)</span>'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)

	for match in matches:
		logger.info("Encontrado iframe mirrors "+match[0])
		# Lee el iframe
		mirror = urlparse.urljoin(url,match[0].replace(" ","%20"))
		req = urllib2.Request(mirror)
		req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
		response = urllib2.urlopen(req)
		data=response.read()
		response.close()

		listavideos = servertools.findvideos(data)

		for video in listavideos:
			videotitle = video[0]
			scrapedurl = video[1]
			server = video[2]
			xbmctools.addnewvideo( CHANNELNAME , "play" , category , server , title.strip()+" "+match[1]+" "+match[2]+" "+videotitle , scrapedurl , thumbnail , plot )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def play(params,url,category):
	logger.info("[gratisdocumentales.py] play")

	title = urllib.unquote_plus( params.get("title") )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = unicode( xbmc.getInfoLabel( "ListItem.Plot" ), "utf-8" )
	server = params["server"]

	xbmctools.playvideo(CHANNELNAME,server,url,category,title,thumbnail,plot)
