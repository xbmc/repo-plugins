# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# tvalacarta - XBMC Plugin
# Canal para Terra TV
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

xbmc.output("[terratv.py] init")

DEBUG = False
CHANNELNAME = "Terra TV"
CHANNELCODE = "terratv"

def mainlist(params,url,category):
	xbmc.output("[terratv.py] mainlist")

	url = 'http://www.terra.tv/'

	# --------------------------------------------------------
	# Descarga la página
	# --------------------------------------------------------
	data = scrapertools.cachePage(url)
	#xbmc.output(data)

	# --------------------------------------------------------
	# Extrae las categorias (carpetas)
	# --------------------------------------------------------
	patron = '<li class="(?:subMenu|first|)"><a.*?href="([^"]+)".*?><span[^>]+>([^<]+)</span></a>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	if DEBUG:
		scrapertools.printMatches(matches)

	for match in matches:
		try:
			scrapedtitle = unicode( match[1], "utf-8" ).encode("iso-8859-1")
		except:
			scrapedtitle = match[1]
		scrapedurl = urlparse.urljoin(url,match[0])
		scrapedurl = scrapedurl.replace("&amp;","&")

		scrapedthumbnail = ""
		scrapedplot = ""

		# Depuracion
		if (DEBUG):
			xbmc.output("scrapedtitle="+scrapedtitle)
			xbmc.output("scrapedurl="+scrapedurl)
			xbmc.output("scrapedthumbnail="+scrapedthumbnail)

		# Añade al listado de XBMC
		#addvideo( scrapedtitle , scrapedurl , category )
		xbmctools.addnewfolder( CHANNELCODE , "channellist" , CHANNELNAME , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )

	# Disable sorting...
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def channellist(params,url,category):
	xbmc.output("[terratv.py] channellist")

	# --------------------------------------------------------
	# Descarga la página
	# --------------------------------------------------------
	data = scrapertools.cachePage(url)
	#xbmc.output(data)

	# --------------------------------------------------------
	# Extrae el código de canal
	# --------------------------------------------------------
	matches = re.compile("http\:\/\/.*?channel=([0-9]+)",re.DOTALL).findall(url)
	codigo=""
	if len(matches)>0:
		codigo=matches[0]
	xbmc.output("codigo="+codigo)
	
	# --------------------------------------------------------
	# Extrae los subcanales
	# --------------------------------------------------------
	patron = '<ul style="" class="subMenuChannels" id="sub_channel_'+codigo+'".*?</ul>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	data=""
	if len(matches)>0:
		data = matches[0]
		xbmc.output("data="+data)
	else:
		xbmc.output("No hay categorias en el nivel inferior, redirigiendo al listado de videos")
		videolist(params,url,category)
		return
	
	patron = '<li[^>]+><a href="([^"]+)"[^>]+><span[^>]+>([^<]+)</span></a></li>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	if DEBUG:
		scrapertools.printMatches(matches)

	for match in matches:
		scrapedtitle = match[1]
		scrapedurl = 'http://www.terra.tv'+match[0].replace("&amp;","&")
		scrapedthumbnail = ""
		scrapedplot = ""

		# Depuracion
		if (DEBUG):
			xbmc.output("scrapedtitle="+scrapedtitle)
			xbmc.output("scrapedurl="+scrapedurl)
			xbmc.output("scrapedthumbnail="+scrapedthumbnail)

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELCODE , "subchannellist" , CHANNELNAME , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )
	
	#-----------------------------------------------------------
	# Añade la lista completa de vídeos del canal
	#-----------------------------------------------------------
	xbmctools.addnewfolder( CHANNELCODE , "videolist" , CHANNELNAME , "(Todos los vídeos)" , url , "", "" )
	
	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )

	# Disable sorting...
	#xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def subchannellist(params,url,category):
	xbmc.output("[terratv.py] channellist")

	# --------------------------------------------------------
	# Descarga la página
	# --------------------------------------------------------
	data = scrapertools.cachePage(url)
	#xbmc.output(data)
	
	# --------------------------------------------------------
	# Extrae el código de canal
	# --------------------------------------------------------
	matches = re.compile("http\:\/\/.*?channel=([0-9]+)",re.DOTALL).findall(url)
	codigo=""
	if len(matches)>0:
		codigo=matches[0]
	xbmc.output("codigo="+codigo)
	
	'''
	<ul style="" class="subMenuChannels" id="sub_channel_1997" onmouseover="showMenu(1997,1);" onmouseout="showMenuDefault();">
	<li class="itemSelected "><a href="/templates/channelContents.aspx?channel=2124&amp;template=tabhome" onclick="forceStop()" title="National Geographic"><span style="COLOR:#192734;">National Geographic</span></a></li>

	<li id="sub_2128" class="first"><a href="/templates/channelContents.aspx?channel=2128&amp;template=tabhome" onclick="forceStop()" title="Aventura"><span style="COLOR:#FFFFFF;">Aventura</span></a></li>
	<li id="sub_2127" class=""><a href="/templates/channelContents.aspx?channel=2127&amp;template=tabhome" onclick="forceStop()" title="Historia y Cultura"><span style="COLOR:#FFFFFF;">Historia y Cultura</span></a></li>
	<li id="sub_2129" class=""><a href="/templates/channelContents.aspx?channel=2129&amp;template=tabhome" onclick="forceStop()" title="Mundo Moderno"><span style="COLOR:#FFFFFF;">Mundo Moderno</span></a></li>
	<li id="sub_2130" class=""><a href="/templates/channelContents.aspx?channel=2130&amp;template=tabhome" onclick="forceStop()" title="Mundo National Geographic"><span style="COLOR:#FFFFFF;">Mundo National Geographic</span></a></li>
	<li id="sub_2149" class=""><a href="/templates/channelContents.aspx?channel=2149&amp;template=tabhome" onclick="forceStop()" title="Paisajes"><span style="COLOR:#FFFFFF;">Paisajes</span></a></li>
	<li id="sub_2131" class=""><a href="/templates/channelContents.aspx?channel=2131&amp;template=tabhome" onclick="forceStop()" title="Vida Animal"><span style="COLOR:#FFFFFF;">Vida Animal</span></a></li>
	</ul>
	'''

	# --------------------------------------------------------
	# Extrae los subcanales
	# --------------------------------------------------------
	patron = '<li class="itemSelected.*?channel\='+codigo+'.*?</ul>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	data=""
	if len(matches)>0:
		data = matches[0]
		xbmc.output("data="+data)
	else:
		xbmc.output("No hay categorias en el nivel inferior, redirigiendo al listado de videos")
		videolist(params,url,category)
		return
	
	patron = '<li[^>]+><a href="([^"]+)"[^>]+><span[^>]+>([^<]+)</span></a></li>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	if DEBUG:
		scrapertools.printMatches(matches)

	# Ignora la primera entrada, es la de (todos)
	for i in range(1, len(matches)):
		match = matches[i]
	
		scrapedtitle = match[1]
		scrapedurl = 'http://www.terra.tv'+match[0].replace("&amp;","&")
		scrapedthumbnail = ""
		scrapedplot = ""

		# Depuracion
		if (DEBUG):
			xbmc.output("scrapedtitle="+scrapedtitle)
			xbmc.output("scrapedurl="+scrapedurl)
			xbmc.output("scrapedthumbnail="+scrapedthumbnail)

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELCODE , "videolist" , CHANNELNAME , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )
	
	#-----------------------------------------------------------
	# Añade la lista completa de vídeos del canal
	#-----------------------------------------------------------
	xbmctools.addnewfolder( CHANNELCODE , "videolist" , CHANNELNAME , "(Todos los vídeos)" , url , "", "" )
	
	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )

	# Disable sorting...
	#xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def videolist(params,url,category):
	xbmc.output("[terratv.py] videolist")

	# --------------------------------------------------------
	# Descarga la página
	# --------------------------------------------------------
	data = scrapertools.cachePage(url)
	#xbmc.output(data)

	# --------------------------------------------------------
	# Extrae enlace a página siguiente
	# --------------------------------------------------------
	patron = '<ul class="paginacao">.*?<li><a class="bt" title="pr.ximo" style="cursor:pointer" onclick="ajaxManagerCache.Add\(\'([^\']+)\''
	matches = re.compile(patron,re.DOTALL).findall(data)
	if DEBUG:
		scrapertools.printMatches(matches)

	for match in matches:
		scrapedtitle = "(Página siguiente)"
		scrapedurl = 'http://www.terra.tv/templates/'+match.replace("&amp;","&")
		scrapedthumbnail = ""
		scrapedplot = ""

		# Depuracion
		if (DEBUG):
			xbmc.output("scrapedtitle="+scrapedtitle)
			xbmc.output("scrapedurl="+scrapedurl)
			xbmc.output("scrapedthumbnail="+scrapedthumbnail)

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELCODE , "videolist" , CHANNELNAME , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# --------------------------------------------------------
	# Extrae los videos
	# --------------------------------------------------------
	patron = '<li>[^<]+<div class="img">[^<]+<a href="([^"]+)"[^>]+>[^<]+<img src="([^"]+)".*?<a[^>]+>([^<]+)<.*?<a[^>]+>([^<]+)<'
	matches = re.compile(patron,re.DOTALL).findall(data)
	if DEBUG:
		scrapertools.printMatches(matches)

	for match in matches:
		try:
			scrapedtitle = unicode( match[2] + " - " + match[3], "utf-8" ).encode("iso-8859-1")
		except:
			scrapedtitle = match[2] + " - " + match[3]
		scrapedurl = match[0]
		scrapedthumbnail = match[1]
		scrapedplot = ""

		# Depuracion
		if (DEBUG):
			xbmc.output("scrapedtitle="+scrapedtitle)
			xbmc.output("scrapedurl="+scrapedurl)
			xbmc.output("scrapedthumbnail="+scrapedthumbnail)

		# Añade al listado de XBMC
		xbmctools.addnewvideo( CHANNELCODE , "play" , CHANNELNAME , "" , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )

	# Disable sorting...
	#xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def play(params,url,category):
	xbmc.output("[terratv.py] play")

	title = unicode( xbmc.getInfoLabel( "ListItem.Title" ), "utf-8" )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = unicode( xbmc.getInfoLabel( "ListItem.Plot" ), "utf-8" )
	server = "Directo"
	xbmc.output("[terratv.py] thumbnail="+thumbnail)

	# Abre dialogo
	dialogWait = xbmcgui.DialogProgress()
	dialogWait.create( 'Descargando datos del vídeo...', title )

	# --------------------------------------------------------
	# Descarga pagina detalle
	# --------------------------------------------------------
	data = scrapertools.cachePage(url)
	patron = "'(http\:\/\/www\.terra\.tv\/templates\/getVideo\.aspx[^']+)'"
	matches = re.compile(patron,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)
	url = matches[0]
	xbmc.output("url="+url)

	req = urllib2.Request(url)
	req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
	response = urllib2.urlopen(req)
	data=response.read()
	response.close()
	xbmc.output("data="+data)

	patron = '<ref href="([^"]+)"'
	matches = re.compile(patron,re.DOTALL).findall(data)

	if len(matches)==0:
		patron = '<video src="([^"]+)"'
		matches = re.compile(patron,re.DOTALL).findall(data)

	url = matches[0]
	xbmc.output("url="+url)
	
	# --------------------------------------------------------
	# Amplia el argumento
	# --------------------------------------------------------
	patron = '<div id="encuesta">\s*<div class="cab">.*?</div>(.*?)</div>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)
	if len(matches)>0:
		plot = "%s" % matches[0]
		plot = plot.replace("<p>","")
		plot = plot.replace("</p>"," ")
		plot = plot.replace("<strong>","")
		plot = plot.replace("</strong>","")
		plot = plot.replace("<br />"," ")
		plot = plot.strip()
	
	# Cierra dialogo
	dialogWait.close()
	del dialogWait

	xbmctools.playvideo(CHANNELNAME,server,url,category,title,thumbnail,plot)
